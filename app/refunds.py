"""Customer app code -- BREAK 3 (SDK rename, NOT a REST spec change).

Written against stripe-python 15.x, where the class was ``stripe.Reversal``.

In stripe-python 16.0.0 (2026-09-30, pins API version 2026-09-30.endive)
``stripe.Reversal`` was renamed to ``stripe.TransferReversal``; code
referencing the old name raises AttributeError on upgrade.
Source: https://github.com/stripe/stripe-python/blob/master/CHANGELOG.md
(16.0.0, PR #1915). Verified live against real stripe==16.0.0:
``hasattr(stripe, 'TransferReversal')`` is True, ``stripe.Reversal``
raises AttributeError.

This break is NOT visible in the Stripe OpenAPI spec at all -- it is an
SDK-surface change. The detector catches it via the SDK-changelog
registry (detector/data/known_breaks.json), not via spec diff.
"""

from __future__ import annotations


def get_transfer_reversal(sdk, reversal_id: str):
    """Retrieve a transfer reversal. BREAKS on stripe-python 16.x."""
    return sdk.Reversal.retrieve(reversal_id)
