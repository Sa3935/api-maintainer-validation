"""Mocked Twilio API client.

Simulates Twilio's product sunset -- NO network, NO real account, NO keys.
The client takes an explicit ``today`` date so tests are deterministic.

Source (Twilio's own changelog, verified 2026-11-09):
- Programmable Chat API: Twilio "intend[s] to sunset the Programmable
  Chat API on July 25, 2022 to focus on the next generation of chat,
  the Twilio Conversations API."
  https://www.twilio.com/en-us/changelog/programmable-chat-end-of-life-notice
  Twilio's docs now mark the Chat v1 REST API deprecated and unsupported.
  NOTE: Twilio did not name a specific HTTP status for calls after the
  sunset in that notice; the mock models it as 410:GONE (the standard
  sunset code, as used by Salesforce), and this modelling choice is
  flagged in docs/MULTI_API_SOURCES.md. Do not quote a Twilio 410 as a
  Twilio fact. The verified facts are the sunset date and the
  Conversations migration target.
"""

from __future__ import annotations

from datetime import date

PROGRAMMABLE_CHAT_SUNSET = date(2022, 7, 25)


class TwilioAPIError(Exception):
    """A fake Twilio API error with an HTTP status + code."""

    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


class FakeTwilioClient:
    """A date-aware fake of the Twilio API (offline)."""

    def __init__(self, today: str = "2026-11-09"):
        year, month, day = (int(p) for p in today.split("-"))
        self.today = date(year, month, day)

    def chat_channels_create(self, service_sid: str, friendly_name: str):
        """POST Programmable Chat v1 channels -- sunset July 25, 2022."""
        if self.today >= PROGRAMMABLE_CHAT_SUNSET:
            raise TwilioAPIError(
                410, "GONE",
                "Programmable Chat API was sunset July 25, 2022; migrate to "
                "the Twilio Conversations API. (410 is this mock's model of "
                "the sunset; Twilio's notice names the date, not a status.)",
            )
        return {"sid": "CH_test", "friendly_name": friendly_name}

    def conversations_create(self, friendly_name: str):
        """POST Conversations v1 -- the migration target; works."""
        return {"sid": "CH_test", "friendly_name": friendly_name}
