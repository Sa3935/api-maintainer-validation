/* Customer app code -- NODE BREAK N1 (stripe-node 21, wrong parser throws).
 *
 * stripe-node 21.0.0 (pins Stripe API 2026-03-25.dahlia) added a guard
 * (PR #2616 / #2618, release notes
 * https://github.com/stripe/stripe-node/releases/tag/v21.0.0):
 *  - stripe.webhooks.constructEvent() now THROWS when passed a thin
 *    (v2.core.event) event notification, and tells you to use
 *    stripe.parseEventNotification() instead.
 *  - stripe.parseEventNotification() now THROWS when passed a snapshot
 *    (v1, object:'event') webhook payload, and tells you to use
 *    stripe.webhooks.constructEvent() instead.
 * Before 21, using the wrong parser did NOT raise; it just returned an
 * object with missing data ("signature passes but no data comes out").
 * Verified live in this repo: stripe@21.0.0 throws both ways, while
 * stripe@20.0.0 silently returns in both wrong-method cases
 * (see test_node_breaks.js and docs/MULTI_API_SOURCES.md).
 *
 * No network, no real keys: the Stripe client is constructed with a
 * fake test key and only its local webhook-verification code runs.
 */
'use strict';

function handleSnapshotEvent(stripe, payload, sigHeader, secret) {
  // CORRECT: snapshot (v1) event -> constructEvent.
  return stripe.webhooks.constructEvent(payload, sigHeader, secret);
}

function handleThinEvent(stripe, payload, sigHeader, secret) {
  // CORRECT: thin (v2.core.event) notification -> parseEventNotification.
  return stripe.parseEventNotification(payload, sigHeader, secret);
}

function handleThinEventWithConstructEvent(stripe, payload, sigHeader, secret) {
  // BREAK (N1a): thin event fed to constructEvent.
  // stripe-node <21 returned it silently; >=21 throws.
  return stripe.webhooks.constructEvent(payload, sigHeader, secret);
}

function handleSnapshotWithParseEventNotification(stripe, payload, sigHeader, secret) {
  // BREAK (N1b): snapshot event fed to parseEventNotification.
  // stripe-node <21 returned it silently; >=21 throws.
  return stripe.parseEventNotification(payload, sigHeader, secret);
}

module.exports = {
  handleSnapshotEvent,
  handleThinEvent,
  handleThinEventWithConstructEvent,
  handleSnapshotWithParseEventNotification,
};
