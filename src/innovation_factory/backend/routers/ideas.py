from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import select

from ..dependencies import SessionDep, RuntimeDep
from ..models import (
    IdeaSession,
    IdeaSessionOut,
    IdeaSessionCreate,
    IdeaSessionStatus,
    IdeaMessage,
    IdeaMessageIn,
    IdeaMessageOut,
)

router = APIRouter(prefix="/ideas", tags=["ideas"])


@router.post("/sessions", response_model=IdeaSessionOut, operation_id="createIdeaSession")
def create_idea_session(db: SessionDep):
    """Start a new idea session."""
    session = IdeaSession(status=IdeaSessionStatus.collecting_name)
    db.add(session)
    db.commit()
    db.refresh(session)

    # Add welcome message
    welcome = IdeaMessage(
        session_id=session.id,
        role="assistant",
        content="Welcome! Let's build something new. What's the name of the company? (It can also be made up)",
    )
    db.add(welcome)
    db.commit()

    return session


@router.get("/sessions/{session_id}", response_model=IdeaSessionOut, operation_id="getIdeaSession")
def get_idea_session(session_id: int, db: SessionDep):
    """Get an idea session."""
    session = db.get(IdeaSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get(
    "/sessions/{session_id}/messages",
    response_model=List[IdeaMessageOut],
    operation_id="getIdeaMessages",
)
def get_idea_messages(session_id: int, db: SessionDep):
    """Get all messages for an idea session."""
    session = db.get(IdeaSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    statement = (
        select(IdeaMessage)
        .where(IdeaMessage.session_id == session_id)
        .order_by(IdeaMessage.created_at.asc())
    )
    messages = db.exec(statement).all()
    return list(messages)


@router.post("/sessions/{session_id}/chat", operation_id="sendIdeaMessage")
async def send_idea_message(
    session_id: int,
    message: IdeaMessageIn,
    db: SessionDep,
    rt: RuntimeDep,
):
    """Send a message in an idea session and get a response (SSE streaming for generation)."""
    session = db.get(IdeaSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save user message
    user_msg = IdeaMessage(
        session_id=session.id,
        role="user",
        content=message.content,
    )
    db.add(user_msg)
    db.commit()

    # Process based on session state
    if session.status == IdeaSessionStatus.collecting_name:
        # User just provided the company name
        session.company_name = message.content.strip()
        session.status = IdeaSessionStatus.collecting_description
        db.add(session)
        db.commit()

        reply = IdeaMessage(
            session_id=session.id,
            role="assistant",
            content=f'Great! "{session.company_name}" sounds interesting. Now describe what you\'d like to build. What kind of application or service should it be?',
        )
        db.add(reply)
        db.commit()

        return {"message": reply.content, "status": session.status, "done": True}

    elif session.status == IdeaSessionStatus.collecting_description:
        # User provided the description - generate the prompt
        session.description = message.content.strip()
        session.status = IdeaSessionStatus.generating
        db.add(session)
        db.commit()

        # Generate the coding agent prompt
        prompt = _generate_coding_prompt(session.company_name or "", session.description or "")

        session.generated_prompt = prompt
        session.status = IdeaSessionStatus.completed
        db.add(session)
        db.commit()

        reply = IdeaMessage(
            session_id=session.id,
            role="assistant",
            content=f"Here's your coding agent prompt:\n\n---\n\n{prompt}\n\n---\n\nYou can copy this prompt and use it with a coding agent to build your application!",
        )
        db.add(reply)
        db.commit()

        return {
            "message": reply.content,
            "status": session.status,
            "generated_prompt": prompt,
            "done": True,
        }

    else:
        return {
            "message": "This session is already complete. Start a new session to build another idea!",
            "status": session.status,
            "done": True,
        }


def _generate_coding_prompt(company_name: str, description: str) -> str:
    """Generate a structured coding agent prompt."""
    return f"""Build a full-stack web application for "{company_name}".

## Description
{description}

## Technical Requirements
- **Framework:** Use APX framework (FastAPI backend + React 19 + TypeScript frontend)
- **Database:** SQLModel with PostgreSQL (Lakebase on Databricks)
- **UI:** shadcn/ui components + Tailwind CSS
- **Routing:** TanStack Router (file-based routing)
- **Data Fetching:** TanStack Query with auto-generated API client
- **Deployment:** Deploy as a Databricks App

## Architecture
- Backend: FastAPI with SQLModel ORM, Pydantic validation
- Frontend: React 19 with TypeScript, shadcn/ui components
- Database: PostgreSQL with auto-migration via SQLModel.metadata.create_all()
- API: RESTful with auto-generated OpenAPI schema

## Key Patterns
- Use the 3-model pattern: Entity (DB table), EntityIn (input validation), EntityOut (response)
- All API routes must have response_model and operation_id for client generation
- Use Suspense + React Query for data fetching
- Sidebar layout with navigation
- Dark/light mode toggle

## Getting Started
1. Initialize with: `apx init --name {company_name.lower().replace(' ', '-')} --template stateful`
2. Define your database models in `backend/models.py`
3. Create API routes in `backend/routers/`
4. Build UI pages in `ui/routes/`
5. Seed sample data in `backend/seed.py`
6. Run locally: `apx dev start`
7. Deploy: `databricks bundle deploy`"""
