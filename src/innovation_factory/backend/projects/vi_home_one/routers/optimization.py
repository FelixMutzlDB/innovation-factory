"""API router for optimization suggestions."""
from fastapi import APIRouter, HTTPException

from ....dependencies import SessionDep
from ..models import VhHousehold, VhOptimizationSuggestionOut
from ..services.optimization import generate_optimization_suggestions

router = APIRouter(prefix="/optimization", tags=["vh-optimization"])


@router.get("/households/{household_id}/suggestions", response_model=list[VhOptimizationSuggestionOut], operation_id="vh_get_optimization_suggestions")
def get_optimization_suggestions(household_id: int, db: SessionDep):
    """Get optimization suggestions for a household based on their selected mode."""
    household = db.get(VhHousehold, household_id)
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")

    suggestions = generate_optimization_suggestions(household, db)
    return suggestions
