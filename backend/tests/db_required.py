"""Marker for the tests that log in to the seeded application database (tests/test_backend.py).

They used to fail on every machine without that database, which made a red test run mean nothing. Now they are skipped with
a visible reason; set REQUIRE_DB_TESTS=1 (a release check, CI) to run them anyway and fail when the database is down.
"""
import os

import pytest
from sqlalchemy import create_engine, text

from app.core.config import settings


def _database_reachable():
    try:
        args = {} if settings.DATABASE_URL.startswith("sqlite") else {"connect_timeout": 2}
        with create_engine(settings.DATABASE_URL, connect_args=args).connect() as conn:
            conn.execute(text("select 1"))
        return True
    except Exception:
        return False


needs_db = pytest.mark.skipif(
    not os.environ.get("REQUIRE_DB_TESTS") and not _database_reachable(),
    reason="the seeded application database is not reachable (set REQUIRE_DB_TESTS=1 to fail instead)")
