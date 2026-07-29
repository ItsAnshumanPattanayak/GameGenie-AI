from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_game_service
from app.schemas.common import FacetResponse
from app.services.game_service import GameService

router = APIRouter(tags=["catalogue"])
ServiceDep = Annotated[GameService, Depends(get_game_service)]


@router.get("/genres", response_model=FacetResponse)
def genres(service: ServiceDep) -> FacetResponse:
    return FacetResponse(items=service.genres())


@router.get("/platforms", response_model=FacetResponse)
def platforms(service: ServiceDep) -> FacetResponse:
    return FacetResponse(items=service.platforms())
