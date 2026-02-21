from fastapi import APIRouter

from app.api.routes import (
    competitions,
    contests,
    countries,
    judokas,
    login,
    rating_changes,
    rating_formulas,
    ratings,
    sync,
    users,
    utils,
)

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)

# Judo rating system routes
api_router.include_router(judokas.router)
api_router.include_router(competitions.router)
api_router.include_router(contests.router)
api_router.include_router(countries.router)
api_router.include_router(ratings.router)
api_router.include_router(rating_changes.router)
api_router.include_router(rating_formulas.router)
api_router.include_router(sync.router)
