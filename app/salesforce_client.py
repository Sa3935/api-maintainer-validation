"""Mocked Salesforce Platform REST API client.

Simulates the version-retirement behaviour documented in Salesforce's
own API End-of-Life Policy -- NO network, NO real org, NO credentials.

Source: https://developer.salesforce.com/docs/platform/api-rest/guide/api-rest-eol.html
(verified 2026-11-09):
- Salesforce supports each API version for a minimum of 3 years from
  first release, and notifies customers at least 1 year before support ends.
- Versions 7.0-20.0: retired Summer '22, unavailable.
- Versions 21.0-30.0: deprecated Summer '22, RETIRED Summer '25,
  unavailable. REST requests to a retired version return 410:GONE;
  SOAP returns 500 UNSUPPORTED_API_VERSION; Bulk API v1 returns
  400 InvalidVersion (per third-party write-ups of the same retirement;
  the 410 for REST is Salesforce's own doc, the SOAP/Bulk codes are
  recorded in docs/MULTI_API_SOURCES.md).
- Versions 31.0-40.0: supported now, deprecated and unsupported from
  Summer '27, RETIRED from Summer '28 (same policy page).
- Versions 41.0+: supported.

The mock models REST only. A retired version raises 410 on every call;
a 31.0-40.0 version answers but is flagged deprecated_upcoming, so the
detector can warn BEFORE the Summer '28 retirement, not after it.
"""

from __future__ import annotations


class SalesforceAPIError(Exception):
    """A fake of a Salesforce REST error with an HTTP status + code."""

    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


# (low, high) inclusive ranges, as floats, from the policy page.
RETIRED_RANGES = [(7.0, 20.0), (21.0, 30.0)]
DEPRECATED_UPCOMING_RANGES = [(31.0, 40.0)]


def version_status(api_version: str) -> str:
    """'retired' | 'deprecated_upcoming' | 'supported' for a version like '28.0'."""
    v = float(api_version)
    for low, high in RETIRED_RANGES:
        if low <= v <= high:
            return "retired"
    for low, high in DEPRECATED_UPCOMING_RANGES:
        if low <= v <= high:
            return "deprecated_upcoming"
    return "supported"


class FakeSalesforceClient:
    """A version-aware fake of the Salesforce REST API (offline)."""

    def __init__(self, api_version: str):
        self.api_version = api_version
        self.status = version_status(api_version)

    def query(self, soql: str):
        """GET /services/data/vNN.0/query -- 410:GONE on a retired version."""
        if self.status == "retired":
            raise SalesforceAPIError(
                410,
                "GONE",
                "API version %s is retired (Summer '25 for 21.0-30.0). "
                "REST API returns 410:GONE for retired versions. "
                "Migrate to API version 41.0 or later." % self.api_version,
            )
        return {
            "totalSize": 1,
            "records": [{"Id": "001xx000003Test", "Name": "Acme"}],
            "warning": (
                "API version %s is deprecated and unsupported from Summer '27, "
                "retired Summer '28." % self.api_version
                if self.status == "deprecated_upcoming"
                else None
            ),
        }
