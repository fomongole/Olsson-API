from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint for Render keep-alive pings and uptime monitoring.
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }
