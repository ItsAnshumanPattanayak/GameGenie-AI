"""Domain exceptions and consistent FastAPI error handlers."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code, self.message, self.status_code = code, message, status_code
        super().__init__(message)


class GameNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__("GAME_NOT_FOUND", "The requested game was not found.", 404)


class DatasetMissingError(AppError):
    def __init__(self, message: str = "The configured dataset was not found.") -> None:
        super().__init__("DATASET_MISSING", message, 503)


class InvalidDatasetError(AppError):
    def __init__(self, message: str = "The dataset is malformed or invalid.") -> None:
        super().__init__("INVALID_DATASET", message, 503)


class CatalogueInitializationError(AppError):
    def __init__(self) -> None:
        super().__init__("CATALOGUE_INITIALIZATION_FAILED", "The game catalogue is unavailable.", 503)


def _error(code: str, message: str, details: Any | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"success": False, "error": {"code": code, "message": message}}
    if details is not None:
        result["error"]["details"] = details
    return result


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning("Application error path=%s code=%s", request.url.path, exc.code)
        return JSONResponse(status_code=exc.status_code, content=_error(exc.code, exc.message))

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [{"field": ".".join(map(str, item["loc"])), "message": item["msg"]} for item in exc.errors()]
        logger.info("Request validation failed path=%s", request.url.path)
        return JSONResponse(status_code=422, content=_error("VALIDATION_ERROR", "Request validation failed.", details))

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        message = "The requested resource was not found." if exc.status_code == 404 else str(exc.detail)
        return JSONResponse(status_code=exc.status_code, content=_error(code, message))

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unexpected error path=%s", request.url.path)
        return JSONResponse(status_code=500, content=_error("INTERNAL_ERROR", "An unexpected internal error occurred."))
