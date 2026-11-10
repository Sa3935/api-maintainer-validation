"""Deterministic, opt-in fixes for the two non-mechanical Stripe breaks.

These are NOT run by the default codemod (fixer/codemod.py, B1 only),
and they are NOT applied to app/ by any script in this repo. They operate
on a source string (or, via --apply, on an explicit file you name) and
are verified by tests on temp copies. That separation is deliberate:

- B2 billed_until is SEMANTIC. The fix -- request the field via
  ``expand=["billed_until"]`` -- is a decision about what the caller
  needs, not a mechanical deletion. So fix_billed_until() REFUSES to run
  unless confirm=True is passed explicitly (the --confirm CLI flag).
  It also refuses unless the file contains exactly ONE un-expanded
  subscription_items_retrieve() call, so it can never silently rewrite
  a call it does not understand.
- B3 stripe.Reversal -> stripe.TransferReversal is a mechanical SDK
  rename, but it is a one-way upgrade: after the fix the code works on
  stripe-python 16 and BREAKS on 15 (TransferReversal does not exist
  there). The function only renames the attribute ``.Reversal`` (never
  a class definition or a bare word), and the tests prove both sides.

Usage:
    python -m fixer.semantic_fixes --file app/refunds.py --fix reversal --check
    python -m fixer.semantic_fixes --file app/billing.py --fix billed_until --confirm --apply
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_RETRIEVE = re.compile(
    r"\.subscription_items_retrieve\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)"
)


def fix_billed_until(source: str, *, confirm: bool = False) -> str:
    """Add expand=["billed_until"] to the single retrieve() call.

    Requires confirm=True (semantic decision -- see module docstring).
    Raises ValueError unless there is exactly one un-expanded call.
    """
    if not confirm:
        raise ValueError(
            "fix_billed_until requires confirm=True: requesting billed_until "
            "via expand is a semantic decision about what the caller needs, "
            "not a mechanical deletion. Pass confirm=True (or --confirm) "
            "only after a human has approved it."
        )
    matches = list(_RETRIEVE.finditer(source))
    if len(matches) != 1:
        raise ValueError(
            "expected exactly 1 un-expanded subscription_items_retrieve() "
            "call, found %d -- refusing to guess" % len(matches)
        )
    (match,) = matches
    arg = match.group(1)
    new_source = (
        source[: match.start()]
        + '.subscription_items_retrieve(%s, expand=["billed_until"])' % arg
        + source[match.end():]
    )
    ast.parse(new_source)
    assert 'expand=["billed_until"]' in new_source
    return new_source


def fix_reversal_rename(source: str) -> str:
    """Rename attribute access ``.Reversal`` -> ``.TransferReversal``.

    AST-based: only real Attribute nodes named ``Reversal`` are renamed
    (``sdk.Reversal``). The word in docstrings, comments, or class names
    is untouched -- a regex would have renamed those too.
    """
    tree = ast.parse(source)
    spans = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "Reversal":
            # The attribute name is the last len("Reversal") chars of the node.
            spans.append((node.lineno, node.end_col_offset - len("Reversal"),
                          node.end_col_offset))
    if not spans:
        raise ValueError("no .Reversal attribute access found -- nothing to fix")
    lines = source.splitlines(keepends=True)
    for lineno, start, end in sorted(spans, reverse=True):
        line = lines[lineno - 1]
        assert line[start:end] == "Reversal", (line, start, end)
        lines[lineno - 1] = line[:start] + "TransferReversal" + line[end:]
    new_source = "".join(lines)
    ast.parse(new_source)
    return new_source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, help="file to fix, e.g. app/refunds.py")
    parser.add_argument("--fix", required=True, choices=["billed_until", "reversal"])
    parser.add_argument("--confirm", action="store_true",
                        help="required for billed_until (semantic fix)")
    parser.add_argument("--check", action="store_true", help="dry run")
    parser.add_argument("--apply", action="store_true", help="write the file in place")
    args = parser.parse_args()
    if not (args.check or args.apply):
        parser.error("pass --check or --apply")
    path = ROOT / args.file
    source = path.read_text(encoding="utf-8")
    if args.fix == "billed_until":
        new_source = fix_billed_until(source, confirm=args.confirm)
    else:
        new_source = fix_reversal_rename(source)
    print("fix %s: %d line(s) changed in %s" % (
        args.fix, sum(1 for a, b in zip(source.splitlines(), new_source.splitlines()) if a != b),
        path))
    if args.apply:
        path.write_text(new_source, encoding="utf-8")
        print("applied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
