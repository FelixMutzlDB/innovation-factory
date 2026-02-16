"""Knowledge base router for BSH Home Connect."""
from typing import Annotated, List
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from ....dependencies import get_session
from ..models import (
    BshKnowledgeArticle,
    BshKnowledgeArticleOut,
    BshDocument,
    BshDocumentOut,
    DeviceCategory,
)

router = APIRouter(tags=["bsh-knowledge"])


@router.get("/knowledge/search", response_model=List[BshKnowledgeArticleOut], operation_id="bsh_searchKnowledge")
def search_knowledge(
    db: Annotated[Session, Depends(get_session)],
    query: str = Query(..., min_length=3),
    category: DeviceCategory | None = None,
    limit: int = Query(default=10, le=50),
):
    """Search knowledge base articles."""
    statement = select(BshKnowledgeArticle)
    if category:
        statement = statement.where(BshKnowledgeArticle.category == category)
    statement = statement.where(
        (BshKnowledgeArticle.title.contains(query)) |  # type: ignore[unresolved-attribute]
        (BshKnowledgeArticle.content.contains(query))  # type: ignore[unresolved-attribute]
    )
    statement = statement.limit(limit)
    articles = db.exec(statement).all()
    return [BshKnowledgeArticleOut.model_validate(article) for article in articles]


@router.get("/knowledge/device/{device_id}", response_model=List[BshKnowledgeArticleOut], operation_id="bsh_getDeviceKnowledge")
def get_device_knowledge(device_id: int, db: Annotated[Session, Depends(get_session)]):
    """Get knowledge articles for a specific device."""
    statement = select(BshKnowledgeArticle).where(BshKnowledgeArticle.device_id == device_id)
    articles = db.exec(statement).all()
    return [BshKnowledgeArticleOut.model_validate(article) for article in articles]


@router.get("/documents/{device_id}", response_model=List[BshDocumentOut], operation_id="bsh_getDeviceDocuments")
def get_device_documents(device_id: int, db: Annotated[Session, Depends(get_session)]):
    """Get documents for a specific device."""
    statement = select(BshDocument).where(BshDocument.device_id == device_id)
    documents = db.exec(statement).all()
    return [BshDocumentOut.model_validate(doc) for doc in documents]
