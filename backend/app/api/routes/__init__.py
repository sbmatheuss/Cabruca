from fastapi import APIRouter

from app.api.routes.images import router as images_router

api_router = APIRouter()
api_router.include_router(images_router)
