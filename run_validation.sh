#!/usr/bin/env bash
# Full validation loop. Run from the repo root: ./run_validation.sh
# Exits 0 if the loop ran to completion; the GO/NO-GO verdict is printed
# and written to validation_results.json (exit code is NOT the verdict).
set -u
cd "$(dirname "$0")"

export STRIPE_SUPPRESS_NOTICES=true
PY="${PY:-python3}"
if [ -x ".venv/bin/python" ]; then PY=".venv/bin/python"; fi

step() { echo ""; echo "=== $1 ==="; }

# 1. Tests on main: break-reproduction tests must pass; the codemod test
#    must FAIL (proving the break is real before the fix).
step "1/5 pytest on main (expect test_checkout_passes_after_codemod to FAIL)"
set +e
"$PY" -m pytest tests/test_breaks.py tests/test_codemod.py tests/test_real_stripe_sdk.py -q 2>&1 | tail -15
MAIN_PYTEST_EXIT=$?
set -e

# 2. Detector against the real specs.
step "2/5 detector (real Stripe specs)"
"$PY" -m detector.detect

# 3. Codemod on a real branch.
step "3/5 codemod on branch fix/remove-payment-method-types"
git checkout -q main 2>/dev/null || true
git branch -D fix/remove-payment-method-types 2>/dev/null || true
git checkout -q -b fix/remove-payment-method-types
"$PY" -m fixer.codemod --apply
git add -A
git -c user.name="api-maintainer-validation" -c user.email="validation@localhost" \
    commit -q -m "fix: remove payment_method_types (Stripe 2026-09-30.endive)

Deterministic codemod: drops the removed payment_method_types kwarg
from app/checkout.py. Billed_until (semantic) and stripe.Reversal
rename deliberately untouched." || echo "(nothing to commit - already applied)"
git log --oneline -1

# 4. Tests on the fix branch: everything must pass now.
step "4/5 pytest on fix branch (expect ALL to pass)"
set +e
"$PY" -m pytest tests/ -q 2>&1 | tail -8
FIX_PYTEST_EXIT=$?
set -e

# 5. Back to main, write the verdict.
step "5/5 verdict"
git checkout -q main
"$PY" - <<'EOF'
import json
from pathlib import Path
report = json.loads(Path("detector/report.json").read_text())
s = report["summary"]
verdict = {
    "detector_detected": s["detected"],
    "detector_total": s["total_known_breaks"],
    "false_positives": s["false_positives"],
    "detector_go_no_go": s["go_no_go"],
}
Path("validation_results.json").write_text(json.dumps(verdict, indent=2))
print(json.dumps(verdict, indent=2))
EOF
echo ""
echo "main-branch pytest exit: $MAIN_PYTEST_EXIT (non-zero is EXPECTED: the codemod test fails on unfixed code)"
echo "fix-branch pytest exit:  $FIX_PYTEST_EXIT (0 is required for GO)"
echo "Done. Repo is back on main; the fix lives on branch fix/remove-payment-method-types"
echo "(including patches/fix-payment-method-types.patch, committed there)."
