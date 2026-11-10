# Outreach drafts — 5 tailored messages (ready to copy-paste after the push)

Status: DRAFTS ONLY — do not send until the sandbox is pushed to GitHub.
Once pushed, replace `[REPO LINK]` in each message with the real repo URL
(e.g. `https://github.com/Sa3935/api-maintainer-validation`).
No message has been sent. No team has been contacted.

Go/no-go (from docs/outreach_template.md): at least 2 of 5 say they'd pay per repo.
Record answers in docs/outreach_template.md's table.

Honesty rules, from docs/outreach_targets.md:
- Gumroad and OpenCode are CONFIRMED hits from public PR/issue text — you may
  name the exact code.
- Zulip, Habitica and Ghost are confirmed heavy Stripe users with the right
  surface, NOT confirmed line-by-line `payment_method_types` passers — ask
  whether it bit them, never claim it did.
- Keep each message short, no pitch deck, no promise of a product. A straight
  "no" is useful data.

---

## 1. Gumroad — strongest, direct hit

Where to post: comment on PR #6290 — https://github.com/antiwork/gumroad/pull/6290

> Hi — quick question, I'm testing a tool idea, not selling anything.
>
> Your `PreparePaymentIntentService` still sets `intent_payment_method_types`
> (PR #6290). When Stripe shipped 2026-09-30 it removed `payment_method_types`
> from PaymentIntents — passing it now returns a 400. Did that bite you on
> upgrade?
>
> The tool I'm testing would watch the Stripe spec + changelog, find the exact
> lines in a repo that break, and open a PR with the fix (tests must pass first
> — nothing auto-merges). Demo: [REPO LINK]
>
> Would you pay per repo for that, and if so roughly what per repo per month?
> I'm deciding whether to build it at all, and a straight "no" is useful data.

Why this one first: it names their exact live-checkout code, so the question
is concrete, not generic.

## 2. OpenCode — strong, active right now

Where to post: comment on issue #62639 — https://github.com/anomalyco/opencode/issues/62639
(opened Nov 7, 2026 — they are configuring `payment_method_types` in Stripe
checkout this week, so the question is live, not hypothetical)

> Hi — quick question while you're in this code, I'm testing a tool idea, not
> selling anything.
>
> Issue #62639 says PayPal "needs to be enabled in the main Console billing
> code / Stripe checkout configuration (`payment_method_types`)". When Stripe
> shipped 2026-09-30 it removed `payment_method_types` — passing it now
> returns a 400. Did that affect you, or did you have to work around it?
>
> The tool I'm testing would watch the Stripe spec + changelog, find the exact
> lines in a repo that break, and open a PR with the fix (tests must pass first
> — nothing auto-merges). Demo: [REPO LINK]
>
> Would you pay per repo for that, and if so roughly what per repo per month?
> I'm deciding whether to build it at all, and a straight "no" is useful data.

## 3. Zulip — strong, admits the gap

Where to post: new issue / discussion in zulip/zulip — check first for an
existing Stripe-upgrade thread and comment there instead if one exists.
Evidence: https://zulip.readthedocs.io/en/8.3/subsystems/billing.html

> Hi — quick question, I'm testing a tool idea, not selling anything.
>
> Your billing docs say you're "not set up to do version upgrades where there
> are breaking changes" for Stripe. When Stripe shipped 2026-09-30 it removed
> `payment_method_types`, and in May it made `billed_until` on subscription
> items includable-only. Did either of those bite you?
>
> The tool I'm testing would watch the Stripe spec + changelog, find the exact
> lines in a repo that break, and open a PR with the fix (tests must pass first
> — nothing auto-merges). Demo: [REPO LINK]
>
> Would you pay per repo for that, and if so roughly what per repo per month?
> I'm deciding whether to build it at all, and a straight "no" is useful data.

Do NOT claim Zulip passes `payment_method_types` — that was not confirmed
line-by-line. The opener is their own docs admitting the missing process.

## 4. Habitica — good, Checkout Sessions + subscriptions

Where to post: new issue in HabitRPG/habitica — check first for an existing
Stripe thread and comment there instead if one exists.

> Hi — quick question, I'm testing a tool idea, not selling anything.
>
> You create Stripe Checkout Sessions for card changes
> (`website/server/libs/payments/stripe/checkout.js`) and run $5/mo
> subscriptions via Stripe. When Stripe shipped 2026-09-30 it removed
> `payment_method_types` from Checkout Sessions, and in May it made
> `billed_until` on subscription items includable-only. Did either of those
> bite you?
>
> The tool I'm testing would watch the Stripe spec + changelog, find the exact
> lines in a repo that break, and open a PR with the fix (tests must pass first
> — nothing auto-merges). Demo: [REPO LINK]
>
> Would you pay per repo for that, and if so roughly what per repo per month?
> I'm deciding whether to build it at all, and a straight "no" is useful data.

Do NOT claim Habitica passes `payment_method_types` — that was not confirmed
line-by-line. The opener is their Checkout Sessions + subscriptions surface,
which is confirmed.

## 5. Ghost — good, Stripe-only subscriptions

Where to post: new discussion in TryGhost/Ghost — check first for an existing
Stripe/billing thread and comment there instead if one exists.
Evidence: https://github.com/TryGhost/Ghost

> Hi — quick question, I'm testing a tool idea, not selling anything.
>
> Ghost's paid tiers run entirely through Stripe subscriptions. In May, Stripe
> made `billed_until` on subscription items includable-only — it silently
> comes back empty unless requested. Did that change (or the Sep 30
> `payment_method_types` removal) bite anything you read from
> SubscriptionItems?
>
> The tool I'm testing would watch the Stripe spec + changelog, find the exact
> lines in a repo that break, and open a PR with the fix (tests must pass first
> — nothing auto-merges). Demo: [REPO LINK]
>
> Would you pay per repo for that, and if so roughly what per repo per month?
> I'm deciding whether to build it at all, and a straight "no" is useful data.

Do NOT claim Ghost passes `payment_method_types` — that was not confirmed
line-by-line. The opener is the `billed_until` change, which fits their
subscription-heavy surface.

---

## Order to send

1. Gumroad, 2. OpenCode — confirmed hits, send first.
2. Zulip, Habitica, Ghost — send after, with the honesty caveats above.

Send all five only after the push, so every message carries a working repo
link. If a team replies, log it in docs/outreach_template.md: breaks hit
them? would pay? price? notes?
