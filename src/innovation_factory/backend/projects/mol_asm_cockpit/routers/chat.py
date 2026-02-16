"""Chat / Agent proxy endpoints for the ASM Cockpit.

Proxies user messages to the Multi-Agent Supervisor (MAS) serving endpoint.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from sqlmodel import select

from ....dependencies import SessionDep
from ..models import (
    MacChatSession,
    MacChatMessage,
    MacChatRole,
    MacChatMessageIn,
    MacChatMessageOut,
    MacChatHistoryOut,
)

router = APIRouter(prefix="/chat", tags=["mac-chat"])

# Agent Bricks Multi-Agent Supervisor endpoint
MAS_ENDPOINT_NAME: Optional[str] = "mas-25c4ab04-endpoint"


@router.post("/send", response_model=MacChatMessageOut, operation_id="mac_sendChatMessage")
def send_chat_message(
    body: MacChatMessageIn,
    session: SessionDep,
    request: Request,
    session_id: Optional[int] = Query(None),
):
    """Send a message to the Issue Resolution Agent and get a response."""
    # Get or create session
    if session_id:
        chat_session = session.get(MacChatSession, session_id)
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")
    else:
        chat_session = MacChatSession(session_type=body.session_type)
        session.add(chat_session)
        session.flush()

    # Save user message
    user_msg = MacChatMessage(
        session_id=chat_session.id,
        role=MacChatRole.user,
        content=body.message,
    )
    session.add(user_msg)
    session.flush()

    # Call MAS endpoint (or mock if not available)
    response_content = _query_mas(body.message, request)

    # Save assistant response
    assistant_msg = MacChatMessage(
        session_id=chat_session.id,
        role=MacChatRole.assistant,
        content=response_content,
    )
    session.add(assistant_msg)
    session.commit()
    session.refresh(assistant_msg)

    return assistant_msg


@router.get("/history/{session_id}", response_model=MacChatHistoryOut, operation_id="mac_getChatHistory")
def get_chat_history(session_id: int, session: SessionDep):
    """Get chat history for a session."""
    chat_session = session.get(MacChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = session.exec(
        select(MacChatMessage)
        .where(MacChatMessage.session_id == session_id)
        .order_by(MacChatMessage.created_at)  # type: ignore[invalid-argument-type]
    ).all()

    return MacChatHistoryOut(
        session_id=chat_session.id,  # type: ignore[invalid-argument-type]
        session_type=chat_session.session_type,
        started_at=chat_session.started_at,
        ended_at=chat_session.ended_at,
        messages=[MacChatMessageOut.model_validate(m) for m in messages],
    )


def _query_mas(user_message: str, request: Request) -> str:
    """Query the Multi-Agent Supervisor endpoint.

    Uses the Databricks API raw request format because MAS endpoints
    expect ``input`` (not ``messages``) and return ``output`` (not ``choices``).
    """
    if not MAS_ENDPOINT_NAME:
        return _mock_response(user_message)

    try:
        runtime = request.app.state.runtime
        ws = runtime.ws
        response = ws.api_client.do(
            "POST",
            f"/serving-endpoints/{MAS_ENDPOINT_NAME}/invocations",
            body={"input": [{"role": "user", "content": user_message}]},
        )
        output = response.get("output", [])
        for item in output:
            if item.get("type") == "message" and item.get("role") == "assistant":
                content_parts = item.get("content", [])
                texts = [
                    p.get("text", "")
                    for p in content_parts
                    if p.get("type") == "output_text"
                ]
                if texts:
                    return "\n".join(texts)
        if hasattr(response, "choices") and response.get("choices"):
            return response["choices"][0]["message"]["content"]
        return "I received a response but couldn't parse it. Please try again."
    except Exception as e:
        return (
            f"I encountered an issue connecting to the agent system: {str(e)}. "
            "Please try again in a moment."
        )


def _mock_response(user_message: str) -> str:
    """Fallback mock response for development without a live MAS endpoint."""
    msg_lower = user_message.lower()
    if any(kw in msg_lower for kw in ["underperform", "drop", "decline", "down"]):
        return (
            "Based on the data analysis, here are the key drivers for the performance decline:\n\n"
            "**Traffic:** Footfall is down 12% vs last month, likely due to road construction on the main access route.\n\n"
            "**Pricing:** Your diesel price is 0.04 EUR/L above the nearest Shell station. Consider a targeted price adjustment.\n\n"
            "**Suggested Actions:**\n"
            "1. Reduce diesel price by 0.02 EUR/L to close the competitor gap\n"
            "2. Launch a Fresh Corner promotion to drive in-store traffic\n"
            "3. Extend morning hot food availability by 30 minutes (forecast shows demand)\n\n"
            "Would you like me to look into any of these areas in more detail?"
        )
    elif any(kw in msg_lower for kw in ["upside", "opportunity", "improve", "best"]):
        return (
            "Here are the top opportunity areas across your stations:\n\n"
            "**Pricing Opportunities:**\n"
            "- 8 stations have room for premium fuel margin improvement (+0.02-0.04 EUR/L)\n"
            "- Elasticity analysis shows minimal volume risk\n\n"
            "**Fresh Corner:**\n"
            "- 5 stations with coffee sales 25%+ below peer average\n"
            "- Hot food spoilage reduction could save EUR 1,200/month across your region\n\n"
            "**Staffing:**\n"
            "- 3 stations consistently understaffed during 7-9am peak\n"
            "- Proposed shift reallocation could improve service scores by 15%\n\n"
            "Shall I drill into a specific area or station?"
        )
    elif any(kw in msg_lower for kw in ["hot dog", "food", "bakery", "coffee", "fresh"]):
        return (
            "**Fresh Corner Analysis:**\n\n"
            "Based on the demand forecast and recent patterns:\n\n"
            "- **Hot dogs:** Increase batch sizes 15-20% during 7-9am weekdays. Reduce after 8pm by 30% to cut spoilage.\n"
            "- **Coffee:** Morning peak (6:30-9:00) accounts for 55% of daily volume. Ensure machines are prepped by 6:00.\n"
            "- **Bakery:** Tuesday and Wednesday deliveries are oversized by ~15% vs actual demand. Adjust order template.\n\n"
            "Current spoilage rate: **8.2%** (target: 5%)\n"
            "Potential monthly savings from optimization: **EUR 340**\n\n"
            "Would you like a station-by-station breakdown?"
        )
    else:
        return (
            "I can help you with several areas:\n\n"
            "- **Performance Analysis:** Ask about station performance, trends, and comparisons\n"
            "- **Pricing Intelligence:** Competitor price monitoring and margin optimization\n"
            "- **Operations:** Workforce scheduling, inventory management, and Fresh Corner optimization\n"
            "- **Issue Resolution:** Equipment problems, supply disruptions, and customer complaints\n"
            "- **Customer Relations:** B2B fleet contracts, loyalty program, and campaign management\n\n"
            "Try asking something like:\n"
            '- "Why is Station HU-BP-001 underperforming vs last month?"\n'
            '- "Which 10 stations have the biggest margin upside this weekend?"\n'
            '- "Show me the spoilage trends for Fresh Corner"\n\n'
            "What would you like to explore?"
        )
