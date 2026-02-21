"""Rating changes API routes."""

from typing import Any

from fastapi import APIRouter

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    RatingChangesPublic,
)

router = APIRouter(prefix="/rating-changes", tags=["rating-changes"])


@router.get("/", response_model=RatingChangesPublic)
def read_rating_changes(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    judoka_id: int | None = None,
    contest_id: int | None = None,
) -> Any:
    """Retrieve rating changes."""
    changes, count = crud.get_rating_changes(
        session=session,
        skip=skip,
        limit=limit,
        judoka_id=judoka_id,
        contest_id=contest_id,
    )
    return RatingChangesPublic(data=changes, count=count)
