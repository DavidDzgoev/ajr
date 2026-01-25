from fastapi import APIRouter

from app.api.routes import (
    items,
    login,
    private,
    users,
    utils,
    judokas,
    competitions,
    contests,
    ratings,
    rating_formulas,
    sync,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)

# Judo rating system routes
api_router.include_router(judokas.router)
api_router.include_router(competitions.router)
api_router.include_router(contests.router)
api_router.include_router(ratings.router)
api_router.include_router(rating_formulas.router)
api_router.include_router(sync.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
