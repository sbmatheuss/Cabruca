from fastapi import APIRouter

from app.api.routes.images import router as images_router
from app.api.routes.properties import router as properties_router

api_router = APIRouter()
api_router.include_router(images_router)
api_router.include_router(properties_router)
