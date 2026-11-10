# api-maintainer-validation

A $0 sandbox that proves (or disproves) the core claim of the
self-maintaining APIs idea -- "Dependabot for API contracts" -- using
**real** vendor breaking changes, **real** published Stripe OpenAPI
specs, and mocked vendors (no network, no real keys, no paid tools).

The question being tested: can a tool detect a vendor API break, map it
to the exact lines in a customer repo, and open a fix PR that passes
tests -- before any product is built?

## The 7 real breaks tested (plus 2 upcoming warnings)

| # | Break | Source | Detection |
|---|---|---|---|
| B1 | `payment_method_types` removed from Checkout Sessions / PaymentIntents / SetupIntents in Stripe API `2026-09-30.endive` (HTTP 400 if sent) | [Stripe changelog, 2026-09-30.endive](https://docs.stripe.com/changelog) | Spec diff (real specs) |
| B2 | `billed_until` on SubscriptionItem changed to includable in `2026-05-27.dahlia` -- code reading it directly gets an empty value, silently | [Stripe changelog, dahlia](https://docs.stripe.com/changelog/dahlia/2026-05-27/subscription-item-billed-until-includable) | Changelog registry only -- **invisible in the spec diff** |
| B3 | `stripe.Reversal` renamed to `stripe.TransferReversal` in stripe-python 16.0.0 | [stripe-python CHANGELOG 16.0.0](https://github.com/stripe/stripe-python/blob/master/CHANGELOG.md) | SDK-changelog registry only -- not in the REST spec at all |
| S1 | Salesforce Platform API versions 21.0-30.0 retired Summer '25 -- REST returns HTTP 410:GONE | [Salesforce API End-of-Life Policy](https://developer.salesforce.com/docs/platform/api-rest/guide/api-rest-eol.html) | Retirement registry (version pinned in code vs retired ranges) |
| H1 | HubSpot Contact Lists API (v1) sunset April 30, 2026 -- v1 endpoints return HTTP 404 | [HubSpot changelog](https://developers.hubspot.com/changelog/extension-contact-lists-api-v1-sunset-moved-to-april-30-2026) | Sunset registry |
| T1 | Twilio Programmable Chat API sunset July 25, 2022 -- migrate to Conversations | [Twilio changelog](https://www.twilio.com/en-us/changelog/programmable-chat-end-of-life-notice) | Sunset registry |
| N1 | stripe-node 21: `constructEvent` throws on a thin event, `parseEventNotification` throws on a snapshot event; before 21 the wrong parser returned silently | [stripe-node v21.0.0 release notes](https://github.com/stripe/stripe-node/releases/tag/v21.0.0) (PR #2616) | Node SDK-changelog registry + live Node test |

Upcoming warnings (detected, NOT counted in the GO verdict):
- **S2** Salesforce API 31.0-40.0: deprecated Summer '27, retired Summer '28.
- **H2** HubSpot Pipelines API v1: sunsets December 4, 2026, v1 endpoints
  stop responding after that date.

Controls (must NOT be flagged): `POST /v1/customers`, webhook signature
verification, Salesforce v60.0, HubSpot Lists v3, Twilio Conversations,
and the correct Node parser per event type.

Full sources, dates, and which status codes are vendor-stated vs
modelled by this sandbox: `docs/MULTI_API_SOURCES.md`.

## Honest findings (read this before trusting the verdict)

1. **A pure spec-diff tool would miss 5 of the 7 breaks.** `billed_until`
   is byte-identical as a property in both specs; only the changelog says
   it stopped being returned by default. The `Reversal` rename, the
   Salesforce retirement, the HubSpot/Twilio sunsets, and the stripe-node
   guard are all invisible to a spec diff. The detector therefore combines
   spec diff + changelog + SDK-changelog + retirement/sunset registries.
2. **The Node webhook claim is now verified live, in Node.** The original
   plan's stripe-node 21 break is reproduced in `node_app/` against the
   real `stripe@21.0.0` package (4/4 cases), and contrasted with
   `stripe@20.0.0`, which returns silently in both wrong-method cases.
   Run it: `cd node_app && npm install && npm test`.
3. **oasdiff now works -- and agrees.** The real oasdiff binary could not
   be downloaded when this repo was first built (0-byte artifacts). Retried
   2026-11-09, it downloaded fine (v1.37.0) and flags
   `payment_method_types` removed on the same 3 watched endpoints
   (see `tests/test_oasdiff_crosscheck.py`). Two warnings from that run:
   raw oasdiff output is **80,685 changes**, overwhelmingly response-side
   noise, so a production tool must filter to watched endpoints + call
   sites; and oasdiff also flags the `{intent}` update/confirm variants,
   which the Python detector does not watch.
4. **Fixes now exist for B2 and B3, but they are opt-in, not automatic.**
   `fixer/semantic_fixes.py` adds `expand=["billed_until"]` (B2, requires
   explicit `--confirm` -- it is a semantic decision) and renames
   `.Reversal` -> `.TransferReversal` (B3, AST-based, docstrings untouched).
   Both are verified by tests on temp copies; the default codemod still
   covers B1 only, and neither fix is applied to `app/` by any script.
   B3's fix is one-way: it works on stripe-python 16 and breaks on 15.
   S1/H1/T1/N1 have no codemod -- the fix is a version bump / endpoint
   migration, documented per break in `known_breaks.json`.
5. **Call-site mapping is text-based, and the scale check measures it.**
   On a 150-file synthetic repo the detector finds all 6 Python break
   call sites with 0 control false positives -- but comment/docstring-only
   mentions also count as hits (see `scale/scale_report.json`). A
   production detector needs AST-level call-site mapping to fix that.

## The Salesforce difference (why S1 matters most)

Stripe pins an integration to its API version indefinitely, so a break
only bites when a team **deliberately upgrades**. Salesforce retires
versions on a schedule (3-year minimum support, 1-year notice, then
410:GONE), so the break bites whether or not the team upgrades. That
forced retirement is the urgency Stripe cannot prove -- and it is now
tested here (S1 retired, S2 upcoming).

## How to run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./run_validation.sh
```

`run_validation.sh` runs the full loop and prints the verdict:
1. pytest on `main` -- the break-reproduction tests pass, and
   `test_checkout_passes_after_codemod` **fails** (the break is real).
2. Detector against the real specs + vendor registries -> `detector/report.json`.
3. Codemod on a branch `fix/remove-payment-method-types` -- removes
   `payment_method_types` from `app/checkout.py` only, writes
   `patches/fix-payment-method-types.patch`, commits the branch.
4. pytest on that branch -- everything passes, including the codemod test.
5. Scale check (150-file synthetic repo) + Node test summary.
6. Back on `main`, verdict written to `validation_results.json`.

Or run the pieces directly:
```bash
python -m pytest tests/ -q            # full suite (detector test takes ~1 min; oasdiff test skips unless OASDIFF_BIN is set)
python -m detector.detect                 # detector only (7 breaks + 2 upcoming)
python -m detector.scale_check            # scale check only
python -m fixer.codemod --check           # codemod dry run
cd node_app && npm install && npm test    # Node break, real stripe@21.0.0
```

## Go / no-go criteria

Proceed with the idea **only if all three hold**:
- Detector flags **7/7** real breaks with **0 false positives**,
- the fix patch **passes tests** on its branch,
- and (step 5, your job, template in `docs/outreach_template.md`)
  at least **2 of 5** dev teams say they would pay per repo.

Otherwise drop it.

## Layout

- `app/` -- the "customer repo": small Python app using the breaks,
  plus controls. Talks only to mocked vendors (offline).
- `node_app/` -- Node customer code + live test for the stripe-node 21
  break (real `stripe@21.0.0`, `package.json` pinned; `node_modules/`
  is gitignored).
- `detector/` -- spec diff + vendor retirement/sunset registries +
  call-site mapping + JSON/Markdown report. `detector/data/` holds
  `known_breaks.json` and `vendor_retirements.json`.
- `fixer/` -- deterministic AST codemod for B1, plus opt-in
  `semantic_fixes.py` for B2/B3.
- `scale/` -- generator + report for the 150-file scale check.
- `tests/` -- pytest suite (breaks, detector, codemod, semantic fixes,
  multi-API, Node, scale, real SDK surface, oasdiff cross-check).
- `specs/` -- real published Stripe OpenAPI specs (see `docs/SPECS.md`).
- `docs/` -- spec provenance, multi-API sources, outreach template/targets.
- `patches/` -- the fix patch produced by the codemod run.

## Still NOT proven

- The real GitHub PR flow: no real PR was ever opened, no GitHub App
  install, no webhook, no permissions test. The push itself failed
  earlier, so the "open a PR for a customer" loop is still unproven.
- Live calls to Salesforce, HubSpot, or Twilio (no accounts, no keys).
- Whether any team will pay (step 5 outreach -- not done, not by this repo).
- AST-level call-site mapping (text-based scan over-counts comments).
- The Python detector does not watch the `{intent}` update/confirm
  variants that oasdiff flags for `payment_method_types`.
