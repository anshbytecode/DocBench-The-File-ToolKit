"""
Vercel Python entry point.
Vercel's Python runtime auto-detects a WSGI-compatible `app` object.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app  # noqa: E402

# Vercel looks for a module-level `app` (WSGI) in this file.
