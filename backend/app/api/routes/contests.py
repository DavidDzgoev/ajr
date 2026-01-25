"""Contests API routes."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    ContestPublic,
    ContestsPublic,
)

router = APIRouter(prefix="/contests", tags=["contests"])


@router.get("/", response_model=ContestsPublic)
def read_contests(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    competition_id: int | None = None,
    judoka_id: int | None = None,
) -> Any:
    """Retrieve contests."""
    contests = crud.get_contests(
        session=session,
        skip=skip,
        limit=limit,
        competition_id=competition_id,
        judoka_id=judoka_id,
    )
    return ContestsPublic(data=contests, count=len(contests))


@router.get("/{contest_id}", response_model=ContestPublic)
def read_contest(
    contest_id: int, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get a specific contest by id."""
    contest = crud.get_contest_by_id(session=session, contest_id=contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    return contest
