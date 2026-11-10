# Multi-API sources (verified 2026-11-09)

Every break added in the `expand/multi-api` expansion is sourced from the
vendor's own docs/changelog. Status codes are split into two groups --
**vendor-stated** (the vendor names the code) and **modelled** (the vendor
names the date/event, this sandbox models the failure code). Do not quote
a modelled code as a vendor fact.

## Salesforce -- forced retirement (S1 broken, S2 upcoming)

Source: Salesforce API End-of-Life Policy,
https://developer.salesforce.com/docs/platform/api-rest/guide/api-rest-eol.html

- Policy: each API version supported for a minimum of 3 years from first
  release; customers notified at least 1 year before support ends.
- Versions 7.0-20.0: retired Summer '22, unavailable.
- Versions 21.0-30.0: deprecated Summer '22, **retired Summer '25**,
  unavailable. **REST returns 410:GONE** -- vendor-stated.
- Versions 31.0-40.0: supported now, deprecated and unsupported from
  Summer '27, **retired from Summer '28** -- vendor-stated (upcoming, S2).
- SOAP retired version: 500 UNSUPPORTED_API_VERSION; Bulk API v1:
  400 InvalidVersion. These two codes are NOT on the REST policy page
  above; they are reported in write-ups of the same retirement (e.g.
  the Summer '25 retirement summaries). The mock models REST only, so
  they do not affect any test in this repo.
- Why it matters: unlike Stripe, Salesforce retires versions on a
  schedule, so the break bites whether or not a team deliberately
  upgrades. That is the urgency Stripe cannot prove.

## HubSpot -- dated sunsets (H1 broken, H2 upcoming)

- H1 Contact Lists API (v1): sunset **April 30, 2026** (extended from
  Sep 30, 2025, announced Sep 12, 2025). After that date v1 Lists
  endpoints **return HTTP 404** -- vendor-stated. Migrate to Lists v3.
  https://developers.hubspot.com/changelog/extension-contact-lists-api-v1-sunset-moved-to-april-30-2026
  and https://developers.hubspot.com/docs/api-reference/latest/deprecated-apis
- H2 Pipelines API V1: sunset **December 4, 2026** (announced Aug 14,
  2026). "After this date, the API will no longer be supported" and v1
  endpoints "stop responding"; migrate to the 2026-03 or newer version.
  https://developers.hubspot.com/changelog/pipelines-api-v1-sunset
  **Modelled:** HubSpot did not name a status code for Pipelines v1,
  so the mock models "stop responding" as 404 (same as Lists v1).
- v1-v3 APIs and legacy public/private apps become **unsupported in
  September 2027** (Fall Spotlight, Sep 15, 2026). No shutdown date
  announced for them -- a warning, not a break.
  https://developers.hubspot.com/changelog/legacy-apis-and-legacy-apps-whats-going-unsupported-and-when

## Twilio -- product sunset (T1)

- Programmable Chat API: Twilio "intend[s] to sunset the Programmable
  Chat API on **July 25, 2022** to focus on the next generation of
  chat, the Twilio Conversations API."
  https://www.twilio.com/en-us/changelog/programmable-chat-end-of-life-notice
  Twilio's docs now mark the Chat v1 REST API deprecated and unsupported.
- **Modelled:** Twilio's notice names the date, not a status code, so
  the mock models post-sunset calls as 410:GONE (the standard sunset
  code, as used by Salesforce). Do not quote a Twilio 410 as a Twilio fact.

## stripe-node 21 -- wrong webhook parser throws (N1)

- stripe-node 21.0.0 (pins Stripe API 2026-03-25.dahlia), breaking
  change #2618 / PR #2616: "Throw an error when using the wrong
  webhook parsing method".
  https://github.com/stripe/stripe-node/releases/tag/v21.0.0
  https://github.com/stripe/stripe-node/pull/2616
- Behaviour, verified live in this repo against the real packages:
  - stripe@21.0.0: `constructEvent(thin v2.core.event)` throws
    "Use stripe.parseEventNotification instead."; 
    `parseEventNotification(snapshot v1 event)` throws
    "Use stripe.webhooks.constructEvent instead."
  - stripe@20.0.0: both wrong-method calls return silently (the
    object comes back with missing/wrong data).
  - Correct methods work on both versions.
  - Run it: `cd node_app && npm install && npm test` (4/4 cases).
  - Note: the string/Buffer payload-type check ("Webhook payload must
    be provided as a string or a Buffer") already existed in v20; it
    is NOT the v21 change. The v21 change is the event-type guard
    (`object === 'v2.core.event'` vs `object === 'event'`).

## What is still modelled, not vendor-verified

- HubSpot Pipelines v1 status code (404) -- modelled, see above.
- Twilio Programmable Chat post-sunset status code (410) -- modelled.
- Salesforce SOAP 500 / Bulk 400 codes -- from retirement write-ups,
  not the REST policy page; not used by any mock in this repo.
- All mocks use fake clients with explicit version/date parameters;
  no live call was made to Salesforce, HubSpot, or Twilio (no accounts,
  no keys, $0).
