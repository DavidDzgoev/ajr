"""Judokas API routes."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    JudokaPublic,
    JudokasPublic,
)

router = APIRouter(prefix="/judokas", tags=["judokas"])


@router.get("/", response_model=JudokasPublic)
def read_judokas(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    id_country: int | None = None,
) -> Any:
    """Retrieve judokas."""
    judokas, count = crud.get_judokas(
        session=session,
        skip=skip,
        limit=limit,
        id_country=id_country,
    )
    return JudokasPublic(data=judokas, count=count)


@router.get("/{judoka_id}", response_model=JudokaPublic)
def read_judoka(judoka_id: int, session: SessionDep, current_user: CurrentUser) -> Any:
    """Get a specific judoka by id."""
    judoka = crud.get_judoka_by_id(session=session, judoka_id=judoka_id)
    if not judoka:
        raise HTTPException(status_code=404, detail="Judoka not found")
    return judoka


@router.get("/{judoka_id}/contests", response_model=Any)
def read_judoka_contests(
    judoka_id: int,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Get contests for a specific judoka."""
    judoka = crud.get_judoka_by_id(session=session, judoka_id=judoka_id)
    if not judoka:
        raise HTTPException(status_code=404, detail="Judoka not found")

    contests = crud.get_judoka_contests(
        session=session, judoka_id=judoka_id, skip=skip, limit=limit
    )
    return {"data": contests, "count": len(contests)}


@router.get("/{judoka_id}/ratings", response_model=Any)
def read_judoka_ratings(
    judoka_id: int, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get ratings for a specific judoka."""
    judoka = crud.get_judoka_by_id(session=session, judoka_id=judoka_id)
    if not judoka:
        raise HTTPException(status_code=404, detail="Judoka not found")

    ratings = crud.get_judoka_ratings(session=session, judoka_id=judoka_id)
    return {"data": ratings, "count": len(ratings)}
