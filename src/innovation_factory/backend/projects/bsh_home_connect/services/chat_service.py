"""Chat service with RAG pipeline for BSH appliance support."""
from typing import List, Dict, Any, AsyncIterator
from sqlmodel import Session, select
import json
from datetime import datetime

from ..models import (
    BshTicket,
    BshCustomerDevice,
    BshDevice,
    BshKnowledgeArticle,
    BshDocument,
    BshChatSession,
    BshChatMessage,
    BshChatRole,
)


class ChatService:
    """Service for AI-powered chat with RAG and guardrails."""

    def __init__(self):
        self.model_endpoint = "databricks-meta-llama-3-1-70b-instruct"

    def _build_system_prompt(self) -> str:
        return """You are a helpful BSH appliance repair assistant. Your role is to help customers and technicians troubleshoot and repair BSH kitchen appliances (Bosch and Siemens brands).

CRITICAL GUARDRAILS:
1. ONLY answer based on the provided context (knowledge articles, manuals, device specifications).
2. ALWAYS cite your sources.
3. If you don't have enough information, say: "I don't have enough information. Let me connect you with a technician."
4. DO NOT make up specifications, repair procedures, or part numbers.
5. For safety-critical issues, always recommend contacting a licensed technician.
6. Keep responses clear, step-by-step, and focused.
"""

    def _retrieve_context(
        self, db: Session, ticket: BshTicket,
        customer_device: BshCustomerDevice, device: BshDevice, query: str,
    ) -> List[Dict[str, Any]]:
        contexts = []

        contexts.append({
            "type": "device_info",
            "source": f"{device.brand} {device.name} ({device.model_number})",
            "content": f"""Device: {device.brand} {device.name}
Model: {device.model_number}
Category: {device.category}
Serial Number: {customer_device.serial_number}
Warranty Status: {'Active' if customer_device.warranty_expiry_date and customer_device.warranty_expiry_date > datetime.now().date() else 'Expired'}
"""
        })

        kb_statement = select(BshKnowledgeArticle).where(
            BshKnowledgeArticle.category == device.category
        ).limit(5)
        articles = db.exec(kb_statement).all()
        for article in articles:
            if any(word.lower() in article.content.lower() for word in query.split() if len(word) > 3):
                contexts.append({
                    "type": "knowledge_article",
                    "source": f"Knowledge Article: {article.title}",
                    "content": f"{article.title}\n\n{article.content}",
                })

        doc_statement = select(BshDocument).where(BshDocument.device_id == device.id)
        documents = db.exec(doc_statement).all()
        for doc in documents:
            contexts.append({
                "type": "document",
                "source": f"{doc.document_type.replace('_', ' ').title()}: {doc.title}",
                "content": doc.content[:2000] if doc.content else "",
            })

        return contexts

    async def stream_chat_response(
        self, db: Session, ticket_id: int, user_message: str,
        session_type: str = "customer_support",
    ) -> AsyncIterator[str]:
        """Stream AI response with RAG."""
        ticket = db.get(BshTicket, ticket_id)
        if not ticket:
            yield json.dumps({"error": "Ticket not found"})
            return

        customer_device = db.get(BshCustomerDevice, ticket.customer_device_id)
        device = db.get(BshDevice, customer_device.device_id)

        # Get or create chat session
        session_statement = select(BshChatSession).where(
            BshChatSession.ticket_id == ticket_id,
            BshChatSession.session_type == session_type,
        ).order_by(BshChatSession.started_at.desc())
        session = db.exec(session_statement).first()

        if not session:
            session = BshChatSession(ticket_id=ticket_id, session_type=session_type)
            db.add(session)
            db.commit()
            db.refresh(session)

        # Save user message
        user_msg = BshChatMessage(
            session_id=session.id, role=BshChatRole.user, content=user_message,
        )
        db.add(user_msg)
        db.commit()

        # Retrieve context
        contexts = self._retrieve_context(db, ticket, customer_device, device, user_message)

        # Generate mock response (in production, use Databricks Foundation Model API)
        response = self._generate_mock_response(user_message, device, contexts)

        # Save assistant response
        assistant_msg = BshChatMessage(
            session_id=session.id, role=BshChatRole.assistant, content=response,
            sources=[ctx["source"] for ctx in contexts],
        )
        db.add(assistant_msg)
        db.commit()

        yield json.dumps({"content": response, "done": False})
        yield json.dumps({"content": "", "done": True})

    def _generate_mock_response(self, user_message: str, device: BshDevice, contexts: list) -> str:
        """Generate mock response for demo."""
        msg = user_message.lower()

        if "error" in msg or "e15" in msg or "e24" in msg:
            return f"""Based on the troubleshooting guide for your {device.brand} {device.name}:

**Error Code Troubleshooting:**
1. Switch off the appliance and unplug it
2. Check for visible issues (leaks, blockages)
3. Wait 30 seconds and restart
4. If error persists, check the knowledge base for your specific error code

**Source:** {device.brand} {device.name} Troubleshooting Guide"""

        elif "not working" in msg or "broken" in msg:
            return f"""I understand your {device.brand} {device.name} is having issues. Let's troubleshoot:

1. **Check power supply** - Ensure the appliance is properly plugged in
2. **Check circuit breaker** - Make sure it hasn't tripped
3. **Check for error codes** - Note any codes on the display
4. **Basic reset** - Turn off for 30 seconds, then restart

If these steps don't help, I recommend creating a service ticket for a technician visit.

**Source:** {device.brand} {device.name} User Manual"""

        else:
            return f"""I'm here to help with your {device.brand} {device.name}!

I can assist with:
- Error code diagnosis
- Troubleshooting steps
- Maintenance guidance
- Warranty information

Please describe your issue in detail and I'll provide specific guidance.

**Source:** BSH Knowledge Base"""

    def get_chat_history(self, db: Session, ticket_id: int, session_type: str = "customer_support") -> List[BshChatMessage]:
        """Get chat history for a ticket."""
        session_statement = select(BshChatSession).where(
            BshChatSession.ticket_id == ticket_id,
            BshChatSession.session_type == session_type,
        ).order_by(BshChatSession.started_at.desc())
        session = db.exec(session_statement).first()
        if not session:
            return []

        return list(db.exec(
            select(BshChatMessage).where(BshChatMessage.session_id == session.id)
            .order_by(BshChatMessage.created_at.asc())
        ).all())
