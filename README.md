# api-maintainer-validation

A $0 sandbox that proves (or disproves) the core claim of the
self-maintaining APIs idea -- "Dependabot for API contracts" -- using
**real** Stripe breaking changes, **real** published Stripe OpenAPI
specs, and a mocked Stripe (no network, no real keys, no paid tools).

The question being tested: can a tool detect a vendor API break, map it
to the exact lines in a customer repo, and open a fix PR that passes
tests -- before any product is built?

## The 3 real breaks tested

| # | Break | Source | Detection |
|---|---|---|---|
| B1 | `payment_method_types` removed from Checkout Sessions / PaymentIntents / SetupIntents in API version `2026-09-30.endive` (HTTP 400 if sent) | [Stripe changelog, 2026-09-30.endive](https://docs.stripe.com/changelog) | Spec diff (real specs) |
| B2 | `billed_until` on SubscriptionItem changed to includable in `2026-05-27.dahlia` -- code reading it directly gets an empty value, silently | [Stripe changelog, dahlia](https://docs.stripe.com/changelog/dahlia/2026-05-27/subscription-item-billed-until-includable) | Changelog registry only -- **invisible in the spec diff** (see below) |
| B3 | `stripe.Reversal` renamed to `stripe.TransferReversal` in stripe-python 16.0.0 | [stripe-python CHANGELOG 16.0.0](https://github.com/stripe/stripe-python/blob/master/CHANGELOG.md) | SDK-changelog registry only -- not in the REST spec at all |

Two controls are included and must NOT be flagged: `POST /v1/customers`
(unchanged request params) and webhook signature verification
(`stripe.Webhook.construct_event`, unchanged in stripe-python 15 -> 16).

## Honest findings (read this before trusting the verdict)

1. **A pure spec-diff tool would miss 2 of the 3 breaks.** `billed_until`
   is byte-identical as a property in both specs; only the changelog says
   it stopped being returned by default. The `Reversal` rename is an SDK
   change, not a REST change. The detector therefore combines spec diff +
   changelog + SDK-changelog registries, and says so in its report.
2. **The Node webhook claim from the original plan did not survive
   verification.** The stripe-node 21 `constructEvent` throwing behaviour
   has no clean Python equivalent, so it was replaced with B3, a
   verified Python break (stripe-python 16.0.0 rename, confirmed live
   against the real `stripe==16.0.0` package).
3. **oasdiff could not be installed in this sandbox** (release-artifact
   downloads returned 0 bytes). The detector implements the same
   comparison in Python; the equivalent oasdiff command is documented in
   `detector/detect.py`.

## The Stripe caveat

Stripe pins an integration to its API version indefinitely, so a break
only bites when a team **deliberately upgrades** to a new major version.
This sandbox tests the **upgrade path**, not forced retirement. A
forced-retirement API (e.g. Salesforce: 3-year support, 1-year notice,
then 410 GONE) creates more urgency and may be a better first API --
that is a product decision, not something this sandbox settles.

## How to run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./run_validation.sh
```

`run_validation.sh` runs the full loop and prints the verdict:
1. pytest on `main` -- the break-reproduction tests pass, and
   `test_checkout_passes_after_codemod` **fails** (the break is real).
2. Detector against the real specs -> `detector/report.json`.
3. Codemod on a branch `fix/remove-payment-method-types` -- removes
   `payment_method_types` from `app/checkout.py` only, writes
   `patches/fix-payment-method-types.patch`, commits the branch.
4. pytest on that branch -- everything passes, including the codemod test.
5. Back on `main`, verdict written to `validation_results.json`.

Or run the pieces directly:
```bash
python -m pytest tests/ -x -q            # tests (detector test takes ~1 min)
python -m detector.detect                 # detector only
python -m fixer.codemod --check           # codemod dry run
```

## Go / no-go criteria

Proceed with the idea **only if all three hold**:
- Detector flags **3/3** real breaks with **0 false positives**,
- the fix patch **passes tests** on its branch,
- and (step 5, your job, template in `docs/outreach_template.md`)
  at least **2 of 5** dev teams say they would pay per repo.

Otherwise drop it.

## Layout

- `app/` -- the "customer repo": small Python app using the 3 breaks,
  plus controls. Talks only to `FakeStripeClient` (mocked, offline).
- `detector/` -- spec diff + call-site mapping + JSON/Markdown report.
- `fixer/` -- deterministic AST codemod for break B1 only.
- `tests/` -- pytest suite (breaks, detector, codemod, real SDK surface).
- `specs/` -- real published Stripe OpenAPI specs (see `docs/SPECS.md`).
- `docs/` -- spec provenance + outreach template.
- `patches/` -- the fix patch produced by the codemod run.
