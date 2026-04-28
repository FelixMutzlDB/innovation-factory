"""Integration test for the AECO Hub Multi-Agent Supervisor.

Hits the supervisor's serving endpoint with three questions — one per
sub-agent — and verifies the supervisor returns a non-empty response.
This exercises both the MAS routing logic (the LLM picks the right
sub-agent) and the underlying Genie / KA endpoints.

Requires DATABRICKS_CONFIG_PROFILE plus AECO_MAS_ENDPOINT_NAME
populated by ``scripts/bootstrap.py``.

Run with: pytest tests/integration/test_aeco_hub_mas.py -m integration
"""
from __future__ import annotations

import json
import os

import pytest

pytestmark = pytest.mark.integration


REQUIRES_MAS = pytest.mark.skipif(
    not os.getenv("AECO_MAS_ENDPOINT_NAME"),
    reason="AECO_MAS_ENDPOINT_NAME not set (run scripts/bootstrap.py)",
)


def _ask_mas(ws, endpoint_name: str, question: str) -> str:
    """Send a single-turn question to the MAS endpoint and return text."""
    from innovation_factory.backend.services.databricks_agents import (
        extract_agent_text,
        query_agent_endpoint,
    )

    result = query_agent_endpoint(
        ws,
        endpoint_name,
        [{"role": "user", "content": question}],
    )
    return extract_agent_text(result)


@REQUIRES_MAS
class TestAecoMasRouting:
    """Each test sends a question that should route to a different sub-agent.

    The MAS doesn't echo which sub-agent it picked in a structured way, but
    a non-empty response with topic-relevant keywords is strong evidence
    routing landed correctly.
    """

    @pytest.fixture(scope="class")
    def ws(self):
        from databricks.sdk import WorkspaceClient
        return WorkspaceClient()

    @pytest.fixture(scope="class")
    def endpoint(self):
        return os.environ["AECO_MAS_ENDPOINT_NAME"]

    def test_project_analytics_route(self, ws, endpoint):
        """Portfolio question should route to project_analytics Genie."""
        text = _ask_mas(ws, endpoint, "Which projects are behind schedule?")
        assert text, "MAS returned empty response"
        # Heuristic check — the response should mention something
        # project-relevant. Genie typically references the table or the
        # project names from the seed data.
        assert any(
            kw in text.lower()
            for kw in ["project", "schedule", "behind", "delayed",
                       "qsp", "thc", "kes", "log", "ams"]
        ), f"Response did not look project-related: {text[:300]}"

    def test_operations_intelligence_route(self, ws, endpoint):
        """IoT / energy question should route to operations_intelligence."""
        text = _ask_mas(
            ws, endpoint,
            "What is the total kWh consumed across all buildings in the last 30 days?",
        )
        assert text, "MAS returned empty response"
        assert any(
            kw in text.lower()
            for kw in ["kwh", "energy", "consumption", "building", "meter"]
        ), f"Response did not look operations-related: {text[:300]}"

    def test_standards_compliance_route(self, ws, endpoint):
        """Standards question should route to standards_compliance KA."""
        text = _ask_mas(
            ws, endpoint,
            "What does COBie require for the operate phase hand-off?",
        )
        assert text, "MAS returned empty response"
        assert any(
            kw in text.lower()
            for kw in ["cobie", "hand-off", "handover", "component",
                       "space", "type", "facility"]
        ), f"Response did not look compliance-related: {text[:300]}"
