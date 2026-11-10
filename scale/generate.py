"""Generate a larger synthetic customer repo for the scale check.

Deterministic (seeded): 150 Python files, ~1,900 lines total.
Contents:
- 6 files with REAL break call sites (one per Python break: B1, B2, B3,
  S1, H1, T1) -- the detector must find all of them.
- 120 control files calling only unchanged endpoints (customers_create,
  charges, etc.) -- must NOT be flagged as breaks.
- 24 decoy files that mention a break symbol ONLY in a comment or
  docstring (e.g. '# TODO: check payment_method_types') -- these
  measure the detector's text-based call-site over-count honestly:
  they are counted as hits by find_call_sites(), so call-site precision
  is <100% by design. The registry-anchored detection (which requires a
  specific call-site file from known_breaks.json) is NOT affected by
  decoys, and the scale report records both numbers separately.

Run: python -m scale.generate <target_dir>
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

CONTROL_CALLS = [
    'client.customers_create(email="a@example.com", name="A")',
    'client.charges_create(amount=100, currency="usd")',
    'client.invoices_create(customer="cus_1")',
    'client.products_create(name="Widget")',
    'client.prices_create(unit_amount=500, currency="usd")',
]

REAL_BREAKS = {
    "checkout_b1.py": 'client.checkout_sessions_create(mode="payment", payment_method_types=["card"])\n',
    "billing_b2.py": 'item = client.subscription_items_retrieve("si_1")\nreturn item.get("billed_until")\n',
    "refunds_b3.py": 'return sdk.Reversal.retrieve("trr_1")\n',
    "salesforce_s1.py": 'client = FakeSalesforceClient("v28.0")\nreturn client.query("SELECT Id FROM Account")\n',
    "hubspot_h1.py": 'return client.lists_v1_get("123")\n',
    "twilio_t1.py": 'return client.chat_channels_create("IS_1", "general")\n',
}

DECOY_COMMENTS = [
    '# TODO: check whether payment_method_types is still used anywhere\n',
    '"""Legacy note: billed_until used to come back by default."""\n',
    '# Reversal handling was moved to another service\n',
    '# NOTE: v28.0 Salesforce version is old, do not copy this comment\n',
]


def generate(target: Path, seed: int = 42) -> dict:
    rng = random.Random(seed)
    target.mkdir(parents=True, exist_ok=True)
    counts = {"real_break_files": 0, "control_files": 0, "decoy_files": 0, "total_lines": 0}

    for name, body in REAL_BREAKS.items():
        (target / name).write_text(
            '"""Synthetic customer file (real break call site)."""\n\n\ndef run(client, sdk=None):\n    %s' % body,
            encoding="utf-8",
        )
        counts["real_break_files"] += 1

    for i in range(120):
        calls = "\n    ".join(rng.choice(CONTROL_CALLS) for _ in range(rng.randint(2, 5)))
        (target / ("control_%03d.py" % i)).write_text(
            '"""Synthetic control file %d (unchanged endpoints only)."""\n\n\ndef run(client):\n    %s\n    return True\n' % (i, calls),
            encoding="utf-8",
        )
        counts["control_files"] += 1

    for i in range(24):
        comment = rng.choice(DECOY_COMMENTS)
        (target / ("decoy_%03d.py" % i)).write_text(
            '"""Synthetic decoy file %d."""\n%s\n\ndef run(client):\n    return client.customers_create(email="a@example.com")\n' % (i, comment),
            encoding="utf-8",
        )
        counts["decoy_files"] += 1

    counts["total_lines"] = sum(
        len(p.read_text(encoding="utf-8").splitlines()) for p in target.glob("*.py")
    )
    counts["total_files"] = len(list(target.glob("*.py")))
    return counts


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("scale/generated_repo")
    print(generate(target))
