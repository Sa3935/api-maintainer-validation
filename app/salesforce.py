"""Customer app code -- SALESFORCE BREAK S1 (forced retirement, 410:GONE).

Written against Salesforce Platform API v28.0. Versions 21.0-30.0 were
retired in Summer '25: every REST call on those versions now returns
HTTP 410:GONE. Unlike Stripe (which pins your version indefinitely),
Salesforce retires versions on a schedule, so this break bites whether
or not the team deliberately upgrades -- that is the urgency difference.

Source: https://developer.salesforce.com/docs/platform/api-rest/guide/api-rest-eol.html
"""

from __future__ import annotations

from app.salesforce_client import FakeSalesforceClient

# Pinned in the customer code -- this is the break. v28.0 is retired.
RETIRED_VERSION = "28.0"
# v35.0 is supported now but deprecated from Summer '27, retired Summer '28.
UPCOMING_VERSION = "35.0"
# Control: a supported version.
SUPPORTED_VERSION = "60.0"


def get_client(version: str = RETIRED_VERSION) -> FakeSalesforceClient:
    return FakeSalesforceClient(version)


def query_accounts(client: FakeSalesforceClient):
    """SELECT Id, Name FROM Account -- 410:GONE on v28.0 (retired)."""
    return client.query("SELECT Id, Name FROM Account")
