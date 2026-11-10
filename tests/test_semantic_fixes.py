"""Opt-in semantic fixes for B2 (billed_until) and B3 (Reversal rename).

The fixes are NEVER applied to app/ by the default codemod; these tests
run them on TEMP COPIES of the whole app/ tree, so they are safe on any
branch and prove the fix actually works end-to-end:
- B2: the fixed billing.py returns billed_until on the new API version.
- B3: the fixed refunds.py works on stripe-python 16 (and, correctly,
  breaks on 15 -- the rename is a one-way upgrade).
- B2 without confirm=True must refuse (semantic decision).
- The real app/billing.py and app/refunds.py on main stay unfixed.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _copy_app_tree() -> Path:
    """Copy app/ to a temp dir importable as a package."""
    tmp = Path(tempfile.mkdtemp())
    shutil.copytree(ROOT / "app", tmp / "app")
    return tmp


def _original_source(filename: str) -> str:
    result = subprocess.run(
        ["git", "show", "main:app/%s" % filename],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    if result.returncode == 0 and result.stdout:
        return result.stdout
    return (ROOT / "app" / filename).read_text(encoding="utf-8")


def _load_from_copy(tmp: Path, module: str):
    sys.path.insert(0, str(tmp))
    try:
        import importlib
        for name in list(sys.modules):
            if name == "app" or name.startswith("app."):
                del sys.modules[name]
        return importlib.import_module("app.%s" % module)
    finally:
        sys.path.remove(str(tmp))


# --- B2 ----------------------------------------------------------------------
def test_billed_until_fix_requires_confirm():
    from fixer.semantic_fixes import fix_billed_until

    with pytest.raises(ValueError, match="confirm=True"):
        fix_billed_until(_original_source("billing.py"))


def test_billed_until_fix_refuses_ambiguous_input():
    from fixer.semantic_fixes import fix_billed_until

    with pytest.raises(ValueError, match="exactly 1"):
        fix_billed_until("x = 1\n", confirm=True)
    with pytest.raises(ValueError, match="exactly 1"):
        fix_billed_until(
            'a = client.subscription_items_retrieve("1")\n'
            'b = client.subscription_items_retrieve("2")\n',
            confirm=True,
        )


def test_billed_until_fixed_copy_returns_value_on_new_version():
    from fixer.semantic_fixes import fix_billed_until

    tmp = _copy_app_tree()
    source = (tmp / "app" / "billing.py").read_text(encoding="utf-8")
    fixed = fix_billed_until(source, confirm=True)
    assert 'expand=["billed_until"]' in fixed
    (tmp / "app" / "billing.py").write_text(fixed, encoding="utf-8")

    billing = _load_from_copy(tmp, "billing")
    from app.stripe_client import FakeStripeClient

    client = FakeStripeClient("2026-09-30.endive")
    assert billing.get_subscription_billed_until(client, "si_test_1") == 1790000000


def test_billed_until_fix_is_not_applied_by_default_codemod():
    """The real app/billing.py on main must still contain the break."""
    source = (ROOT / "app" / "billing.py").read_text(encoding="utf-8")
    assert "billed_until" in source
    assert 'expand=["billed_until"]' not in source


# --- B3 ----------------------------------------------------------------------
def test_reversal_fix_on_copy_works_on_sdk16():
    from fixer.semantic_fixes import fix_reversal_rename

    tmp = _copy_app_tree()
    source = (tmp / "app" / "refunds.py").read_text(encoding="utf-8")
    fixed = fix_reversal_rename(source)
    assert ".TransferReversal" in fixed
    assert ".Reversal.retrieve" not in fixed
    (tmp / "app" / "refunds.py").write_text(fixed, encoding="utf-8")

    refunds = _load_from_copy(tmp, "refunds")
    from app.stripe_sdk import get_sdk

    result = refunds.get_transfer_reversal(get_sdk("16"), "trr_test_1")
    assert result["object"] == "transfer_reversal"


def test_reversal_fix_breaks_on_sdk15_as_expected():
    """One-way upgrade: after the rename, stripe-python 15 has no
    TransferReversal. The test documents this, it does not hide it."""
    from fixer.semantic_fixes import fix_reversal_rename

    tmp = _copy_app_tree()
    fixed = fix_reversal_rename((tmp / "app" / "refunds.py").read_text(encoding="utf-8"))
    (tmp / "app" / "refunds.py").write_text(fixed, encoding="utf-8")
    refunds = _load_from_copy(tmp, "refunds")
    from app.stripe_sdk import get_sdk

    with pytest.raises(AttributeError):
        refunds.get_transfer_reversal(get_sdk("15"), "trr_test_1")


def test_reversal_fix_refuses_when_nothing_to_fix():
    from fixer.semantic_fixes import fix_reversal_rename

    with pytest.raises(ValueError, match="no .Reversal"):
        fix_reversal_rename("x = 1\n")


def test_reversal_fix_does_not_touch_docstrings():
    """Only attribute access is renamed; the docstring still says Reversal."""
    from fixer.semantic_fixes import fix_reversal_rename

    fixed = fix_reversal_rename(_original_source("refunds.py"))
    assert "stripe.Reversal" in fixed  # docstring wording preserved
    assert "sdk.Reversal" not in fixed
