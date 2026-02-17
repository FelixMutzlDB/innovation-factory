"""Shared test fixtures for Innovation Factory."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session

# Force local dev mode for testing
os.environ.pop("PGHOST", None)
os.environ.pop("ENDPOINT_NAME", None)
# Use shared in-memory SQLite so app and fixtures use the same DB
os.environ["DATABASE_URL"] = "sqlite:///file:test_shared?mode=memory&cache=shared"


@pytest.fixture(scope="session")
def engine():
    """Create an in-memory SQLite engine for testing."""
    url = os.environ["DATABASE_URL"]
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # SQLModel requires this for SQLite compatibility
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Import all models so they're registered with SQLModel.metadata
    import innovation_factory.backend.models  # noqa: F401
    import innovation_factory.backend.projects.vi_home_one.models  # noqa: F401
    import innovation_factory.backend.projects.bsh_home_connect.models  # noqa: F401
    import innovation_factory.backend.projects.adtech_intelligence.models  # noqa: F401
    import innovation_factory.backend.projects.mol_asm_cockpit.models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create a fresh database session for each test."""
    with Session(engine) as session:
        yield session
        session.rollback()


@pytest.fixture
def client(engine):
    """Create a FastAPI test client with in-memory DB."""
    from innovation_factory.backend.app import app
    from innovation_factory.backend.dependencies import get_session

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
