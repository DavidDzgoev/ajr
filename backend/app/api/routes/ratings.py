"""Ratings API routes."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Rating,
    RatingPublic,
    RatingsPublic,
)

router = APIRouter(prefix="/ratings", tags=["ratings"])


@router.get("/", response_model=RatingsPublic)
def read_ratings(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    formula_id: uuid.UUID | None = None,
    judoka_id: int | None = None,
    surname: str | None = None,
    weight: str | None = None,
    rating_min: float | None = None,
) -> Any:
    """Retrieve ratings."""
    ratings, count = crud.get_ratings(
        session=session,
        skip=skip,
        limit=limit,
        formula_id=formula_id,
        judoka_id=judoka_id,
        surname=surname,
        weight=weight,
        rating_min=rating_min,
    )

    return RatingsPublic(data=ratings, count=count)


@router.get("/{formula_id}/leaderboard", response_model=Any)
def read_leaderboard(
    formula_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Get leaderboard for a specific formula."""
    formula = crud.get_rating_formula_by_id(session=session, formula_id=formula_id)
    if not formula:
        raise HTTPException(status_code=404, detail="Rating formula not found")

    ratings = crud.get_leaderboard(
        session=session, formula_id=formula_id, skip=skip, limit=limit
    )
    return {"data": ratings, "count": len(ratings)}


@router.get("/{formula_id}/judoka/{judoka_id}", response_model=RatingPublic)
def read_judoka_rating(
    formula_id: uuid.UUID,
    judoka_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get rating for a specific judoka and formula."""
    rating = crud.get_rating_by_judoka_and_formula(
        session=session, judoka_id=judoka_id, formula_id=formula_id
    )
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    return rating


@router.get("/{formula_id}/judoka/{judoka_id}/history", response_model=Any)
def read_rating_history(
    formula_id: uuid.UUID,
    judoka_id: int,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Get rating change history for a specific judoka and formula."""
    rating = crud.get_rating_by_judoka_and_formula(
        session=session, judoka_id=judoka_id, formula_id=formula_id
    )
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")

    changes = crud.get_rating_history(
        session=session, rating_id=rating.id, skip=skip, limit=limit
    )
    return {"data": changes, "count": len(changes)}
