from pydantic import BaseModel
from sqlmodel import SQLModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from .. import __version__


# ============================================================================
# Platform Models
# ============================================================================

class Project(SQLModel, table=True):
    __tablename__ = "if_projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    name: str
    description: str
    company: str
    icon: Optional[str] = None
    color: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PlatformUser(SQLModel, table=True):
    __tablename__ = "platform_users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    display_name: str
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# "Build a New Idea" Models
# ============================================================================

class IdeaSessionStatus(str, Enum):
    collecting_name = "collecting_name"
    collecting_description = "collecting_description"
    generating = "generating"
    completed = "completed"


class IdeaSession(SQLModel, table=True):
    __tablename__ = "idea_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_name: Optional[str] = None
    description: Optional[str] = None
    generated_prompt: Optional[str] = None
    status: IdeaSessionStatus = Field(default=IdeaSessionStatus.collecting_name)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class IdeaMessage(SQLModel, table=True):
    __tablename__ = "idea_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="idea_sessions.id", index=True)
    role: str  # "user", "assistant", "system"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Pydantic Models (Input/Output)
# ============================================================================

class VersionOut(BaseModel):
    version: str

    @classmethod
    def from_metadata(cls):
        return cls(version=__version__)


class ProjectOut(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    company: str
    icon: Optional[str] = None
    color: Optional[str] = None


class IdeaSessionOut(BaseModel):
    id: int
    company_name: Optional[str] = None
    description: Optional[str] = None
    generated_prompt: Optional[str] = None
    status: IdeaSessionStatus
    created_at: datetime


class IdeaSessionCreate(BaseModel):
    pass


class IdeaMessageIn(BaseModel):
    content: str


class IdeaMessageOut(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime
