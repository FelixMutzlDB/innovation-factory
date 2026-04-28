"""Cross-discipline issue tracker for AECO Hub.

Lists and filters ``dt_issues`` rows: clashes, RFIs, defects, change requests,
safety, design issues. Pagination is hard-capped via ``Query(le=200)`` so the
endpoint can't accidentally return a huge payload.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select

from ....dependencies import SessionDep
from ..models import (
    AecoIssueCategory,
    AecoIssueSeverity,
    AecoIssueStatus,
    DtIssue,
    DtIssueOut,
    DtIssueStatsOut,
    DtProject,
)

router = APIRouter(tags=["aeco-hub"])


@router.get(
    "/projects/{project_id}/issues",
    response_model=list[DtIssueOut],
    operation_id="aeco_listIssues",
)
def list_issues(
    project_id: int,
    db: SessionDep,
    status: Optional[AecoIssueStatus] = None,
    severity: Optional[AecoIssueSeverity] = None,
    category: Optional[AecoIssueCategory] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    stmt = select(DtIssue).where(DtIssue.project_id == project_id)
    if status:
        stmt = stmt.where(DtIssue.status == status)
    if severity:
        stmt = stmt.where(DtIssue.severity == severity)
    if category:
        stmt = stmt.where(DtIssue.category == category)
    stmt = stmt.order_by(DtIssue.created_at.desc()).offset(offset).limit(limit)  # type: ignore[unresolved-attribute]
    return db.exec(stmt).all()


@router.get(
    "/projects/{project_id}/issues/stats",
    response_model=DtIssueStatsOut,
    operation_id="aeco_getIssueStats",
)
def get_issue_stats(project_id: int, db: SessionDep) -> DtIssueStatsOut:
    if not db.get(DtProject, project_id):
        raise HTTPException(404, detail="Project not found")
    base = select(func.count(DtIssue.id)).where(DtIssue.project_id == project_id)
    total = db.exec(base).one()
    open_count = db.exec(base.where(DtIssue.status == AecoIssueStatus.open)).one()
    in_progress = db.exec(base.where(DtIssue.status == AecoIssueStatus.in_progress)).one()
    resolved = db.exec(base.where(DtIssue.status == AecoIssueStatus.resolved)).one()
    critical = db.exec(base.where(DtIssue.severity == AecoIssueSeverity.critical)).one()
    by_category: dict[str, int] = {}
    for cat in AecoIssueCategory:
        by_category[cat.value] = db.exec(base.where(DtIssue.category == cat)).one()
    return DtIssueStatsOut(
        project_id=project_id,
        total=total,
        open=open_count,
        in_progress=in_progress,
        resolved=resolved,
        critical=critical,
        by_category=by_category,
    )


@router.get(
    "/issues/{issue_id}",
    response_model=DtIssueOut,
    operation_id="aeco_getIssue",
)
def get_issue(issue_id: int, db: SessionDep):
    issue = db.get(DtIssue, issue_id)
    if not issue:
        raise HTTPException(404, detail="Issue not found")
    return issue
