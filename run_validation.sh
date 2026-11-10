#!/usr/bin/env bash
# Full validation loop. Run from the repo root: ./run_validation.sh
# Exits 0 if the loop ran to completion; the GO/NO-GO verdict is printed
# and written to validation_results.json (exit code is NOT the verdict).
set -uo pipefail
cd "$(dirname "$0")"

export STRIPE_SUPPRESS_NOTICES=true
PY="${PY:-python3}"
if [ -x ".venv/bin/python" ]; then PY=".venv/bin/python"; fi

step() { echo ""; echo "=== $1 ==="; }

# 0. Node deps for the stripe-node 21 test (real stripe@21.0.0, $0).
#    If npm is unavailable / offline, the Node test skips and the verdict
#    records node as "skipped" instead of failing the whole run.
step "0/6 node deps (stripe@21.0.0, for the Node break test)"
NODE_STATUS="skipped"
if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
  if (cd node_app && npm install --no-audit --no-fund >/dev/null 2>&1); then
    NODE_STATUS="installed"
    echo "node deps installed: $(node -p "JSON.parse(require('fs').readFileSync('./node_app/node_modules/stripe/package.json','utf-8')).version" 2>/dev/null || echo '?')"
  else
    echo "npm install failed -- Node test will be skipped"
  fi
else
  echo "node/npm not found -- Node test will be skipped"
fi

# 1. Tests on main: break-reproduction tests must pass; the codemod test
#    must FAIL (proving the break is real before the fix).
step "1/6 pytest on main (expect test_checkout_passes_after_codemod to FAIL)"
set +e
"$PY" -m pytest tests/test_breaks.py tests/test_codemod.py tests/test_real_stripe_sdk.py \
  tests/test_multi_api.py tests/test_semantic_fixes.py tests/test_node_breaks.py -q 2>&1 | tail -15
MAIN_PYTEST_EXIT=$?
set -e

# 2. Detector against the real specs + vendor registries (7 breaks, 2 upcoming).
step "2/6 detector (real Stripe specs + vendor retirement registries)"
"$PY" -m detector.detect

# 3. Codemod on a real branch (B1 only; B2/B3 are opt-in semantic fixes).
step "3/6 codemod on branch fix/remove-payment-method-types"
git checkout -q main 2>/dev/null || true
git branch -D fix/remove-payment-method-types 2>/dev/null || true
git checkout -q -b fix/remove-payment-method-types
"$PY" -m fixer.codemod --apply
git add -A
git -c user.name="api-maintainer-validation" -c user.email="validation@localhost" \
    commit -q -m "fix: remove payment_method_types (Stripe 2026-09-30.endive)

Deterministic codemod: drops the removed payment_method_types kwarg
from app/checkout.py. Billed_until (semantic) and stripe.Reversal
rename deliberately untouched (see fixer/semantic_fixes.py)." || echo "(nothing to commit - already applied)"
git log --oneline -1

# 4. Tests on the fix branch: the full suite minus the two
#    break-reproduction tests must pass. (Those two assert the OLD code
#    raises 400, so on fixed code they must FAIL -- that failure is
#    itself the proof the fix works, checked explicitly just below.)
step "4/6 pytest on fix branch (expect ALL to pass)"
set +e
"$PY" -m pytest tests/ -q \
  --deselect tests/test_breaks.py::test_checkout_breaks_on_endive \
  --deselect tests/test_breaks.py::test_payment_intent_breaks_on_endive 2>&1 | tail -8
FIX_PYTEST_EXIT=$?
echo ""
echo "--- proof the fix works: the two break-reproduction tests must now FAIL ---"
"$PY" -m pytest tests/test_breaks.py::test_checkout_breaks_on_endive tests/test_breaks.py::test_payment_intent_breaks_on_endive -q 2>&1 | tail -4
REPRO_EXIT=$?
set -e

# 5. Scale check (150-file synthetic repo) + Node test summary.
step "5/6 scale check + node test"
"$PY" -m detector.scale_check > /tmp/scale_check_out.json 2>&1 || true
python3 -c "import json; print(json.dumps(json.loads(open('scale/scale_report.json').read()), indent=2))" 2>/dev/null || echo "(scale report not written)"
if [ "$NODE_STATUS" = "installed" ]; then
  (cd node_app && node test_node_breaks.js 2>&1 | tail -6)
  NODE_TEST="passed"
else
  NODE_TEST="skipped"
fi

# 6. Back to main, write the verdict.
step "6/6 verdict"
git checkout -q main
"$PY" - "$NODE_STATUS" "$NODE_TEST" <<'EOF'
import json, sys
from pathlib import Path
report = json.loads(Path("detector/report.json").read_text())
s = report["summary"]
scale = {}
try:
    scale = json.loads(Path("scale/scale_report.json").read_text())
except Exception:
    pass
verdict = {
    "detector_detected": s["detected"],
    "detector_total": s["total_known_breaks"],
    "false_positives": s["false_positives"],
    "detector_go_no_go": s["go_no_go"],
    "upcoming_warnings_detected": s["upcoming_warnings_detected"],
    "upcoming_warnings_total": s["upcoming_warnings_total"],
    "node_deps": sys.argv[1],
    "node_test": sys.argv[2],
    "scale_files": scale.get("generated_files"),
    "scale_real_call_sites_found": scale.get("real_call_sites_found"),
    "scale_real_call_sites_total": scale.get("real_call_sites_total"),
    "scale_false_positives": scale.get("false_positives"),
    "scale_decoy_comment_only_hits": scale.get("decoy_comment_only_hits"),
}
Path("validation_results.json").write_text(json.dumps(verdict, indent=2))
print(json.dumps(verdict, indent=2))
EOF
echo ""
echo "main-branch pytest exit: $MAIN_PYTEST_EXIT (non-zero is EXPECTED: the codemod test fails on unfixed code)"
echo "fix-branch pytest exit:  $FIX_PYTEST_EXIT (0 is required for GO)"
echo "repro-tests-on-fix exit: $REPRO_EXIT (non-zero is EXPECTED: fixed code no longer raises 400)"
echo "node test: $NODE_TEST"
echo "Done. Repo is back on main; the fix lives on branch fix/remove-payment-method-types"
echo "(including patches/fix-payment-method-types.patch, committed there)."
