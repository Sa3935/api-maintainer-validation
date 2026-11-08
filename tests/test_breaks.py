"""Break-reproduction tests (mocked Stripe, no network, no real keys).

These tests encode the 3 real Stripe breaks. How to read them:

- Tests named ``test_*_breaks_*`` / ``test_*_silent_*`` PASS on the
  original (main) code: they prove the break reproduces.
- ``test_checkout_passes_after_codemod`` FAILS on main and PASSES on the
  ``fix/remove-payment-method-types`` branch: it proves the codemod
  actually fixes break 1.
- Controls PASS on both versions: they prove unchanged behaviour stays
  unchanged (the false-positive guard).
"""

from pathlib import Path

import pytest

from app import billing, checkout, refunds, webhooks
from app.stripe_client import FakeStripeClient, StripeAPIError
from app.stripe_sdk import get_sdk
from tests.conftest import NEW_API_VERSION, OLD_API_VERSION

ROOT = Path(__file__).resolve().parent.parent


# --- Break 1: payment_method_types removed (endive) -----------------------
def test_checkout_breaks_on_endive():
    """Old code + new API version -> HTTP 400. Reproduces break 1."""
    client = FakeStripeClient(NEW_API_VERSION)
    with pytest.raises(StripeAPIError) as exc:
        checkout.create_checkout_session(client)
    assert exc.value.status == 400
    assert exc.value.code == "payment_method_types_no_longer_supported"


def test_checkout_works_on_old_version():
    """Same old code + old API version -> works (the break is the upgrade)."""
    client = FakeStripeClient(OLD_API_VERSION)
    session = checkout.create_checkout_session(client)
    assert session["id"].startswith("cs_test_")


def test_payment_intent_breaks_on_endive():
    client = FakeStripeClient(NEW_API_VERSION)
    with pytest.raises(StripeAPIError) as exc:
        checkout.create_payment_intent(client)
    assert exc.value.status == 400


def test_checkout_passes_after_codemod():
    """PASSES only after the codemod removed payment_method_types.

    FAILS on main (old code still sends the removed param). This is the
    test the fix branch must turn green.
    """
    source = (ROOT / "app" / "checkout.py").read_text(encoding="utf-8")
    from fixer.codemod import find_removals

    assert find_removals(source) == [], (
        "app/checkout.py still sends payment_method_types as a kwarg -- "
        "run the codemod (python -m fixer.codemod --apply)"
    )
    client = FakeStripeClient(NEW_API_VERSION)
    session = checkout.create_checkout_session(client)
    assert session["id"].startswith("cs_test_")


# --- Break 2: billed_until silent None (dahlia, semantic) -----------------
def test_billed_until_silent_none_on_new_version():
    """Old code reads billed_until directly -> None, silently, no error."""
    client = FakeStripeClient(NEW_API_VERSION)
    assert billing.get_subscription_billed_until(client, "si_test_1") is None


def test_billed_until_returned_on_old_version():
    client = FakeStripeClient(OLD_API_VERSION)
    assert billing.get_subscription_billed_until(client, "si_test_1") == 1790000000


def test_billed_until_returned_when_expanded():
    """The correct (semantic) fix is expand -- documented, not automated."""
    client = FakeStripeClient(NEW_API_VERSION)
    item = client.subscription_items_retrieve("si_test_1", expand=["billed_until"])
    assert item["billed_until"] == 1790000000


# --- Break 3: stripe.Reversal renamed (stripe-python 16) ------------------
def test_reversal_breaks_on_sdk16():
    """Old code + stripe-python 16 surface -> AttributeError."""
    sdk = get_sdk("16")
    with pytest.raises(AttributeError):
        refunds.get_transfer_reversal(sdk, "trr_test_1")


def test_reversal_works_on_sdk15():
    sdk = get_sdk("15")
    result = refunds.get_transfer_reversal(sdk, "trr_test_1")
    assert result["object"] == "reversal"


# --- Controls: unchanged behaviour ----------------------------------------
def test_customers_create_unchanged_across_versions():
    for version in (OLD_API_VERSION, NEW_API_VERSION):
        client = FakeStripeClient(version)
        customer = webhooks.create_customer(client, email="a@example.com", name="A")
        assert customer["id"].startswith("cus_test_")
        assert customer["email"] == "a@example.com"


def test_webhook_signature_verification_unchanged():
    import json

    payload = json.dumps({"id": "evt_test_1", "type": "checkout.session.completed"}).encode()
    secret = "whsec_test_only_not_a_real_secret"
    sig = webhooks.make_test_signature(payload, secret)
    event = webhooks.handle_webhook(payload, sig, secret)
    assert event["id"] == "evt_test_1"
    with pytest.raises(ValueError):
        webhooks.handle_webhook(payload, "t=1,v1=deadbeef", secret)
