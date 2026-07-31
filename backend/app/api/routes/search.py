"""Phase 3 — Prompt Interpretation API."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.ai.preference_parser import KeywordPreferenceParser
from app.api.dependencies import get_preference_parser
from app.schemas.search import InterpretRequest, InterpretResponse, ParsedPreferencesResponse

router = APIRouter(prefix="/search", tags=["search"])

ParserDep = Annotated[KeywordPreferenceParser, Depends(get_preference_parser)]


@router.post("/interpret", response_model=InterpretResponse)
def interpret(payload: InterpretRequest, parser: ParserDep) -> InterpretResponse:
    parsed = parser.parse(payload.query)
    return InterpretResponse(
        query=payload.query,
        preferences=ParsedPreferencesResponse(
            genres=list(parsed.genres),
            platforms=list(parsed.platforms),
            tags=list(parsed.tags),
            free_text=parsed.free_text,
        ),
    )
