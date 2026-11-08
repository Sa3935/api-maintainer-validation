"""Mocked Stripe API client.

Simulates the Stripe REST API's behaviour for two pinned API versions,
with NO network calls and NO real keys. This is the "Stripe" the
customer app talks to in the sandbox.

Behaviour modelled from Stripe's own changelog:
- 2026-09-30.endive: ``payment_method_types`` removed from Checkout
  Sessions, PaymentIntents and SetupIntents; requests including it get
  HTTP 400 ``payment_method_types_no_longer_supported``.
  Source: https://docs.stripe.com/changelog (2026-09-30.endive) and
  https://docs.stripe.com/payments/payment-methods/integration-options
- 2026-05-27.dahlia: ``billed_until`` on SubscriptionItem changed from
  "returned by default" to "includable" -- it is only present when
  requested via ``expand``. Code reading it directly gets ``None``.
  Source: https://docs.stripe.com/changelog/dahlia/2026-05-27/subscription-item-billed-until-includable
- Versions before 2026-05-27.dahlia returned ``billed_until`` by default.
"""

from __future__ import annotations


class StripeAPIError(Exception):
    """A fake of stripe.error.StripeError with an HTTP status + code."""

    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def _version_tuple(version: str) -> tuple:
    """'2026-09-30.endive' -> (2026, 9, 30). Codename ignored for ordering."""
    date_part = version.split(".")[0]
    year, month, day = (int(p) for p in date_part.split("-"))
    return (year, month, day)


# The date on which billed_until stopped being returned by default.
BILLED_UNTIL_INCLUDABLE_FROM = (2026, 5, 27)
# The date on which payment_method_types was removed.
PAYMENT_METHOD_TYPES_REMOVED_FROM = (2026, 9, 30)


class FakeStripeClient:
    """A version-aware fake of the Stripe REST API (test mode, offline)."""

    def __init__(self, api_version: str):
        self.api_version = api_version
        self._v = _version_tuple(api_version)

    # -- Checkout -------------------------------------------------------
    def checkout_sessions_create(self, **params):
        if (
            self._v >= PAYMENT_METHOD_TYPES_REMOVED_FROM
            and "payment_method_types" in params
        ):
            raise StripeAPIError(
                400,
                "payment_method_types_no_longer_supported",
                "payment_method_types is no longer supported on Checkout "
                "Sessions in API version %s. Use allowed_payment_method_types "
                "or dynamic payment methods instead." % self.api_version,
            )
        return {
            "id": "cs_test_fake123",
            "object": "checkout.session",
            "url": "https://checkout.stripe.com/pay/cs_test_fake123",
            "payment_method_types": params.get("payment_method_types", ["card"]),
            "mode": params.get("mode", "payment"),
        }

    # -- PaymentIntents ---------------------------------------------------
    def payment_intents_create(self, **params):
        if (
            self._v >= PAYMENT_METHOD_TYPES_REMOVED_FROM
            and "payment_method_types" in params
        ):
            raise StripeAPIError(
                400,
                "payment_method_types_no_longer_supported",
                "payment_method_types is no longer supported on PaymentIntents "
                "in API version %s." % self.api_version,
            )
        return {"id": "pi_test_fake123", "object": "payment_intent", "status": "requires_payment_method"}

    # -- Subscription items ----------------------------------------------
    def subscription_items_retrieve(self, item_id: str, expand=None):
        expand = expand or []
        item = {
            "id": item_id,
            "object": "subscription_item",
            "price": {"id": "price_test_fake"},
            "quantity": 1,
        }
        # Before 2026-05-27.dahlia billed_until came back by default.
        # From then on it is only present when explicitly expanded.
        if self._v < BILLED_UNTIL_INCLUDABLE_FROM or "billed_until" in expand:
            item["billed_until"] = 1790000000
        return item

    # -- Customers (CONTROL: unchanged between the two versions) ----------
    def customers_create(self, **params):
        return {
            "id": "cus_test_fake123",
            "object": "customer",
            "email": params.get("email"),
            "name": params.get("name"),
        }
