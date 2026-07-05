"""
Netlify Functions entry point (alternative to Vercel).

IMPORTANT: Netlify's Python function support is much more constrained than
Vercel's — smaller deployment package limits, a default 10s execution
timeout, and less official tooling around native-code dependencies like
PyMuPDF/pikepdf. This wrapper is provided for completeness, but Vercel
is the recommended target for this project. See README.md.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app import app  # noqa: E402
import serverless_wsgi  # pip install serverless-wsgi


def handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)
