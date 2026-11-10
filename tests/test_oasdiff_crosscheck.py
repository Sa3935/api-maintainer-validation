"""Cross-check the Python spec diff against the REAL oasdiff binary.

Skipped unless an oasdiff binary is available (PATH, or OASDIFF_BIN env).
Reproduced 2026-11-09 with oasdiff 1.37.0:
  curl -sL -o /tmp/oasdiff.tar.gz \
    https://github.com/oasdiff/oasdiff/releases/download/v1.37.0/oasdiff_1.37.0_linux_amd64.tar.gz
  tar xzf /tmp/oasdiff.tar.gz -C /tmp/oasdiff
  OASDIFF_BIN=/tmp/oasdiff/oasdiff python -m pytest tests/test_oasdiff_crosscheck.py -q

Findings from that run (recorded here, not just in the test):
- oasdiff flags `payment_method_types` removed on POST /v1/checkout/sessions,
  POST /v1/payment_intents, POST /v1/setup_intents -- the same 3 endpoints
  the Python detector watches. It also flags the {intent} update/confirm
  variants, which the Python detector does not watch (documented gap).
- Raw oasdiff output is 80,685 changes, overwhelmingly response-side
  noise (anyOf additions, enum additions). A production tool must filter
  to watched endpoints + call sites, or the signal drowns.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _find_oasdiff():
    env = os.environ.get("OASDIFF_BIN")
    if env and Path(env).exists():
        return env
    return shutil.which("oasdiff")


def test_oasdiff_confirms_payment_method_types_removal():
    binary = _find_oasdiff()
    if not binary:
        pytest.skip("oasdiff binary not found (set OASDIFF_BIN or put oasdiff on PATH)")
    result = subprocess.run(
        [binary, "breaking",
         "specs/spec3-2026-03-25.dahlia.yaml",
         "specs/spec3-2026-09-30.endive.yaml"],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )
    # oasdiff exits 0 with the full change list on stdout in this version.
    assert result.returncode == 0, result.stderr[:500]
    out = result.stdout
    for endpoint in ("/v1/checkout/sessions", "/v1/payment_intents", "/v1/setup_intents"):
        assert endpoint in out
    assert out.count("removed the request property `payment_method_types`") >= 3
    # The raw output is mostly noise -- record the scale, do not assert on it.
    assert "changes:" in out.splitlines()[0]
