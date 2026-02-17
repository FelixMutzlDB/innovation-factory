"""Unit tests for Databricks agent utilities (no live connection required)."""
import pytest

from innovation_factory.backend.services.databricks_agents import extract_agent_text


class TestAgentTextExtraction:
    """Test the shared agent text extraction utility."""

    def test_extract_simple_text(self):
        response = {
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Hello!"}],
                }
            ]
        }
        assert extract_agent_text(response) == "Hello!"

    def test_extract_from_choices(self):
        response = {"choices": [{"message": {"content": "World!"}}]}
        assert extract_agent_text(response) == "World!"

    def test_extract_filters_tool_calls(self):
        response = {
            "output": [
                {"type": "function_call", "name": "tool", "arguments": "{}"},
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Real answer"}],
                },
            ]
        }
        result = extract_agent_text(response)
        assert "Real answer" in result
        assert "function_call" not in result
