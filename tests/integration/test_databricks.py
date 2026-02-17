"""Integration tests for Databricks services.

These tests require a live Databricks connection and are skipped in CI.
Run with: pytest tests/integration/ -m integration
"""
import os
import pytest

pytestmark = pytest.mark.integration

REQUIRES_DATABRICKS = pytest.mark.skipif(
    not os.getenv("DATABRICKS_CONFIG_PROFILE") and not os.getenv("DATABRICKS_HOST"),
    reason="No Databricks configuration found",
)


@REQUIRES_DATABRICKS
class TestDatabricksConnection:
    def test_workspace_client(self):
        from databricks.sdk import WorkspaceClient

        ws = WorkspaceClient()
        user = ws.current_user.me()
        assert user.user_name is not None

    def test_lakebase_credential(self):
        endpoint = os.getenv("ENDPOINT_NAME")
        if not endpoint:
            pytest.skip("ENDPOINT_NAME not set")
        assert endpoint is not None
        from databricks.sdk import WorkspaceClient

        ws = WorkspaceClient()
        cred = ws.postgres.generate_database_credential(endpoint=endpoint)
        assert cred.token is not None
        assert len(cred.token) > 10


@REQUIRES_DATABRICKS
class TestServingEndpoints:
    """Test Agent Bricks serving endpoint connectivity."""

    def test_mas_endpoint_reachable(self):
        from innovation_factory.backend.services.databricks_agents import (
            query_agent_endpoint,
        )
        from databricks.sdk import WorkspaceClient

        endpoint = os.getenv("ADTECH_MAS_ENDPOINT_NAME")
        if not endpoint:
            pytest.skip("ADTECH_MAS_ENDPOINT_NAME not set")
        assert endpoint is not None
        ws = WorkspaceClient()
        result = query_agent_endpoint(
            ws, endpoint, [{"role": "user", "content": "Hello, are you available?"}]
        )
        assert result is not None
        assert "output" in result or "choices" in result

    def test_ka_endpoint_reachable(self):
        from innovation_factory.backend.services.databricks_agents import (
            query_agent_endpoint,
        )
        from databricks.sdk import WorkspaceClient

        endpoint = os.getenv("ADTECH_ISSUE_RESOLUTION_KA_ENDPOINT")
        if not endpoint:
            pytest.skip("ADTECH_ISSUE_RESOLUTION_KA_ENDPOINT not set")
        assert endpoint is not None
        ws = WorkspaceClient()
        result = query_agent_endpoint(
            ws,
            endpoint,
            [{"role": "user", "content": "What types of issues can you help with?"}],
        )
        assert result is not None


@REQUIRES_DATABRICKS
class TestIdeaGenerator:
    """Test the idea generator serving endpoint."""

    def test_idea_generator_endpoint(self):
        from databricks.sdk import WorkspaceClient

        endpoint = os.getenv("IDEA_GENERATOR_ENDPOINT")
        if not endpoint:
            pytest.skip("IDEA_GENERATOR_ENDPOINT not set")
        assert endpoint is not None
        ws = WorkspaceClient()
        result = ws.api_client.do(
            "POST",
            f"/serving-endpoints/{endpoint}/invocations",
            body={
                "messages": [{"role": "user", "content": "Generate a brief idea for TestCorp"}],
                "max_tokens": 200,
            },
        )
        assert result is not None
        choices = result.get("choices", [])  # type: ignore[union-attr]
        assert len(choices) > 0
        content = choices[0].get("message", {}).get("content", "")  # type: ignore[union-attr,index]
        assert len(content) > 20


@REQUIRES_DATABRICKS
class TestDashboardEmbed:
    """Test dashboard embedding configuration."""

    def test_adtech_dashboard_url(self):
        workspace_url = os.getenv("ADTECH_WORKSPACE_URL")
        dashboard_id = os.getenv("ADTECH_DASHBOARD_ID")
        if not workspace_url or not dashboard_id:
            pytest.skip("ADTECH dashboard config not set")
        embed_url = f"https://{workspace_url}/embed/dashboardsv3/{dashboard_id}?embed"
        assert workspace_url
        assert dashboard_id
        assert len(dashboard_id) > 10
