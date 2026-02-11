from typing import Annotated, Generator
import os

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.iam import User as DatabricksUser, Name, ComplexValue
from fastapi import Depends, Header, Request
from sqlmodel import Session
from dataclasses import dataclass

from .config import AppConfig
from .runtime import Runtime


def get_config(request: Request) -> AppConfig:
    if not hasattr(request.app.state, "config"):
        raise RuntimeError(
            "AppConfig not initialized. "
            "Ensure app.state.config is set during application lifespan startup."
        )
    return request.app.state.config


ConfigDep = Annotated[AppConfig, Depends(get_config)]


def get_runtime(request: Request) -> Runtime:
    if not hasattr(request.app.state, "runtime"):
        raise RuntimeError(
            "Runtime not initialized. "
            "Ensure app.state.runtime is set during application lifespan startup."
        )
    return request.app.state.runtime


RuntimeDep = Annotated[Runtime, Depends(get_runtime)]


def is_local_dev() -> bool:
    """Check if running in local development mode."""
    return not bool(os.getenv("DATABRICKS_RUNTIME_VERSION"))


@dataclass
class MockDatabricksUser:
    """Mock Databricks user for local development."""
    id: str = "local-dev-user"
    user_name: str = "local@developer.com"
    display_name: str = "Local Developer"
    active: bool = True

    def __post_init__(self):
        self.emails = [ComplexValue(value="local@developer.com", primary=True, type="work")]
        self.name = Name(given_name="Local", family_name="Developer")

    def as_dict(self):
        return {
            "id": self.id,
            "user_name": self.user_name,
            "display_name": self.display_name,
            "active": self.active,
            "emails": [{"value": "local@developer.com", "primary": True}],
            "name": {"given_name": "Local", "family_name": "Developer"},
        }


class MockWorkspaceClient:
    """Mock WorkspaceClient for local development."""
    class MockCurrentUser:
        def me(self):
            return MockDatabricksUser()

    def __init__(self):
        self.current_user = self.MockCurrentUser()


def get_obo_ws(
    token: Annotated[str | None, Header(alias="X-Forwarded-Access-Token")] = None,
) -> WorkspaceClient:
    """
    Returns a Databricks Workspace client with authentication behalf of user.
    In local development mode, returns a mock client.
    """
    if is_local_dev():
        return MockWorkspaceClient()

    if not token:
        raise ValueError(
            "OBO token is not provided in the header X-Forwarded-Access-Token"
        )

    return WorkspaceClient(
        token=token, auth_type="pat"
    )


def get_session(rt: RuntimeDep) -> Generator[Session, None, None]:
    with rt.get_session() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
