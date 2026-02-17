"""Chat service for the MOL ASM Cockpit.

Proxies user messages to the Multi-Agent Supervisor (MAS) serving endpoint.
Uses shared Databricks Agent Bricks utilities.
"""

from databricks.sdk import WorkspaceClient

from ....services.databricks_agents import extract_agent_text, query_agent_endpoint
from ..databricks_config import MAS_ENDPOINT_NAME


def send_message(ws: WorkspaceClient, user_message: str) -> str:
    """Send a message to the Multi-Agent Supervisor and return the response.

    If MAS_ENDPOINT_NAME is not configured, returns a mock response for development.

    Args:
        ws: WorkspaceClient instance
        user_message: The user's message

    Returns:
        The assistant's response text
    """
    if not MAS_ENDPOINT_NAME:
        return _mock_response(user_message)

    try:
        messages = [{"role": "user", "content": user_message}]
        result = query_agent_endpoint(ws, MAS_ENDPOINT_NAME, messages)
        return extract_agent_text(result)
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
