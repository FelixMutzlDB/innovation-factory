"""Integration smoke test for AECO Hub Genie spaces.

Hits each of the two AECO Genie spaces with a known sample question and
asserts the result is non-empty. Requires DATABRICKS_CONFIG_PROFILE (or
DATABRICKS_HOST) plus the Genie space IDs to be wired into env vars by
``scripts/bootstrap.py`` (which prints them after a successful run).

Run with: pytest tests/integration/test_aeco_hub_genie.py -m integration
"""
from __future__ import annotations

import json
import os
import time

import pytest

pytestmark = pytest.mark.integration


REQUIRES_GENIE = pytest.mark.skipif(
    not os.getenv("AECO_PROJECT_ANALYTICS_GENIE_SPACE_ID")
    or not os.getenv("AECO_OPERATIONS_INTELLIGENCE_GENIE_SPACE_ID"),
    reason="Genie space IDs not configured (run scripts/bootstrap.py first)",
)


def _ask_genie(ws, space_id: str, question: str, timeout_s: int = 90) -> dict:
    """Start a conversation with a Genie space and poll until the message
    has a final state. Returns the final message dict.
    """
    body = {"content": question}
    start = ws.api_client.do(
        "POST",
        f"/api/2.0/genie/spaces/{space_id}/start-conversation",
        body=body,
    )
    conversation_id = start.get("conversation_id") or start["conversation"]["id"]
    message_id = start.get("message_id") or start["message"]["id"]

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        msg = ws.api_client.do(
            "GET",
            f"/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}",
        )
        status = msg.get("status")
        if status in ("COMPLETED", "FAILED", "CANCELLED"):
            return msg
        time.sleep(2)
    raise TimeoutError(f"Genie did not respond within {timeout_s}s")


@REQUIRES_GENIE
class TestAecoGenieSmoke:
    def test_project_analytics_returns_non_empty(self):
        from databricks.sdk import WorkspaceClient

        ws = WorkspaceClient()
        space_id = os.environ["AECO_PROJECT_ANALYTICS_GENIE_SPACE_ID"]
        msg = _ask_genie(ws, space_id, "How many projects are there?")
        assert msg.get("status") == "COMPLETED", f"Genie status: {msg.get('status')}, content: {msg}"
        # The completed message should have at least one attachment with
        # either text content or a query result.
        attachments = msg.get("attachments", [])
        assert len(attachments) > 0, f"No attachments in response: {json.dumps(msg)[:500]}"

    def test_operations_intelligence_returns_non_empty(self):
        from databricks.sdk import WorkspaceClient

        ws = WorkspaceClient()
        space_id = os.environ["AECO_OPERATIONS_INTELLIGENCE_GENIE_SPACE_ID"]
        msg = _ask_genie(ws, space_id, "What is the total kWh consumed in the last 30 days?")
        assert msg.get("status") == "COMPLETED", f"Genie status: {msg.get('status')}, content: {msg}"
        attachments = msg.get("attachments", [])
        assert len(attachments) > 0, f"No attachments in response: {json.dumps(msg)[:500]}"
