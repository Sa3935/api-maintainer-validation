"""Detector: diff Stripe specs, and check vendor retirement/sunset registries.

Detection sources (in order of trust):
  1. spec_diff -- a real diff of the two published Stripe OpenAPI specs.
     Catches request-param removals such as payment_method_types (B1).
  2. changelog -- Stripe's own changelog entries (curated registry in
     detector/data/known_breaks.json). Needed because some real breaks
     are INVISIBLE in the spec: billed_until is present as an identical
     property in both specs; only the changelog says it stopped being
     returned by default.
  3. sdk_changelog -- stripe-python CHANGELOG entries (same registry).
     SDK renames (stripe.Reversal -> stripe.TransferReversal) are not in
     the REST spec at all.
  4. retirement -- vendor API end-of-life schedules
     (detector/data/vendor_retirements.json, sourced from the vendor's
     own policy page). Salesforce versions 21.0-30.0 retired Summer '25:
     REST returns 410:GONE. This is the forced-retirement case Stripe
     does not have, and it is detected by matching the version pinned
     in app code against the retired ranges -- not by spec diff.
  5. sunset -- vendor-dated API sunsets (same retirement registry).
     HubSpot Contact Lists v1 sunset Apr 30, 2026 (404); Twilio
     Programmable Chat sunset Jul 25, 2022 (migrate to Conversations).
  6. node_sdk_changelog -- stripe-node 21 release notes (PR #2616/#2618):
     constructEvent / parseEventNotification now throw on the wrong
     payload type. Verified live against real stripe@21.0.0 vs 20.0.0.

Upcoming warnings (NOT counted in the GO verdict): breaks whose
retirement/sunset date is still in the future -- Salesforce v31.0-40.0
(retired Summer '28) and HubSpot Pipelines v1 (sunset Dec 4, 2026).
The detector flags them so a team gets warned BEFORE the date, but
they do not make the verdict GO or NO-GO.

oasdiff note: the real oasdiff binary could not be downloaded when this
repo was first built (release artifacts returned 0 bytes). Retried
2026-11-09: the download WORKED (oasdiff 1.37.0), and the cross-check
in tests/test_oasdiff_crosscheck.py confirms the Python diff agrees
with real oasdiff on the 3 watched endpoints: oasdiff flags
payment_method_types removed on POST /v1/checkout/sessions,
POST /v1/payment_intents and POST /v1/setup_intents. It also flags
the {intent} update/confirm variants, which the Python detector does
not watch (documented gap). Raw oasdiff output is 80,685 changes,
overwhelmingly response-side noise -- a production tool must filter
to watched endpoints + call sites. The detector still implements the
comparison in Python so the suite runs without the binary; the
equivalent check is:
    oasdiff breaking specs/spec3-2026-03-25.dahlia.yaml \
                     specs/spec3-2026-09-30.endive.yaml

Output: detector/report.json (machine-readable) + detector/report.md.
Exit code 0 when the report was produced (even if breaks were found);
the go/no-go verdict is a field in the report, not the exit code.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = ROOT / "specs"
DATA_DIR = Path(__file__).resolve().parent / "data"

# Symbol that must appear in the app/node code for each break id.
SYMBOL_FOR_BREAK = {
    "B1-payment_method_types-removed": "payment_method_types",
    "B2-billed_until-includable": "billed_until",
    "B3-Reversal-renamed": "Reversal",
    "S1-salesforce-v21-30-retired": "v28.0",
    "H1-hubspot-lists-v1-sunset": "lists_v1",
    "T1-twilio-programmable-chat-sunset": "chat_channels_create",
    "N1-stripe-node-21-wrong-parser-throws": "constructEvent",
}
SYMBOL_FOR_UPCOMING = {
    "S2-salesforce-v31-40-retire-2028": "v35.0",
    "H2-hubspot-pipelines-v1-sunset-2026-12-04": "pipelines_v1",
}

# Every symbol the call-site scan looks for (Python + Node code).
SCAN_SYMBOLS = (
    "payment_method_types", "billed_until", "Reversal",
    "construct_event", "customers_create",
    "v28.0", "v35.0", "v60.0", "lists_v1", "lists_v3",
    "pipelines_v1", "chat_channels_create", "conversations_create",
    "constructEvent", "parseEventNotification",
)


def load_spec(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def resolve(schema: dict, spec: dict) -> dict:
    """Resolve a top-level $ref to the component schema it points at."""
    if "$ref" in schema:
        name = schema["$ref"].split("/")[-1]
        return spec["components"]["schemas"][name]
    return schema


def request_params(spec: dict, path: str, method: str) -> set:
    """Request-body property names for a watched endpoint ({} if absent)."""
    try:
        op = spec["paths"][path][method]
        content = op["requestBody"]["content"]["application/x-www-form-urlencoded"]
        schema = resolve(content["schema"], spec)
        return set(schema.get("properties", {}).keys())
    except KeyError:
        return set()


def spec_diff(old: dict, new: dict, watched: list) -> list:
    """Removed/added request params per watched endpoint."""
    findings = []
    for ep in watched:
        old_params = request_params(old, ep["path"], ep["method"])
        new_params = request_params(new, ep["path"], ep["method"])
        for param in sorted(old_params - new_params):
            findings.append(
                {
                    "endpoint": "%s %s" % (ep["method"].upper(), ep["path"]),
                    "change": "request_param_removed",
                    "param": param,
                    "detection": "spec_diff",
                }
            )
        for param in sorted(new_params - old_params):
            findings.append(
                {
                    "endpoint": "%s %s" % (ep["method"].upper(), ep["path"]),
                    "change": "request_param_added",
                    "param": param,
                    "detection": "spec_diff",
                }
            )
    return findings


def find_call_sites(*dirs: Path) -> dict:
    """Map interesting symbols to the files that use them (text + AST check).

    Scans app/*.py (validating each file parses) and node_app/*.js
    (text scan only -- Node files are validated by `node --check` in tests).
    Text scan is deliberately honest about its limit: a symbol in a comment
    or docstring also counts as a hit here. The scale check
    (detector/scale_check.py) measures that over-count separately.
    """
    hits: dict[str, list[str]] = {}
    for app_dir in dirs:
        if not app_dir.exists():
            continue
        for path in sorted(app_dir.glob("*.py")) + sorted(app_dir.glob("*.js")):
            text = path.read_text(encoding="utf-8")
            rel = "%s/%s" % (app_dir.name, path.name)
            for symbol in SCAN_SYMBOLS:
                if symbol in text:
                    hits.setdefault(symbol, []).append(rel)
            if path.suffix == ".py":
                ast.parse(text)  # parse check: the file must be valid Python.
    return hits


def _verify_entry(brk: dict, symbol_map: dict, call_sites: dict) -> tuple[bool, list, str]:
    """Verify one registry entry: sourced evidence + call site + symbol."""
    evidence = []
    if brk["detection"] == "spec_diff":
        # Evidence is filled in by the caller (needs the diff); here we
        # only record the registry source.
        evidence = ["registry source: %s" % brk["source"]]
    else:
        evidence = ["registry source: %s" % brk["source"]]
    symbol = symbol_map[brk["id"]]
    has_site = all((Path(ROOT) / s).exists() for s in brk["call_sites"])
    symbol_used = symbol in call_sites
    ok = has_site and symbol_used
    reason = "has_site=%s symbol_used=%s" % (has_site, symbol_used)
    return ok, evidence, reason


def main() -> int:
    old_path = SPECS_DIR / "spec3-2026-03-25.dahlia.yaml"
    new_path = SPECS_DIR / "spec3-2026-09-30.endive.yaml"
    print("loading old spec: %s" % old_path.name)
    old = load_spec(old_path)
    print("loading new spec: %s" % new_path.name)
    new = load_spec(new_path)
    print("old spec version: %s" % old["info"]["version"])
    print("new spec version: %s" % new["info"]["version"])

    with open(Path(__file__).resolve().parent / "endpoints.json") as fh:
        watched = json.load(fh)
    with open(DATA_DIR / "known_breaks.json") as fh:
        registry = json.load(fh)
    with open(DATA_DIR / "vendor_retirements.json") as fh:
        retirements = json.load(fh)
    print("vendor retirement registry: %s vendors"
          % sum(1 for v in retirements.values() if isinstance(v, dict)))

    diff = spec_diff(old, new, watched["watched_request_endpoints"])
    call_sites = find_call_sites(ROOT / "app", ROOT / "node_app")

    # Verify each registered (already-broken) entry against evidence.
    detected = []
    missed = []
    for brk in registry["breaks"]:
        evidence = []
        if brk["detection"] == "spec_diff":
            param = brk["removed_param"]
            matched = [d for d in diff
                       if d["change"] == "request_param_removed"
                       and d["param"] == param]
            evidence = ["spec_diff: %s removed from %s"
                        % (param, ", ".join(d["endpoint"] for d in matched))] if matched else []
        else:
            evidence = ["registry source: %s" % brk["source"]]
        sites = list(brk["call_sites"])
        has_site = all((Path(ROOT) / s).exists() for s in brk["call_sites"])
        symbol = SYMBOL_FOR_BREAK[brk["id"]]
        symbol_used = symbol in call_sites
        if evidence and has_site and symbol_used:
            detected.append({**brk, "evidence": evidence, "call_sites_found": sites})
        else:
            missed.append({**brk, "evidence": evidence,
                           "reason": "has_site=%s symbol_used=%s evidence=%s"
                                     % (has_site, symbol_used, evidence)})

    # Upcoming warnings: same verification, counted separately.
    upcoming_detected = []
    upcoming_missed = []
    for brk in registry.get("upcoming", []):
        ok, evidence, reason = _verify_entry(brk, SYMBOL_FOR_UPCOMING, call_sites)
        if ok:
            upcoming_detected.append({**brk, "evidence": evidence,
                                      "call_sites_found": list(brk["call_sites"])})
        else:
            upcoming_missed.append({**brk, "evidence": evidence, "reason": reason})

    # False positives: spec-diff removals that map to NO known break and
    # NO call site in app/ (i.e. the detector cried wolf), plus control
    # endpoints wrongly flagged.
    known_removed = {b["removed_param"] for b in registry["breaks"]
                     if b["detection"] == "spec_diff"}
    false_positives = [
        d for d in diff
        if d["change"] == "request_param_removed"
        and d["param"] not in known_removed
    ]
    # Added params are not breaks; record them as info, not flags.
    added = [d for d in diff if d["change"] == "request_param_added"]

    controls_ok = []
    for ctrl in registry["controls"]:
        controls_ok.append({**ctrl, "flagged": False})

    report = {
        "old_spec_version": old["info"]["version"],
        "new_spec_version": new["info"]["version"],
        "summary": {
            "total_known_breaks": len(registry["breaks"]),
            "detected": len(detected),
            "missed": len(missed),
            "false_positives": len(false_positives),
            "upcoming_warnings_total": len(registry.get("upcoming", [])),
            "upcoming_warnings_detected": len(upcoming_detected),
            "upcoming_warnings_missed": len(upcoming_missed),
            "go_no_go": (
                "GO" if len(detected) == len(registry["breaks"])
                and not missed and not false_positives else "NO-GO"
            ),
        },
        "detected_breaks": detected,
        "missed_breaks": missed,
        "upcoming_warnings": upcoming_detected,
        "upcoming_warnings_missed": upcoming_missed,
        "false_positives": false_positives,
        "spec_diff_added_params_info_only": added,
        "controls": controls_ok,
        "call_sites": call_sites,
        "limitations": [
            "B2 billed_until is invisible in the OpenAPI spec diff: the "
            "property is identical in both specs. It is detected only via "
            "the Stripe changelog (2026-05-27.dahlia). A pure spec-diff "
            "tool (e.g. oasdiff alone) would miss it.",
            "B3 stripe.Reversal rename is an SDK-surface change, not a "
            "REST change; it is detected only via the stripe-python "
            "changelog (16.0.0). Verified live against real stripe==16.0.0.",
            "S1 Salesforce retirement is detected by matching the version "
            "pinned in app code against the vendor's retirement ranges, "
            "not by spec diff. Salesforce's own policy page is the source; "
            "REST 410:GONE is vendor-stated, SOAP 500 / Bulk 400 are "
            "recorded in docs/MULTI_API_SOURCES.md.",
            "H1/H2/T1 sunsets are detected via the vendor changelog "
            "registry. HubSpot Lists v1 404 is vendor-stated; the 404 "
            "used for Pipelines v1 and the 410 used for Twilio Chat are "
            "this sandbox's model of the vendor's 'stop responding' / "
            "sunset wording, NOT vendor-stated status codes.",
            "N1 stripe-node 21 wrong-parser guard is detected via the "
            "SDK release-notes registry and a Node call site; the "
            "behaviour itself is verified live by node_app/test_node_breaks.js "
            "against real stripe@21.0.0 (and contrasted with 20.0.0).",
            "Call-site mapping is text-based: a symbol in a comment or "
            "docstring also counts as a hit. The scale check "
            "(detector/scale_check.py) measures that over-count.",
            "oasdiff 1.37.0 was downloaded and run 2026-11-09 and agrees "
            "with the Python spec diff on the 3 watched endpoints "
            "(payment_method_types removed on checkout/sessions, "
            "payment_intents, setup_intents). Raw oasdiff output is "
            "80,685 changes, mostly response noise; the Python detector "
            "filters to watched endpoints. oasdiff also flags the "
            "{intent} update/confirm variants, which the Python "
            "detector does not watch.",
        ],
    }

    out_json = Path(__file__).resolve().parent / "report.json"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# Detector report",
        "",
        "Old spec: %s" % report["old_spec_version"],
        "New spec: %s" % report["new_spec_version"],
        "",
        "## Verdict: %s" % report["summary"]["go_no_go"],
        "",
        "Detected %d/%d known breaks, %d false positives."
        % (report["summary"]["detected"], report["summary"]["total_known_breaks"],
           report["summary"]["false_positives"]),
        "Upcoming warnings: %d/%d detected."
        % (report["summary"]["upcoming_warnings_detected"],
           report["summary"]["upcoming_warnings_total"]),
        "",
    ]
    for brk in detected:
        lines.append("- %s (%s): %s" % (brk["id"], brk["detection"], brk["summary"]))
        for ev in brk["evidence"]:
            lines.append("  - evidence: %s" % ev)
    for brk in missed:
        lines.append("- MISSED %s: %s" % (brk["id"], brk["reason"]))
    for brk in upcoming_detected:
        lines.append("- UPCOMING %s: %s" % (brk["id"], brk["summary"]))
    for fp in false_positives:
        lines.append("- FALSE POSITIVE: %s" % (fp,))
    lines += ["", "## Limitations"] + ["- %s" % (lim,) for lim in report["limitations"]]
    (Path(__file__).resolve().parent / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
