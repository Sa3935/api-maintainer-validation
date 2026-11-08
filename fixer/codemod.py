"""Deterministic codemod: remove ``payment_method_types`` (BREAK 1 only).

Scope (hard rule): this codemod touches ONLY the ``payment_method_types``
keyword argument in ``app/checkout.py``. It MUST NOT touch:
  - app/billing.py (billed_until -- semantic, agent must not touch it)
  - app/refunds.py (stripe.Reversal rename -- out of scope for this step)

How it works: parse the file with ``ast``, locate every Call node whose
keywords include ``payment_method_types``, remove those keywords from
the source text by line/column, re-parse to prove the file is still
valid Python, and assert the forbidden files are byte-identical
afterwards.

Usage:
    python -m fixer.codemod --check     # dry run, print what would change
    python -m fixer.codemod --apply     # apply + write patches/fix-payment-method-types.patch
"""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "app" / "checkout.py"
FORBIDDEN = [ROOT / "app" / "billing.py", ROOT / "app" / "refunds.py"]
PATCH_PATH = ROOT / "patches" / "fix-payment-method-types.patch"
REMOVED_KWARG = "payment_method_types"


def find_removals(source: str) -> list[dict]:
    """Return the (line, col_start, col_end) spans of the kwarg to remove."""
    tree = ast.parse(source)
    removals = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg == REMOVED_KWARG:
                # kw.value spans the value; the keyword spans from kw.col_offset
                # to the end of its value. Include a trailing comma if present.
                removals.append(
                    {"line": kw.lineno, "col": kw.col_offset,
                     "end_line": kw.value.end_lineno,
                     "end_col": kw.value.end_col_offset}
                )
    return removals


def apply_removals(source: str, removals: list[dict]) -> str:
    """Remove the kwarg occurrences from the source (single-line kwargs)."""
    lines = source.splitlines(keepends=True)
    # Process bottom-up so line numbers stay valid.
    for rem in sorted(removals, key=lambda r: (r["line"], r["col"]), reverse=True):
        if rem["line"] != rem["end_line"]:
            raise ValueError("multi-line payment_method_types kwarg not supported: %s" % (rem,))
        idx = rem["line"] - 1
        line = lines[idx]
        # Span from the keyword start to the end of the value, plus one
        # trailing comma / whitespace if present.
        end = rem["end_col"]
        while end < len(line) and line[end] in " \t":
            end += 1
        if end < len(line) and line[end] == ",":
            end += 1
        new_line = line[: rem["col"]] + line[end:]
        # Clean up a double comma left behind (", ,") or trailing whitespace.
        new_line = new_line.replace(", ,", ",").rstrip() + "\n"
        lines[idx] = new_line
    result = "".join(lines)
    ast.parse(result)  # prove it is still valid Python
    if REMOVED_KWARG in result:
        raise ValueError("payment_method_types still present after codemod")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="dry run")
    parser.add_argument("--apply", action="store_true", help="apply + write patch")
    args = parser.parse_args()
    if not (args.check or args.apply):
        parser.error("pass --check or --apply")

    before = {p: p.read_bytes() for p in FORBIDDEN}
    source = TARGET.read_text(encoding="utf-8")
    removals = find_removals(source)
    print("found %d payment_method_types kwarg(s) in %s" % (len(removals), TARGET))
    for rem in removals:
        print("  line %d col %d" % (rem["line"], rem["col"]))
    if args.check:
        return 0

    new_source = apply_removals(source, removals)
    TARGET.write_text(new_source, encoding="utf-8")
    for path, content in before.items():
        if path.read_bytes() != content:
            raise SystemExit("FORBIDDEN FILE CHANGED: %s -- aborting" % path)
    print("forbidden files untouched: %s" % ", ".join(str(p) for p in FORBIDDEN))

    # Write a real patch (git diff of the working tree).
    PATCH_PATH.parent.mkdir(parents=True, exist_ok=True)
    diff = subprocess.run(
        ["git", "diff", "--", "app/checkout.py"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    PATCH_PATH.write_text(diff, encoding="utf-8")
    print("patch written: %s" % PATCH_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
