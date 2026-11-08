"""Shared pytest fixtures."""
import os
import sys
from pathlib import Path

# stripe 16.x prints an AI-agent notice on import unless suppressed.
os.environ.setdefault("STRIPE_SUPPRESS_NOTICES", "true")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OLD_API_VERSION = "2026-03-25.dahlia"
NEW_API_VERSION = "2026-09-30.endive"
