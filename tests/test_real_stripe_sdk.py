"""Live check against the REAL stripe-python package (if installed).

No network, no keys: this only inspects the installed library's
surface, proving break 3 (stripe.Reversal -> stripe.TransferReversal)
is real and not just a changelog quote. Skipped if `stripe` is not
installed (run `pip install -r requirements.txt`).
"""

import pytest

stripe = pytest.importorskip("stripe")


def test_real_stripe_16_has_transfer_reversal_not_reversal():
    assert hasattr(stripe, "TransferReversal")
    assert not hasattr(stripe, "Reversal")
    with pytest.raises(AttributeError):
        stripe.Reversal


def test_real_stripe_16_pins_endive():
    assert stripe.api_version == "2026-09-30.endive"


def test_real_stripe_webhook_construct_event_exists():
    assert hasattr(stripe.Webhook, "construct_event")
