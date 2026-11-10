"""Break-reproduction tests for the non-Stripe vendors (all mocked, offline).

S1 Salesforce: v21.0-30.0 retired Summer '25 -> REST 410:GONE.
   v31.0-40.0 supported now, deprecated Summer '27, retired Summer '28.
   v60.0 supported (control).
H1 HubSpot Lists v1: sunset Apr 30, 2026 -> 404 after that date.
H2 HubSpot Pipelines v1: sunset Dec 4, 2026 -> stops responding after.
T1 Twilio Programmable Chat: sunset Jul 25, 2022 -> 410 (modelled) after.
   Conversations v1 works (control / migration target).
"""

import pytest

from app import hubspot, salesforce, twilio
from app.hubspot_client import FakeHubSpotClient, HubSpotAPIError
from app.salesforce_client import FakeSalesforceClient, SalesforceAPIError, version_status
from app.twilio_client import FakeTwilioClient, TwilioAPIError


# --- S1: Salesforce forced retirement ---------------------------------------
def test_salesforce_retired_version_returns_410():
    client = salesforce.get_client("28.0")
    assert version_status("28.0") == "retired"
    with pytest.raises(SalesforceAPIError) as exc:
        salesforce.query_accounts(client)
    assert exc.value.status == 410
    assert exc.value.code == "GONE"


def test_salesforce_v21_and_v30_also_retired():
    for v in ("21.0", "25.0", "30.0", "7.0", "20.0"):
        assert version_status(v) == "retired"
        with pytest.raises(SalesforceAPIError):
            FakeSalesforceClient(v).query("SELECT Id FROM Account")


def test_salesforce_upcoming_v31_40_warns_but_still_works():
    """v35.0 is the upcoming-warning case: answers today, retires Summer '28."""
    client = salesforce.get_client("35.0")
    assert version_status("35.0") == "deprecated_upcoming"
    result = salesforce.query_accounts(client)
    assert result["totalSize"] == 1
    assert result["warning"] is not None and "Summer '28" in result["warning"]


def test_salesforce_supported_version_works():
    client = salesforce.get_client("60.0")
    assert version_status("60.0") == "supported"
    assert salesforce.query_accounts(client)["totalSize"] == 1


# --- H1/H2: HubSpot sunsets --------------------------------------------------
def test_hubspot_lists_v1_404_after_sunset():
    client = FakeHubSpotClient(today="2026-11-09")
    with pytest.raises(HubSpotAPIError) as exc:
        hubspot.get_list_v1(client, "123")
    assert exc.value.status == 404


def test_hubspot_lists_v1_worked_before_sunset():
    client = FakeHubSpotClient(today="2026-04-29")
    assert hubspot.get_list_v1(client, "123")["listId"] == "123"


def test_hubspot_lists_v3_is_the_migration_target():
    client = FakeHubSpotClient(today="2026-11-09")
    assert hubspot.get_list_v3(client, "123")["listId"] == "123"


def test_hubspot_pipelines_v1_upcoming_sunset():
    """Dec 4, 2026 is still in the future on 2026-11-09: works now, 404 after."""
    assert hubspot.get_pipeline_v1(FakeHubSpotClient(today="2026-11-09"), "p1")["pipelineId"] == "p1"
    with pytest.raises(HubSpotAPIError) as exc:
        hubspot.get_pipeline_v1(FakeHubSpotClient(today="2026-12-05"), "p1")
    assert exc.value.status == 404


# --- T1: Twilio sunset --------------------------------------------------------
def test_twilio_programmable_chat_sunset():
    client = FakeTwilioClient(today="2026-11-09")
    with pytest.raises(TwilioAPIError) as exc:
        twilio.create_chat_channel(client, "IS_1", "general")
    assert exc.value.status == 410


def test_twilio_chat_worked_before_sunset():
    client = FakeTwilioClient(today="2022-07-24")
    assert twilio.create_chat_channel(client, "IS_1", "general")["sid"] == "CH_test"


def test_twilio_conversations_is_the_migration_target():
    client = FakeTwilioClient(today="2026-11-09")
    assert twilio.create_conversation(client, "general")["sid"] == "CH_test"
