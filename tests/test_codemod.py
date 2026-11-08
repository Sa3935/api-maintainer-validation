"""Codemod tests: the fix is mechanical, scoped, and safe.

Runs the codemod against a TEMP COPY of app/checkout.py (never the
real file), so these tests are safe to run on any branch.
"""

import ast
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run_codemod_on_copy() -> str:
    tmp = Path(tempfile.mkdtemp())
    shutil.copy(ROOT / "app" / "checkout.py", tmp / "checkout.py")
    # Point the codemod at the copy by importing its functions directly.
    sys.path.insert(0, str(ROOT))
    from fixer.codemod import apply_removals, find_removals

    source = (tmp / "checkout.py").read_text(encoding="utf-8")
    removals = find_removals(source)
    assert len(removals) == 2, "expected 2 payment_method_types kwargs, got %d" % len(removals)
    new_source = apply_removals(source, removals)
    (tmp / "checkout.py").write_text(new_source, encoding="utf-8")
    return new_source


def test_codemod_removes_only_payment_method_types():
    new_source = _run_codemod_on_copy()
    assert "payment_method_types" not in new_source
    ast.parse(new_source)  # still valid Python
    # The rest of the call survives: mode, urls, line items intact.
    assert 'mode="payment"' in new_source
    assert "success_url" in new_source
    assert "create_payment_intent" in new_source


def test_codemod_never_touches_billing_or_refunds():
    """Guard rail: the codemod's forbidden list must contain both files,
    and neither file may mention the codemod's target handling."""
    from fixer import codemod

    forbidden = {str(p) for p in codemod.FORBIDDEN}
    assert str(ROOT / "app" / "billing.py") in forbidden
    assert str(ROOT / "app" / "refunds.py") in forbidden
    # And the real files still contain the breaks (codemod didn't fix them).
    assert "billed_until" in (ROOT / "app" / "billing.py").read_text()
    assert "Reversal" in (ROOT / "app" / "refunds.py").read_text()


def test_codemod_check_mode_is_clean():
    result = subprocess.run(
        [sys.executable, "-m", "fixer.codemod", "--check"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "2 payment_method_types kwarg(s)" in result.stdout
