"""Customer app code -- BREAK 1 (mechanical, fixable by codemod).

Written against Stripe API version 2026-03-25.dahlia, where passing
``payment_method_types`` to a Checkout Session was legal.

In 2026-09-30.endive Stripe removed ``payment_method_types`` from
Checkout Sessions, PaymentIntents and SetupIntents: requests including
it now return HTTP 400 ``payment_method_types_no_longer_supported``.
Source: https://docs.stripe.com/changelog (2026-09-30.endive).
"""

from __future__ import annotations

from app.stripe_client import FakeStripeClient


def create_checkout_session(client: FakeStripeClient, *, amount_cents: int = 2000):
    """Create a Checkout Session. BREAKS on API version 2026-09-30.endive."""
    return client.checkout_sessions_create(
        mode="payment",
        line_items=[
            {"price_data": {"currency": "usd", "unit_amount": amount_cents,
                            "product_data": {"name": "Test product"}},
             "quantity": 1}
        ],
        payment_method_types=["card"],
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
    )


def create_payment_intent(client: FakeStripeClient, *, amount_cents: int = 2000):
    """Create a PaymentIntent. Also breaks on endive (same removal)."""
    return client.payment_intents_create(
        amount=amount_cents,
        currency="usd",
        payment_method_types=["card"],
    )
