"""Competitions API routes."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    CompetitionPublic,
    CompetitionsPublic,
)

router = APIRouter(prefix="/competitions", tags=["competitions"])


@router.get("/", response_model=CompetitionsPublic)
def read_competitions(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    id_country: int | None = None,
) -> Any:
    """Retrieve competitions."""
    competitions, count = crud.get_competitions(
        session=session,
        skip=skip,
        limit=limit,
        id_country=id_country,
    )
    return CompetitionsPublic(data=competitions, count=count)


@router.get("/{competition_id}", response_model=CompetitionPublic)
def read_competition(
    competition_id: int, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get a specific competition by id."""
    competition = crud.get_competition_by_id(
        session=session, competition_id=competition_id
    )
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    return competition


@router.get("/{competition_id}/contests", response_model=Any)
def read_competition_contests(
    competition_id: int,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Get contests for a specific competition."""
    competition = crud.get_competition_by_id(
        session=session, competition_id=competition_id
    )
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")

    contests = crud.get_contests(
        session=session, competition_id=competition_id, skip=skip, limit=limit
    )
    return {"data": contests, "count": len(contests)}
