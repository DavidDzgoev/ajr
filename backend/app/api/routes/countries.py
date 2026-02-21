"""Countries API routes."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    CountriesPublic,
    CountryPublic,
)

router = APIRouter(prefix="/countries", tags=["countries"])


@router.get("/", response_model=CountriesPublic)
def read_countries(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Retrieve countries."""
    countries, count = crud.get_countries(session=session, skip=skip, limit=limit)
    return CountriesPublic(data=countries, count=count)


@router.get("/{country_id}", response_model=CountryPublic)
def read_country(
    country_id: int, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get a specific country by id."""
    country = crud.get_country_by_id(session=session, country_id=country_id)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country
