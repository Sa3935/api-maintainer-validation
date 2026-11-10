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
| Gumroad (antiwork/gumroad) | — | — | — | Not reached — PR #6290 merged, interactions restricted to collaborators only. User decided 2026-11-10 to leave at 4. |
| OpenCode (anomalyco/opencode) | Not answered | **No** | — | Gurvir-Dhillon (issue author) replied 2026-11-10 2:31 PM EST on issue #62639: "No I wouldn't" — https://github.com/anomalyco/opencode/issues/62639#issuecomment-6777192918 |
| Zulip (zulip/zulip) | — | — | — | Issue #40652 opened 2026-11-10, no reply as of 2:37 PM EST check. |
| Habitica (HabitRPG/habitica) | — | — | — | Issue #15743 opened 2026-11-10, no reply as of 2:37 PM EST check. |
| Ghost (TryGhost/Ghost) | — | — | — | Issue #32744 opened 2026-11-10, no reply as of 2:37 PM EST check (only an automated "needs:triage" label). |

Tally as of 2026-11-10 2:37 PM EST: 0 yes, 1 no, 3 awaiting reply. Go/no-go needs at least 2 yes.

Go/no-go on outreach: proceed only if at least 2 of 5 say they would pay.
