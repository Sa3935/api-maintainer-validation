"""Mocked HubSpot API client.

Simulates HubSpot's dated sunsets -- NO network, NO real portal, NO keys.
The client takes an explicit ``today`` date so tests are deterministic
(the real API's behaviour depends on the calendar date).

Sources (HubSpot's own developer changelog, verified 2026-11-09):
- Contact Lists API (v1): sunset moved to April 30, 2026; after that
  date v1 Lists endpoints return HTTP 404. Migrate to the Lists v3 API.
  https://developers.hubspot.com/changelog/extension-contact-lists-api-v1-sunset-moved-to-april-30-2026
  and https://developers.hubspot.com/docs/api-reference/latest/deprecated-apis
- Pipelines API V1: sunset December 4, 2026. "After this date, the API
  will no longer be supported" and v1 endpoints "stop responding";
  migrate to the 2026-03 or newer version.
  https://developers.hubspot.com/changelog/pipelines-api-v1-sunset
  NOTE: HubSpot states the 404 explicitly for Lists v1, but for
  Pipelines v1 it only says endpoints "stop responding" -- the mock
  models that as a 404 too, and this modelling choice is flagged in
  docs/MULTI_API_SOURCES.md. Do not quote a Pipelines 404 as a HubSpot fact.
- v1-v3 APIs (and legacy apps) become unsupported in September 2027
  (Fall Spotlight announcement, Sep 15, 2026) -- no shutdown date
  announced for them, so that is a warning, not a break.
"""

from __future__ import annotations

from datetime import date

LISTS_V1_SUNSET = date(2026, 4, 30)
PIPELINES_V1_SUNSET = date(2026, 12, 4)


class HubSpotAPIError(Exception):
    """A fake HubSpot API error with an HTTP status + code."""

    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


class FakeHubSpotClient:
    """A date-aware fake of the HubSpot API (offline)."""

    def __init__(self, today: str = "2026-11-09"):
        year, month, day = (int(p) for p in today.split("-"))
        self.today = date(year, month, day)

    def lists_v1_get(self, list_id: str):
        """GET /contacts/v1/lists/:id -- 404 after April 30, 2026."""
        if self.today >= LISTS_V1_SUNSET:
            raise HubSpotAPIError(
                404, "NOT_FOUND",
                "Contact Lists API (v1) was sunset April 30, 2026; "
                "v1 Lists endpoints return HTTP 404. Migrate to the Lists v3 API.",
            )
        return {"listId": list_id, "name": "Test list"}

    def pipelines_v1_get(self, pipeline_id: str):
        """GET /crm-pipelines/v1/pipelines/:id -- stops responding Dec 4, 2026."""
        if self.today >= PIPELINES_V1_SUNSET:
            raise HubSpotAPIError(
                404, "NOT_FOUND",
                "Pipelines API V1 was sunset December 4, 2026; v1 endpoints "
                "stop responding. Migrate to the 2026-03 or newer version. "
                "(404 is this mock's model of 'stop responding'; HubSpot did "
                "not name a status code for Pipelines v1.)",
            )
        return {"pipelineId": pipeline_id, "label": "Test pipeline"}

    def lists_v3_get(self, list_id: str):
        """GET /crm/v3/lists/:id -- the migration target; works."""
        return {"listId": list_id, "name": "Test list"}
