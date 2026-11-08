"""Customer app code -- BREAK 2 (semantic, DO NOT auto-fix).

Written against Stripe API version 2026-03-25.dahlia, where
``billed_until`` was returned on SubscriptionItem by default.

In 2026-05-27.dahlia Stripe changed ``billed_until`` to be includable
rather than returned by default: code that reads the field directly
gets an empty value (``None`` here) after the upgrade, silently, with
no error. The correct fix is to request it via ``expand`` -- a semantic
decision about what the caller actually needs -- so no agent/codemod
is allowed to touch this file. The codemod is scoped to
``payment_method_types`` only (see fixer/codemod.py).
Source: https://docs.stripe.com/changelog/dahlia/2026-05-27/subscription-item-billed-until-includable
"""

from __future__ import annotations

from app.stripe_client import FakeStripeClient


def get_subscription_billed_until(client: FakeStripeClient, item_id: str):
    """Return the billed-until timestamp for a subscription item.

    Returns ``None`` (silently) on API versions >= 2026-05-27.dahlia,
    because the field is no longer returned by default.
    """
    item = client.subscription_items_retrieve(item_id)
    return item.get("billed_until")
