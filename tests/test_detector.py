"""Detector tests: 7/7 real breaks flagged, 0 false positives, 2 upcoming warnings.

Runs the real detector against the real published Stripe specs
(specs/*.yaml). This is slow (~30-60s: the specs are ~6MB of YAML each)
because it parses both specs; that cost is the point -- it proves the
detection is real, not hard-coded. The non-Stripe breaks are verified
against their vendor registries + call sites in the same run.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "detector" / "report.json"

ALL_BREAK_IDS = {
    "B1-payment_method_types-removed",
    "B2-billed_until-includable",
    "B3-Reversal-renamed",
    "S1-salesforce-v21-30-retired",
    "H1-hubspot-lists-v1-sunset",
    "T1-twilio-programmable-chat-sunset",
    "N1-stripe-node-21-wrong-parser-throws",
}
STRIPE_IDS = {
    "B1-payment_method_types-removed",
    "B2-billed_until-includable",
    "B3-Reversal-renamed",
}
UPCOMING_IDS = {
    "S2-salesforce-v31-40-retire-2028",
    "H2-hubspot-pipelines-v1-sunset-2026-12-04",
}


@pytest.fixture(scope="module")
def report():
    """Run the detector once per test module, return its JSON report."""
    result = subprocess.run(
        [sys.executable, "-m", "detector.detect"],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )
    assert result.returncode == 0, "detector failed:\n%s\n%s" % (result.stdout, result.stderr)
    return json.loads(REPORT.read_text(encoding="utf-8"))


def test_detector_flags_all_seven_breaks(report):
    assert report["summary"]["detected"] == 7
    assert report["summary"]["total_known_breaks"] == 7
    assert report["summary"]["missed"] == 0
    ids = {b["id"] for b in report["detected_breaks"]}
    assert ids == ALL_BREAK_IDS


def test_detector_stripe_subset_still_three_of_three(report):
    """The original Stripe verdict must not regress when vendors are added."""
    ids = {b["id"] for b in report["detected_breaks"]}
    assert STRIPE_IDS <= ids


def test_detector_has_zero_false_positives(report):
    assert report["summary"]["false_positives"] == 0
    assert report["false_positives"] == []


def test_detector_upcoming_warnings(report):
    assert report["summary"]["upcoming_warnings_total"] == 2
    assert report["summary"]["upcoming_warnings_detected"] == 2
    assert report["summary"]["upcoming_warnings_missed"] == 0
    ids = {b["id"] for b in report["upcoming_warnings"]}
    assert ids == UPCOMING_IDS


def test_detector_go_verdict(report):
    assert report["summary"]["go_no_go"] == "GO"


def test_spec_versions_are_real(report):
    assert report["old_spec_version"] == "2026-03-25.dahlia"
    assert report["new_spec_version"] == "2026-09-30.endive"


def test_controls_not_flagged(report):
    flagged_ids = {b["id"] for b in report["detected_breaks"]}
    for ctrl in ("C1-customers-create", "C2-webhook-construct_event",
                 "C3-salesforce-v60-supported", "C4-hubspot-lists-v3",
                 "C5-twilio-conversations", "C6-node-correct-parser"):
        assert ctrl not in flagged_ids
    assert all(c["flagged"] is False for c in report["controls"])
