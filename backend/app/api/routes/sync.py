"""Data sync API routes."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app import crud
from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.models import (
    DataSync,
    DataSyncCreate,
    DataSyncPublic,
    DataSyncsPublic,
    Message,
)
from app.services.sync_service import SyncService

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post(
    "/trigger",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=DataSyncPublic,
)
async def trigger_sync(
    *,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Trigger data synchronization from judobase (admin only)."""
    sync_service = SyncService(session=session)
    data_sync = await sync_service.sync_all(created_by=current_user.id)
    return data_sync


@router.get("/history", response_model=DataSyncsPublic)
def read_sync_history(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
) -> Any:
    """Get sync history."""
    syncs, count = crud.get_data_syncs(
        session=session, skip=skip, limit=limit, status=status
    )
    return DataSyncsPublic(data=syncs, count=count)


@router.get("/{sync_id}", response_model=DataSyncPublic)
def read_sync(
    sync_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Get a specific sync by id."""
    data_sync = crud.get_data_sync_by_id(session=session, sync_id=sync_id)
    if not data_sync:
        raise HTTPException(status_code=404, detail="Sync not found")
    return data_sync
