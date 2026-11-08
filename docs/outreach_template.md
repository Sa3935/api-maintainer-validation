# Design-partner outreach template (step 5 of the validation plan)

Do NOT send this until the detector + codemod steps pass (see README
go/no-go). The point of the outreach is to answer the #1 risk -- will
anyone pay per repo for this? -- before building anything more.

## Who to talk to
5 dev teams found on GitHub/X who integrate Stripe (or Twilio / a CRM)
heavily. Look for repos with recent Stripe SDK upgrades, or teams
complaining about a Stripe upgrade in public.

## Message (short, no pitch deck)
> Hi -- quick question, I'm testing a tool idea. When Stripe shipped
> its 2026-09-30 (endive) release it removed `payment_method_types`
> from Checkout Sessions, and in May it made `billed_until` on
> subscription items includable-only. Did either of those bite you?
>
> The tool I'm testing would watch the Stripe spec + changelog, find
> the exact lines in your repo that break, and open a PR with the fix
> (tests must pass first -- nothing auto-merges). Would you pay per
> repo for that, and if so, roughly what per repo per month?
>
> No sales pitch -- I'm deciding whether to build it at all, and a
> straight "no" is useful data.

## Record answers here
| Team / repo | Breaks hit them? | Would pay? | Price they'd pay | Notes |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

Go/no-go on outreach: proceed only if at least 2 of 5 say they would pay.
