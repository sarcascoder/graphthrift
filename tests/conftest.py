"""Test fixtures — isolate the DB to a temp file before any graphthrift import."""
import os
import tempfile

os.environ.setdefault("GRAPHTHRIFT_BACKEND", "fake")
_tmp = tempfile.mkdtemp(prefix="graphthrift-test-")
os.environ["GRAPHTHRIFT_DATABASE_URL"] = f"sqlite:///{_tmp}/test.sqlite3"

import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _init_db():
    from graphthrift.store import init_db

    init_db()
    yield
