from importlib import resources
from pathlib import Path
from typing import ClassVar

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .._metadata import app_name, app_slug

# project root is the parent of the src folder
project_root = Path(__file__).parent.parent.parent.parent
env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(dotenv_path=env_file)


class DatabaseConfig(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        extra="ignore",
    )
    host: str | None = Field(
        description="The hostname of the Lakebase Autoscaling endpoint",
        default=None,
        validation_alias="PGHOST",
    )
    port: int = Field(
        description="The port of the database", default=5432, validation_alias="PGPORT"
    )
    database_name: str = Field(
        description="The name of the database",
        default="databricks_postgres",
        validation_alias="PGDATABASE",
    )
    user: str | None = Field(
        description="The database user (email for local dev, service principal client ID for production)",
        default=None,
        validation_alias="PGUSER",
    )
    sslmode: str = Field(
        description="SSL mode for the database connection",
        default="require",
        validation_alias="PGSSLMODE",
    )
    endpoint_name: str | None = Field(
        description="Lakebase Autoscaling endpoint name for credential generation "
        "(format: projects/<id>/branches/<id>/endpoints/<id>)",
        default=None,
        validation_alias="ENDPOINT_NAME",
    )


class AppConfig(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=env_file,
        env_prefix=f"{app_slug.upper()}_",
        extra="ignore",
        env_nested_delimiter="__",
    )
    app_name: str = Field(default=app_name)
    db: DatabaseConfig = DatabaseConfig()  # type: ignore

    @property
    def static_assets_path(self) -> Path:
        return Path(str(resources.files(app_slug))).joinpath("__dist__")

    def __hash__(self) -> int:
        return hash(self.app_name)
