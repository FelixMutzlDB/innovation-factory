"""Shared utilities for Databricks Agent Bricks (MAS/KA) serving endpoints."""

import re

from databricks.sdk import WorkspaceClient

from ..logger import logger


# Supervisor MAS endpoints emit the routing decision as XML-ish blocks
# (``<agent_query>...</agent_query>`` or ``<execute_tool>...</execute_tool>``)
# in the first response turn before they would dispatch to a sub-agent.
# Today the platform doesn't auto-orchestrate the second turn over our
# Responses-API integration — see TODO in chat_service — so the dispatch
# block leaks into the user-visible text. Strip it for now and keep only
# any natural-language preamble. Long-term: detect the block, call the
# named sub-agent, and stitch the answer back in.
_ROUTING_BLOCK_RE = re.compile(
    r"<(agent_query|execute_tool)\b[^>]*>.*?</\1>",
    re.DOTALL,
)


def _strip_routing_blocks(text: str) -> str:
    cleaned = _ROUTING_BLOCK_RE.sub("", text).strip()
    return cleaned


def query_agent_endpoint(
    ws: WorkspaceClient,
    endpoint_name: str,
    messages: list[dict],
) -> dict:
    """Call a Databricks Agent Bricks serving endpoint using the input/output format.

    Agent Bricks endpoints require the 'input' field (not 'messages').
    Uses ws.api_client.do() for proper OAuth handling.

    Args:
        ws: WorkspaceClient instance
        endpoint_name: Name of the serving endpoint
        messages: List of message dicts with 'role' and 'content' keys

    Returns:
        Raw response dict from the endpoint
    """
    payload = [{"role": m["role"], "content": m["content"]} for m in messages]
    logger.info(f"Querying serving endpoint '{endpoint_name}' with {len(payload)} messages")
    result = ws.api_client.do(
        "POST",
        f"/serving-endpoints/{endpoint_name}/invocations",
        body={"input": payload},
    )
    logger.info(f"Received response from '{endpoint_name}'")
    return result  # type: ignore[invalid-return-type]


def extract_agent_text(response: dict | list | str) -> str:
    """Extract plain text from an Agent Bricks response.

    Handles the nested output format and filters out internal
    tool-call metadata, returning only human-readable text.

    Agent Bricks endpoints return varied structures:
    - {"output": [{"type":"message","content":[{"type":"output_text","text":"..."}]}]}
    - {"output": "plain string"}
    - {"choices": [{"message": {"content": "..."}}]}

    Internal items (function_call, function_call_output) are skipped.

    Args:
        response: Raw response dict from query_agent_endpoint

    Returns:
        Extracted text string
    """
    if isinstance(response, str):
        return _strip_routing_blocks(response)

    if isinstance(response, dict):
        output = response.get("output")
        if output is not None:
            return extract_agent_text(output)
        choices = response.get("choices")
        if choices and isinstance(choices, list):
            msg = choices[0].get("message", {})
            return msg.get("content", "")
        content = response.get("content")
        if isinstance(content, list):
            texts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "output_text":
                    texts.append(_strip_routing_blocks(block.get("text", "")))
            return "\n".join(t for t in texts if t) if texts else str(response)
        if isinstance(content, str):
            return _strip_routing_blocks(content)
        text = response.get("text")
        if isinstance(text, str):
            return _strip_routing_blocks(text)
        return str(response)

    if isinstance(response, list):
        texts = []
        for item in response:
            if isinstance(item, dict):
                item_type = item.get("type", "")
                # Skip internal agent-to-agent messages
                if item_type in ("function_call", "function_call_output"):
                    continue
                if item_type == "message" and item.get("role") == "assistant":
                    texts.append(extract_agent_text(item))
                elif item_type == "output_text":
                    texts.append(item.get("text", ""))
                elif item_type == "message":
                    # Non-assistant messages (e.g. tool output) — skip
                    continue
                else:
                    texts.append(extract_agent_text(item))
            elif isinstance(item, str):
                texts.append(item)
        return "\n".join(texts) if texts else str(response)

    return str(response)
