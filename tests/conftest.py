import asyncio
import pytest
import os
import tempfile
from pathlib import Path

# Use mock LLM for all tests
os.environ["APP_ENV"] = "test"
os.environ.setdefault("MANUSCLAW_WORKSPACE", tempfile.mkdtemp())


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def tmp_workspace(tmp_path):
    os.environ["MANUSCLAW_WORKSPACE"] = str(tmp_path)
    yield tmp_path
    os.environ.pop("MANUSCLAW_WORKSPACE", None)


@pytest.fixture
def tmp_db(tmp_path):
    from app.db.session import SessionDB
    db = SessionDB(db_path=tmp_path / "test.db")
    yield db
    db.close()
