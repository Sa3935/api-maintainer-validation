"""Customer app code -- CONTROLS (unchanged between the versions).

These endpoints / SDK calls did NOT change between
2026-03-25.dahlia and 2026-09-30.endive (or stripe-python 15 -> 16).
The detector must NOT flag them: they are the false-positive controls.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time

from app.stripe_client import FakeStripeClient


def create_customer(client: FakeStripeClient, *, email: str, name: str = ""):
    """POST /v1/customers -- request params identical in both specs."""
    return client.customers_create(email=email, name=name)


def _sign(payload: bytes, secret: str, timestamp: int | None = None) -> str:
    timestamp = timestamp or int(time.time())
    signed = b"%d.%s" % (timestamp, payload)
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return "t=%d,v1=%s" % (timestamp, sig)


def make_test_signature(payload: bytes, secret: str) -> str:
    """Build a valid Stripe-Signature header for tests (test secret only)."""
    return _sign(payload, secret)


def handle_webhook(payload: bytes, sig_header: str, secret: str):
    """Verify a webhook signature, the way stripe.Webhook.construct_event
    does. Unchanged across stripe-python 15 -> 16 (verified live:
    stripe.Webhook.construct_event exists in 16.0.0).

    Returns the parsed event dict on success, raises ValueError otherwise.
    """
    try:
        parts = dict(p.split("=", 1) for p in sig_header.split(","))
        timestamp = int(parts["t"])
        expected = _sign(payload, secret, timestamp)
        expected_sig = expected.split("v1=")[1]
    except Exception as exc:
        raise ValueError("invalid signature header") from exc
    if abs(int(time.time()) - timestamp) > 300:
        raise ValueError("webhook timestamp too old")
    if not hmac.compare_digest(parts.get("v1", ""), expected_sig):
        raise ValueError("signature verification failed")
    return json.loads(payload.decode("utf-8"))
