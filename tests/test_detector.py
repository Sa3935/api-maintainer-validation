"""Detector tests: 3/3 real breaks flagged, 0 false positives.

Runs the real detector against the real published Stripe specs
(specs/*.yaml). This is slow (~30-60s: the specs are ~6MB of YAML each)
because it parses both specs; that cost is the point -- it proves the
detection is real, not hard-coded.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "detector" / "report.json"


@pytest.fixture(scope="module")
def report():
    """Run the detector once per test module, return its JSON report."""
    result = subprocess.run(
        [sys.executable, "-m", "detector.detect"],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )
    assert result.returncode == 0, "detector failed:\n%s\n%s" % (result.stdout, result.stderr)
    return json.loads(REPORT.read_text(encoding="utf-8"))


def test_detector_flags_all_three_breaks(report):
    assert report["summary"]["detected"] == 3
    assert report["summary"]["total_known_breaks"] == 3
    assert report["summary"]["missed"] == 0
    ids = {b["id"] for b in report["detected_breaks"]}
    assert ids == {
        "B1-payment_method_types-removed",
        "B2-billed_until-includable",
        "B3-Reversal-renamed",
    }


def test_detector_has_zero_false_positives(report):
    assert report["summary"]["false_positives"] == 0
    assert report["false_positives"] == []


def test_detector_go_verdict(report):
    assert report["summary"]["go_no_go"] == "GO"


def test_spec_versions_are_real(report):
    assert report["old_spec_version"] == "2026-03-25.dahlia"
    assert report["new_spec_version"] == "2026-09-30.endive"


def test_controls_not_flagged(report):
    flagged_ids = {b["id"] for b in report["detected_breaks"]}
    assert "C1-customers-create" not in flagged_ids
    assert "C2-webhook-construct_event" not in flagged_ids
    assert all(c["flagged"] is False for c in report["controls"])
