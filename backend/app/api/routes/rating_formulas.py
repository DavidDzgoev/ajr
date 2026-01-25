"""Rating formulas API routes."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import func, select

from app import crud
from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.models import (
    RatingFormula,
    RatingFormulaCreate,
    RatingFormulaPublic,
    RatingFormulaUpdate,
    RatingFormulasPublic,
)

router = APIRouter(prefix="/rating-formulas", tags=["rating-formulas"])


@router.get("/", response_model=RatingFormulasPublic)
def read_rating_formulas(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    is_active: bool | None = None,
) -> Any:
    """Retrieve rating formulas."""
    count_statement = select(func.count()).select_from(RatingFormula)
    if is_active is not None:
        count_statement = count_statement.where(RatingFormula.is_active == is_active)
    count = session.exec(count_statement).one()

    formulas = crud.get_rating_formulas(
        session=session, skip=skip, limit=limit, is_active=is_active
    )

    return RatingFormulasPublic(data=formulas, count=count)


@router.get("/{formula_id}", response_model=RatingFormulaPublic)
def read_rating_formula(
    formula_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get a specific rating formula by id."""
    formula = crud.get_rating_formula_by_id(session=session, formula_id=formula_id)
    if not formula:
        raise HTTPException(status_code=404, detail="Rating formula not found")
    return formula


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=RatingFormulaPublic,
)
def create_rating_formula(
    *, session: SessionDep, formula_in: RatingFormulaCreate
) -> Any:
    """Create new rating formula (admin only)."""
    formula = crud.create_rating_formula(session=session, formula_in=formula_in)
    return formula


@router.patch(
    "/{formula_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=RatingFormulaPublic,
)
def update_rating_formula(
    *,
    session: SessionDep,
    formula_id: uuid.UUID,
    formula_in: RatingFormulaUpdate,
) -> Any:
    """Update a rating formula (admin only)."""
    formula = crud.get_rating_formula_by_id(session=session, formula_id=formula_id)
    if not formula:
        raise HTTPException(status_code=404, detail="Rating formula not found")

    formula = crud.update_rating_formula(
        session=session, db_formula=formula, formula_in=formula_in
    )
    return formula


@router.delete(
    "/{formula_id}",
    dependencies=[Depends(get_current_active_superuser)],
)
def delete_rating_formula(
    formula_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Delete a rating formula (admin only)."""
    formula = crud.get_rating_formula_by_id(session=session, formula_id=formula_id)
    if not formula:
        raise HTTPException(status_code=404, detail="Rating formula not found")

    crud.delete_rating_formula(session=session, formula_id=formula_id)
    return {"message": "Rating formula deleted successfully"}
