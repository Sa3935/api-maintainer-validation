"""Real-repo scale check (synthetic large repo, offline).

Generates a 150-file synthetic customer repo (scale/generate.py),
runs the detector's call-site scan over it, and records:
- whether every Python break's real call site is found (must be 6/6),
- how many control files were wrongly counted as break call sites
  (must be 0 -- controls use only unchanged endpoints),
- call-site precision: how many text hits are real code vs comment/
  docstring-only decoys (honestly <100%: the detector's call-site
  scan is text-based, so decoys count as hits; registry-anchored
  detection is unaffected, because it requires a specific call-site
  file from known_breaks.json).

Output: scale/scale_report.json. Exit 0 when the report was produced.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from detector.detect import find_call_sites  # noqa: E402
from scale.generate import generate  # noqa: E402

# Symbol -> the real-break file that must contain it (real code, not a comment).
REAL_SITES = {
    "payment_method_types": "checkout_b1.py",
    "billed_until": "billing_b2.py",
    "Reversal": "refunds_b3.py",
    "v28.0": "salesforce_s1.py",
    "lists_v1": "hubspot_h1.py",
    "chat_channels_create": "twilio_t1.py",
}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="scale-repo-") as tmp:
        target = Path(tmp) / "generated_repo"
        counts = generate(target)
        hits = find_call_sites(target)

        real_found = {}
        for symbol, filename in REAL_SITES.items():
            files = hits.get(symbol, [])
            real_found[symbol] = any(f.endswith(filename) for f in files)

        # Control files must never appear as a break call site.
        control_flagged = sorted({
            f for symbol, files in hits.items()
            for f in files if f.startswith("generated_repo/control_")
            and symbol in REAL_SITES
        })

        # Precision: only the break symbols are counted here (controls
        # use customers_create etc., which are not break symbols).
        # Hits that are decoy-only files (symbol only in a comment/
        # docstring) vs hits in real code files.
        break_hits = {s: hits.get(s, []) for s in REAL_SITES}
        total_hits = sum(len(v) for v in break_hits.values())
        decoy_hits = sum(
            1 for files in break_hits.values() for f in files if "/decoy_" in f
        )
        # Count hits per break symbol that are NOT the real file and NOT
        # a decoy: in this synthetic repo there should be none.
        other_hits = sum(
            1 for symbol, files in break_hits.items() for f in files
            if "/decoy_" not in f and not f.endswith(REAL_SITES[symbol])
        )

        report = {
            "generated_files": counts["total_files"],
            "generated_lines": counts["total_lines"],
            "real_break_files": counts["real_break_files"],
            "control_files": counts["control_files"],
            "decoy_files": counts["decoy_files"],
            "real_call_sites_found": sum(real_found.values()),
            "real_call_sites_total": len(REAL_SITES),
            "real_call_sites": real_found,
            "control_files_flagged_as_breaks": control_flagged,
            "false_positives": len(control_flagged),
            "call_site_hits_total": total_hits,
            "decoy_comment_only_hits": decoy_hits,
            "other_unexpected_hits": other_hits,
            "call_site_precision_note": (
                "Text-based call-site scan counts comment/docstring-only "
                "mentions as hits: %d of %d hits are decoy-only. "
                "Registry-anchored detection (known_breaks.json call_sites) "
                "is unaffected. A production detector would need AST-level "
                "call-site mapping to fix this." % (decoy_hits, total_hits)
            ),
        }
        out = ROOT / "scale" / "scale_report.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0


if __name__ == "__main__":
    sys.exit(main())
