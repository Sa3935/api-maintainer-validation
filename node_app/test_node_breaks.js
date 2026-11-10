/* Node break-reproduction tests (real stripe@21.0.0, no network, no keys).
 *
 * Run:  cd node_app && npm install && npm test
 * Uses only local HMAC signature verification, exactly as a real webhook
 * endpoint does. Exits 0 when all 4 cases behave as stripe-node 21 does.
 */
'use strict';

const assert = require('node:assert');
const crypto = require('node:crypto');
const Stripe = require('stripe');
// stripe@21 does not export ./package.json, so read it from disk.
const pkg = JSON.parse(require('node:fs').readFileSync(
  require('node:path').join(__dirname, 'node_modules', 'stripe', 'package.json'),
  'utf-8',
));
const {
  handleSnapshotEvent,
  handleThinEvent,
  handleThinEventWithConstructEvent,
  handleSnapshotWithParseEventNotification,
} = require('./webhook');

const SECRET = 'whsec_testsecret1234567890abcdef';

function sign(payload) {
  const t = Math.floor(Date.now() / 1000);
  const sig = crypto.createHmac('sha256', SECRET).update(`${t}.${payload}`).digest('hex');
  return `t=${t},v1=${sig}`;
}

const SNAPSHOT = JSON.stringify({
  id: 'evt_test_1', object: 'event', type: 'checkout.session.completed',
  livemode: false, api_version: '2026-03-25.dahlia',
});
const THIN = JSON.stringify({
  id: 'evt_test_2', object: 'v2.core.event', type: 'payment_intent.created',
  livemode: false, created: '2026-01-01T00:00:00.000Z', data: {},
  related_object: { url: '/v1/payment_intents/pi_test_1' },
});

function main() {
  console.log('stripe version:', pkg.version);
  assert.ok(pkg.version.startsWith('21.'), `expected stripe 21.x, got ${pkg.version}`);
  const stripe = new Stripe('sk_test_fake123', { apiVersion: '2026-03-25.dahlia' });

  // Correct methods must work.
  assert.strictEqual(handleSnapshotEvent(stripe, SNAPSHOT, sign(SNAPSHOT), SECRET).id, 'evt_test_1');
  console.log('PASS constructEvent(snapshot) works');
  assert.strictEqual(handleThinEvent(stripe, THIN, sign(THIN), SECRET).id, 'evt_test_2');
  console.log('PASS parseEventNotification(thin) works');

  // Wrong methods must THROW on stripe 21 (they did not on stripe 20).
  assert.throws(
    () => handleThinEventWithConstructEvent(stripe, THIN, sign(THIN), SECRET),
    /Use stripe\.parseEventNotification instead/,
  );
  console.log('PASS constructEvent(thin) throws, points to parseEventNotification');
  assert.throws(
    () => handleSnapshotWithParseEventNotification(stripe, SNAPSHOT, sign(SNAPSHOT), SECRET),
    /Use stripe\.webhooks\.constructEvent instead/,
  );
  console.log('PASS parseEventNotification(snapshot) throws, points to constructEvent');

  console.log('NODE BREAKS: 4/4 passed (stripe 21 wrong-parser guard confirmed)');
}

main();
