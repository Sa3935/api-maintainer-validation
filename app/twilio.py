"""Customer app code -- TWILIO BREAK T1 (product sunset).

Programmable Chat v1, sunset July 25, 2022 -- migrate to the Twilio
Conversations API. Source: Twilio changelog (see app/twilio_client.py).
"""

from __future__ import annotations

from app.twilio_client import FakeTwilioClient


def create_chat_channel(client: FakeTwilioClient, service_sid: str, name: str):
    """POST Programmable Chat v1 channel -- sunset July 25, 2022."""
    return client.chat_channels_create(service_sid, name)


def create_conversation(client: FakeTwilioClient, name: str):
    """POST Conversations v1 -- the migration target (control: works)."""
    return client.conversations_create(name)
