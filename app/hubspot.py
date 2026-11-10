"""Customer app code -- HUBSPOT BREAKS H1 (sunset, 404) and H2 (upcoming).

H1: Contact Lists API v1, sunset April 30, 2026 -- v1 endpoints return
    HTTP 404 after that date. Migrate to Lists v3.
H2 (upcoming, not yet broken on 2026-11-09): Pipelines API v1, sunset
    December 4, 2026 -- v1 endpoints stop responding after that date.
    Migrate to the 2026-03 or newer Pipelines API.

Sources: HubSpot developer changelog (see app/hubspot_client.py).
"""

from __future__ import annotations

from app.hubspot_client import FakeHubSpotClient


def get_list_v1(client: FakeHubSpotClient, list_id: str):
    """GET Contact Lists v1 -- 404 after April 30, 2026."""
    return client.lists_v1_get(list_id)


def get_pipeline_v1(client: FakeHubSpotClient, pipeline_id: str):
    """GET Pipelines v1 -- stops responding after December 4, 2026."""
    return client.pipelines_v1_get(pipeline_id)


def get_list_v3(client: FakeHubSpotClient, list_id: str):
    """GET Lists v3 -- the migration target (control: works)."""
    return client.lists_v3_get(list_id)
