# Outreach targets — step 5 of the APIs validation (verified 2026-11-09)

Do NOT contact anyone until the sandbox is pushed to GitHub.
Outreach needs a repo link to point at. Push first:
`gh repo create api-maintainer-validation --private --source . --remote origin --push`
then `git push origin fix/remove-payment-method-types`.
Template to use: `docs/outreach_template.md`. Go/no-go: at least 2 of 5 say they'd pay per repo.

## Ranked list

### 1. Gumroad — strongest, direct hit (antiwork/gumroad)
- Evidence: PR #6290 (Jul 25, 2026) names `Order::PreparePaymentIntentService#intent_payment_method_types` — Gumroad passes `payment_method_types` when creating PaymentIntents, in its live checkout code.
- Why it fits break B1: on Stripe API version 2026-09-30.endive, passing `payment_method_types` on a PaymentIntent returns a 400 (`payment_method_types_no_longer_supported`). Gumroad is exactly the team that would hit this on upgrade.
- Tailored opener: "Your `PreparePaymentIntentService` still sets `intent_payment_method_types` — did the Sep 30 Stripe removal bite you on upgrade?"
- Source: https://github.com/antiwork/gumroad/pull/6290

### 2. OpenCode — strong, active right now (anomalyco/opencode)
- Evidence: Issue #62639, opened Nov 7, 2026 — "Add PayPal support for Console billing and Go subscriptions" — says PayPal "needs to be enabled in the main Console billing code / Stripe checkout configuration (`payment_method_types`)". They are configuring `payment_method_types` in Stripe checkout this week, for credit purchases and Go subscriptions.
- Why it fits break B1: same 400-on-upgrade risk, and the team is touching that exact code now, so the question is live, not hypothetical.
- Tailored opener: comment on / reference issue #62639 — "while you're in the Console billing `payment_method_types` config, did the Sep 30 Stripe removal affect you?"
- Source: https://github.com/anomalyco/opencode/issues/62639

### 3. Zulip — strong, admits the gap (zulip/zulip)
- Evidence: Zulip's own billing docs (`zulip.readthedocs.io`, Billing / Development) say Stripe API version is pinned in `corporate/lib/stripe.py` as `STRIPE_API_VERSION`, and: "We currently aren't set up to do version upgrades where there are breaking changes, though breaking changes should be unlikely given the parts of the product we use."
- Why it fits: a tool that watches spec + changelog and opens a tested fix PR is exactly the missing upgrade process they describe. Zulip Cloud bills per-seat subscriptions via Stripe.
- Tailored opener: "Your billing docs say you're not set up for breaking-change Stripe upgrades — would a tool that flags the break and opens a tested PR help?"
- Source: https://zulip.readthedocs.io/en/8.3/subsystems/billing.html

### 4. Habitica — good, Checkout Sessions + subscriptions (HabitRPG/habitica)
- Evidence: code paths `website/server/libs/payments/stripe/checkout.js` (`createEditCardCheckoutSession`) and `website/server/libs/payments/stripe/subscriptions.js` (`getSubscriptionPaymentDetails`, `handlePaymentMethodChange`). Web subscriptions are $5/month, paid via Stripe on the website.
- Why it fits breaks B1 + B2: Checkout Sessions (B1) and recurring subscriptions (B2, `billed_until`).
- Tailored opener: "You create Stripe Checkout Sessions for card changes and run $5/mo subscriptions — did either the Sep 30 `payment_method_types` removal or the May `billed_until` change bite you?"
- Source: https://deepwiki.com/HabitRPG/habitica/8-payment-infrastructure and https://habitica.fandom.com/wiki/Subscription

### 5. Ghost — good, Stripe-only subscriptions (TryGhost/Ghost)
- Evidence: Ghost is MIT open source; paid memberships run entirely through the member's own Stripe account (Stripe Connect, tiers, trials, offers, 0% Ghost fee). Code includes Stripe subscription / customer / billing-portal handling.
- Why it fits break B2 mainly: subscription-heavy, so the silent `billed_until` change is the relevant one; Checkout Sessions less central than for Gumroad/OpenCode.
- Tailored opener: "Ghost's paid tiers are all Stripe subscriptions — did the May change making `billed_until` includable-only silently break anything you read from SubscriptionItems?"
- Source: https://github.com/TryGhost/Ghost (Stripe membership code, e.g. MockStripeServer / StripeSubscription in PR #26516 discussion)

## Dropped / replaced
- Medusa (medusajs/medusa) was on the earlier ungrounded list. Checked 2026-11-09: Medusa's Stripe Module Provider uses `automatic_payment_methods` and creates PaymentIntents via its provider — it is a framework for downstream stores, not a team whose own checkout passes `payment_method_types`. It is the weakest of the five and was replaced by OpenCode above. Keep Medusa only as a 6th alternate if one of the five does not reply.
- Note on verification limits: GitHub code search requires sign-in, so exact `payment_method_types` occurrences in Ghost / Habitica / Zulip repos could not be confirmed line-by-line on 2026-11-09. The Gumroad and OpenCode hits above are confirmed from public PR / issue text; the other three are confirmed as heavy Stripe users with the relevant surface (Checkout Sessions / subscriptions), not as confirmed `payment_method_types` passers. Say that honestly in outreach — ask whether it bit them, don't claim it did.
