"""Vercel Python serverless entrypoint — exposes the GraphThrift FastAPI app.

Vercel's Python runtime serves the module-level ASGI ``app``. The GraphThrift
source is bundled via ``includeFiles`` in vercel.json and added to sys.path here.
On serverless the DB lives in /tmp (the only writable path) and the default
backend is the deterministic simulator, so the live demo runs with no keys.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("GRAPHTHRIFT_BACKEND", "fake")
os.environ.setdefault("GRAPHTHRIFT_DATABASE_URL", "sqlite:////tmp/graphthrift.sqlite3")
os.environ.setdefault("GRAPHTHRIFT_LOG_JSON", "true")

from graphthrift.api.app import app  # noqa: E402

__all__ = ["app"]
