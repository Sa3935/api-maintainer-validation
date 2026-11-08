"""Fake stripe-python SDK surface, version-aware.

Models the SDK-level (not REST-level) breaking change in
stripe-python 16.0.0 (2026-09-30, pins API version 2026-09-30.endive):

    stripe.Reversal  ->  renamed to  stripe.TransferReversal

Verified live against the real stripe==16.0.0 package (no network, no
keys): ``hasattr(stripe, 'TransferReversal')`` is True,
``stripe.Reversal`` raises AttributeError.
Source: https://github.com/stripe/stripe-python/blob/master/CHANGELOG.md
(16.0.0, PR #1915).
"""

from __future__ import annotations


class _TransferReversal:
    @staticmethod
    def retrieve(reversal_id: str):
        return {"id": reversal_id, "object": "transfer_reversal", "amount": 1000}


class _Reversal:
    @staticmethod
    def retrieve(reversal_id: str):
        return {"id": reversal_id, "object": "reversal", "amount": 1000}


class FakeSDKv15:
    """stripe-python 15.x surface: Reversal exists, TransferReversal does not."""

    Reversal = _Reversal


class FakeSDKv16:
    """stripe-python 16.x surface: Reversal renamed to TransferReversal."""

    TransferReversal = _TransferReversal


def get_sdk(sdk_version: str):
    """Return the fake SDK namespace for a major version ('15' or '16')."""
    if str(sdk_version).startswith("15"):
        return FakeSDKv15()
    if str(sdk_version).startswith("16"):
        return FakeSDKv16()
    raise ValueError("unsupported fake SDK version: %r" % (sdk_version,))
