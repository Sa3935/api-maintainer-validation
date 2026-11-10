"""Node break N1 (stripe-node 21 wrong-parser guard).

The behaviour itself is verified by node_app/test_node_breaks.js against
the REAL stripe@21.0.0 package (npm install first: cd node_app && npm install).
That script is skipped here if stripe is not installed yet, so pytest
stays offline-safe; run_validation.sh installs it first when possible.
The text checks below always run and prove the Node call sites exist.
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
NODE_APP = ROOT / "node_app"


def test_node_webhook_file_has_wrong_parser_call_sites():
    source = (NODE_APP / "webhook.js").read_text(encoding="utf-8")
    assert "handleThinEventWithConstructEvent" in source
    assert "handleSnapshotWithParseEventNotification" in source
    assert "stripe.webhooks.constructEvent" in source
    assert "stripe.parseEventNotification" in source


def test_node_webhook_file_is_valid_js():
    result = subprocess.run(
        ["node", "--check", str(NODE_APP / "webhook.js")],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_node_breaks_against_real_stripe_21():
    """Live: real stripe@21.0.0, 4/4 cases in node_app/test_node_breaks.js."""
    stripe_pkg = NODE_APP / "node_modules" / "stripe" / "package.json"
    if not stripe_pkg.exists():
        pytest.skip("stripe not installed in node_app (run: cd node_app && npm install)")
    result = subprocess.run(
        ["node", "test_node_breaks.js"],
        cwd=NODE_APP, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, "node test failed:\n%s\n%s" % (result.stdout, result.stderr)
    assert "NODE BREAKS: 4/4 passed" in result.stdout
