from fastapi import APIRouter, Request

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict[str, object]:
    settings = get_settings()
    service = getattr(request.app.state, "game_service", None)
    initialized = service is not None
    return {
        "status": "healthy" if initialized else "degraded",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "catalogue_initialized": initialized,
        "game_count": service.count if service else 0,
    }
