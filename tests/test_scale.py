"""Scale check: detector on a 150-file synthetic repo (offline, fast).

Asserts the honest numbers in scale/scale_report.json:
- all 6 Python break call sites found in the large repo,
- 0 control files flagged as breaks,
- the comment/docstring over-count is recorded (decoy hits > 0),
  because the detector's call-site scan is text-based.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "scale" / "scale_report.json"


@pytest.fixture(scope="module")
def report():
    result = subprocess.run(
        [sys.executable, "-m", "detector.scale_check"],
        cwd=ROOT, capture_output=True, text=True, timeout=300,
    )
    assert result.returncode == 0, "scale check failed:\n%s\n%s" % (result.stdout, result.stderr)
    return json.loads(REPORT.read_text(encoding="utf-8"))


def test_scale_repo_size(report):
    assert report["generated_files"] == 150
    assert report["generated_lines"] >= 1000


def test_scale_all_real_breaks_found(report):
    assert report["real_call_sites_found"] == 6
    assert report["real_call_sites_total"] == 6
    assert all(report["real_call_sites"].values())


def test_scale_zero_control_false_positives(report):
    assert report["control_files_flagged_as_breaks"] == []
    assert report["false_positives"] == 0


def test_scale_decoy_overcount_is_recorded(report):
    """Text-based call-site scan counts comment-only mentions as hits.
    This is a known limitation, recorded here -- not hidden, not a GO gate."""
    assert report["decoy_comment_only_hits"] > 0
    assert report["other_unexpected_hits"] == 0
    assert "decoy" in report["call_site_precision_note"].lower()
