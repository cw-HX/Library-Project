"""Utility to locate the MongoDB connection URI used by the app.

Priority order:
- environment variable MONGODB_URI
- repository file at the project root named `mongodb_uri.txt` (useful for local dev; keep it out of git)

This helper centralizes the lookup so other modules (e.g. `settings.py`)
can import it to get the effective connection string.
"""
import os
from pathlib import Path


def get_mongodb_uri():
    """Return the MongoDB URI or None if not configured.

    Checks the MONGODB_URI environment variable first. If that's not set,
    it looks for a file named `mongodb_uri.txt` in the project root and
    returns its first non-empty line.
    """
    # 1) environment
    uri = os.environ.get('MONGODB_URI')
    if uri:
        return uri.strip()

    # 2) repository file fallback (project root)
    base = Path(__file__).resolve().parent.parent
    candidate = base / 'mongodb_uri.txt'
    if candidate.exists():
        text = candidate.read_text(encoding='utf-8').strip()
        if text and not text.startswith('#'):
            # return the first non-empty, non-comment line
            for line in text.splitlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    return line
    return None
