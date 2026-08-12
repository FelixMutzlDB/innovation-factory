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
# Use shared in-memory SQLite so app and fixtures use the same DB.
# Plain `sqlite:///:memory:` is enough because the engine fixture is
# session-scoped and StaticPool reuses one connection — the previous
# `sqlite:///file:test_shared?mode=memory&cache=shared` was treated by
# SQLite as a literal filename (no `uri=true`), creating a real
# `file:test_shared` file in the repo root that persisted DB state
# across runs (TODO B2 backlog).
os.environ["DATABASE_URL"] = "sqlite:///:memory:"


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
    import innovation_factory.backend.projects.aeco_hub.models  # noqa: F401
    import innovation_factory.backend.projects.yard_pro.models  # noqa: F401
    import innovation_factory.backend.projects.hb_product_center.models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(autouse=True)
def _clean_tables(engine):
    """Delete all rows after each test so state never leaks between tests.

    The `engine` fixture is session-scoped with a single StaticPool
    connection, so anything the app or a seed helper `commit()`s persists
    for the whole run — the `session` fixture's trailing rollback() is a
    no-op after an explicit commit. Without this teardown, seeded rows
    accumulate and leak across tests, which is order-dependent flakiness
    waiting to happen the moment a test asserts an absolute count or an
    empty-state total. Deleting in reverse dependency order respects the
    foreign-key PRAGMA.
    """
    yield
    with engine.begin() as conn:
        for table in reversed(SQLModel.metadata.sorted_tables):
            conn.execute(table.delete())


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
