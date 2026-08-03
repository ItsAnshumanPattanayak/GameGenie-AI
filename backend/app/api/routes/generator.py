"""Phase 9 — Game generation API."""

import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_generator_service
from app.core.exceptions import AppError
from app.schemas.generator import GeneratorInterpretRequest, GeneratorInterpretResponse
from app.services.generator_service import GeneratorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2/generator", tags=["generator-v2"])

GeneratorDep = Annotated[GeneratorService, Depends(get_generator_service)]


@router.post("/interpret", response_model=GeneratorInterpretResponse)
def interpret(payload: GeneratorInterpretRequest, service: GeneratorDep) -> GeneratorInterpretResponse:
    if payload.template not in service.supported_templates:
        raise AppError(
            "UNSUPPORTED_TEMPLATE",
            f"Template '{payload.template}' is not supported.",
            422,
        )

    start = time.perf_counter()
    configuration, warnings = service.build_space_shooter(payload.query)
    elapsed_ms = (time.perf_counter() - start) * 1000

    logger.info(
        "Generator interpreted template=%s difficulty=%s time_ms=%.2f",
        payload.template,
        configuration.difficulty,
        elapsed_ms,
    )

    return GeneratorInterpretResponse(
        query=payload.query,
        template=payload.template,
        configuration=configuration,
        warnings=warnings,
    )
