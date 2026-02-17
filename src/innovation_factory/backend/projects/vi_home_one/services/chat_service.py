"""Chat service with RAG pipeline and guardrails for energy system support."""
from typing import AsyncGenerator
from sqlmodel import Session, select

from ..models import (
    VhTicket,
    VhKnowledgeArticle,
    VhEnergyDevice,
    VhHousehold,
    VhEnergyReading,
)


class ChatService:
    """AI chat service with RAG and S4 guardrails."""

    def __init__(self):
        self.temperature = 0.1
        self.system_prompt = """You are an AI assistant for ViDistrictOne, a neighborhood energy management system by Viessmann.

Your role is to help users with:
- Energy system troubleshooting (heat pumps, PV systems, batteries, EVs)
- Optimization advice for energy consumption and costs
- Maintenance guidance
- Understanding their energy data

GUARDRAILS (S4 Framework - Show Sources or Say Sorry):
1. ONLY answer based on the provided context from knowledge base and device data
2. ALWAYS cite specific sources for your answers
3. If you don't have enough information, politely decline and suggest contacting a technician
4. For safety-critical issues (electrical, gas, high voltage), ALWAYS recommend professional help
5. Never speculate or make up technical specifications
6. Be concise and actionable
"""

    async def stream_chat_response(
        self, ticket_id: int, user_message: str, session: Session,
    ) -> AsyncGenerator[str, None]:
        """Stream chat response with RAG context retrieval."""
        ticket = session.get(VhTicket, ticket_id)
        if not ticket:
            yield "Error: Ticket not found."
            return

        household = session.get(VhHousehold, ticket.household_id)
        device = None
        if ticket.device_id:
            device = session.get(VhEnergyDevice, ticket.device_id)

        context_parts = []

        if device:
            articles_query = select(VhKnowledgeArticle).where(
                VhKnowledgeArticle.device_type == device.device_type
            ).limit(3)
            articles = session.exec(articles_query).all()
            for article in articles:
                context_parts.append(f"### {article.title}\n{article.content}\n")

            context_parts.append(f"""
### Device Information
- Type: {device.device_type.value}
- Brand: {device.brand}
- Model: {device.model}
- Capacity: {device.capacity_kw} kW
- Installation Date: {device.installation_date}
- Last Maintenance: {device.last_maintenance_date or 'Not recorded'}
""")

        if household:
            latest_reading_query = select(VhEnergyReading).where(
                VhEnergyReading.household_id == household.id
            ).order_by(VhEnergyReading.timestamp.desc()).limit(1)  # type: ignore[unresolved-attribute]
            latest_reading = session.exec(latest_reading_query).first()
            if latest_reading:
                context_parts.append(f"""
### Current Energy Status
- Total Consumption: {latest_reading.total_consumption_kwh:.2f} kWh
- PV Generation: {latest_reading.pv_generation_kwh:.2f} kWh
- Grid Import: {latest_reading.grid_import_kwh:.2f} kWh
- Battery Level: {latest_reading.battery_level_kwh:.2f} kWh
""")

        context = "\n".join(context_parts)

        response = self._generate_mock_response(user_message, context, device)

        words = response.split()
        for i, word in enumerate(words):
            if i > 0:
                yield " "
            yield word
            import asyncio
            await asyncio.sleep(0.05)

    def _generate_mock_response(self, user_message: str, context: str, device) -> str:
        """Generate a mock response based on user message keywords (for demo)."""
        message_lower = user_message.lower()

        if "not" in message_lower and ("heat" in message_lower or "warm" in message_lower):
            return """Based on the heat pump troubleshooting guide:

**Possible causes for heating issues:**

1. **Check thermostat settings** - Ensure target temperature is set correctly
2. **Air filter maintenance** - Clean or replace air filters if dirty
3. **Outdoor unit clearance** - Ensure outdoor unit has clear airflow
4. **Refrigerant levels** - Low refrigerant may indicate a leak

**Safety note:** If you smell gas or notice unusual sounds, turn off the system immediately and contact a certified technician.

**Source:** Heat Pump Efficiency Drop - Common Causes (Knowledge Base)"""

        elif "pv" in message_lower or "solar" in message_lower or "panel" in message_lower:
            return """Based on the solar system documentation:

**Common PV output issues:**

1. **Dirt and debris** - Clean panels with water 2x per year
2. **Shading** - Check for new obstacles
3. **Inverter status** - Verify inverter is operating normally
4. **System monitoring** - Track performance through Viessmann One Base app

**Source:** Solar Panel Output Reduced - Troubleshooting Guide (Knowledge Base)"""

        elif "battery" in message_lower and ("charg" in message_lower or "not" in message_lower):
            return """Based on battery system diagnostics:

**Battery charging issues checklist:**

1. **Battery Management System** - Check GridBox UX for battery status
2. **Temperature protection** - Optimal range: 15-25C
3. **Charge settings** - Review configuration in GridBox

**Source:** Battery Not Charging - Diagnosis Steps (Knowledge Base)"""

        elif "cost" in message_lower or "save" in message_lower or "money" in message_lower:
            return """**Cost Optimization Tips:**

1. **Night Tariff Usage** (22:00-06:00) - Save up to 25%
2. **Solar Self-Consumption** - Use appliances during sunny hours
3. **Battery Optimization** - Discharge during peak hours (18-21)

**Source:** Optimization Modes Explained (Knowledge Base)"""

        else:
            device_info = f"- Your household has {device.brand} {device.model}" if device else ""
            return f"""I'm here to help with your energy system!

{device_info}

**Common topics I can assist with:**
- Heat pump issues and maintenance
- Solar panel performance
- Battery charging and optimization
- EV charging strategies
- Cost optimization tips

**Source:** ViDistrictOne Knowledge Base"""
