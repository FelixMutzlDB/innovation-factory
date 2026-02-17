import os
from functools import cached_property
from urllib.parse import quote

from databricks.sdk import WorkspaceClient
from sqlalchemy import Engine, Enum as SAEnum, create_engine, event
from sqlalchemy.pool import NullPool, StaticPool
from sqlmodel import SQLModel, Session, text

from .config import AppConfig
from .logger import logger


class Runtime:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    @cached_property
    def _dev_db_port(self) -> int | None:
        """Check for APX_DEV_DB_PORT environment variable for local development."""
        port = os.environ.get("APX_DEV_DB_PORT")
        return int(port) if port else None

    @cached_property
    def _database_url(self) -> str | None:
        """Check for DATABASE_URL environment variable for direct database connection."""
        return os.environ.get("DATABASE_URL")

    @cached_property
    def ws(self) -> WorkspaceClient:
        # note - this workspace client is usually an SP-based client
        # in development it usually uses the DATABRICKS_CONFIG_PROFILE
        return WorkspaceClient()

    @cached_property
    def engine_url(self) -> str:
        # Priority 1: Direct DATABASE_URL override (e.g. local dev with Lakebase Autoscaling)
        if self._database_url:
            url = self._database_url
            # Ensure we use psycopg driver
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+psycopg://", 1)
            logger.info("Using direct DATABASE_URL connection")
            return url

        # Priority 2: Lakebase Autoscaling via PGHOST/PGUSER/PGDATABASE env vars
        if self.config.db.host:
            user = self.config.db.user
            if not user:
                # Fall back to current user if PGUSER is not set
                user = self.ws.current_user.me().user_name
            # URL-encode the username (e.g. email addresses contain @)
            encoded_user = quote(user, safe="")  # type: ignore[no-matching-overload]
            host = self.config.db.host
            port = self.config.db.port
            database = self.config.db.database_name
            sslmode = self.config.db.sslmode
            logger.info(f"Using Lakebase Autoscaling at {host} as {user}")
            return f"postgresql+psycopg://{encoded_user}:@{host}:{port}/{database}?sslmode={sslmode}"

        # Priority 3: Local PGlite dev database (APX_DEV_DB_PORT)
        if self._dev_db_port:
            logger.info(f"Using local PGlite dev database at localhost:{self._dev_db_port}")
            username = "postgres"
            password = os.environ.get("APX_DEV_DB_PWD")
            if password is None:
                raise ValueError(
                    "APX server didn't provide a password, please check the dev server logs"
                )
            return f"postgresql+psycopg://{username}:{password}@localhost:{self._dev_db_port}/postgres?sslmode=disable"

        raise ValueError(
            "No database connection configured. "
            "Set DATABASE_URL or PGHOST env vars, or run with 'apx dev start'."
        )

    def _before_connect(self, dialect, conn_rec, cargs, cparams):
        """Inject fresh Lakebase credential as database password before each connection.

        Lakebase Autoscaling uses OAuth tokens that expire after one hour.
        This callback calls ws.postgres.generate_database_credential() to get
        a fresh token for every new connection, matching the recommended pattern
        from the Lakebase Autoscaling documentation.
        """
        endpoint_name = self.config.db.endpoint_name
        if not endpoint_name:
            raise ValueError(
                "ENDPOINT_NAME must be set for Lakebase Autoscaling credential rotation. "
                "Get it from the Lakebase Connect modal or: databricks postgres list-endpoints"
            )
        credential = self.ws.postgres.generate_database_credential(endpoint=endpoint_name)
        cparams["password"] = credential.token

    @cached_property
    def _is_local_dev(self) -> bool:
        """True only when using PGlite (no DATABASE_URL or PGHOST override)."""
        return (
            self._dev_db_port is not None
            and self._database_url is None
            and not self.config.db.host
        )

    @cached_property
    def _needs_databricks_auth(self) -> bool:
        """Whether we need Databricks SDK token-based auth for the DB connection."""
        return not self._is_local_dev

    @cached_property
    def engine(self) -> Engine:
        # SQLite: for testing (DATABASE_URL=sqlite://)
        if self.engine_url.startswith("sqlite"):
            engine = create_engine(
                self.engine_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )

            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

            return engine

        # In PGlite dev mode: no SSL, no password callback, single connection (PGlite limit)
        # Otherwise (Lakebase Autoscaling): require SSL and use Databricks OAuth token callback
        if self._is_local_dev:
            engine = create_engine(
                self.engine_url,
                poolclass=NullPool,
            )
        else:
            engine = create_engine(
                self.engine_url,
                pool_recycle=45 * 60,
                connect_args={"sslmode": "require"},
                pool_size=4,
            )
            event.listens_for(engine, "do_connect")(self._before_connect)
        return engine

    def get_session(self) -> Session:
        return Session(self.engine)

    def validate_db(self) -> None:
        if self._is_local_dev:
            logger.info(
                f"Validating local dev database connection at localhost:{self._dev_db_port}"
            )
        elif self._database_url:
            logger.info("Validating direct DATABASE_URL connection")
        else:
            logger.info(
                f"Validating Lakebase Autoscaling connection to {self.config.db.host}"
            )

        # check if a connection to the database can be established
        try:
            with self.get_session() as session:
                session.connection().execute(text("SELECT 1"))
                session.close()
        except Exception:
            raise ConnectionError("Failed to connect to the database")

        logger.info("Database connection validated successfully")

    def initialize_models(self) -> None:
        logger.info("Initializing database models")
        # Disable native PostgreSQL ENUMs - Lakebase doesn't allow CREATE TYPE
        for table in SQLModel.metadata.tables.values():
            for column in table.columns:
                if isinstance(column.type, SAEnum):
                    column.type.native_enum = False
        try:
            SQLModel.metadata.create_all(self.engine)
        except Exception as e:
            # With multiple uvicorn workers, another worker may have already created
            # the tables. If so, just log a warning and continue.
            logger.warning(f"create_all raised (likely concurrent worker race): {e}")
        logger.info("Database models initialized successfully")
