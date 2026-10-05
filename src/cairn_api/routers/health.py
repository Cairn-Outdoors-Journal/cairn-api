"""Liveness and readiness checks, used by Fly.io and uptime monitoring."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

from cairn_api import __version__, db
from cairn_api.config import Settings, get_settings

router = APIRouter(tags=["health"])


class Liveness(BaseModel):
    status: Literal["ok"]
    version: str


class Readiness(BaseModel):
    status: Literal["ok", "unavailable"]
    database: Literal["ok", "unreachable", "not_configured"]


@router.get("/healthz")
def healthz() -> Liveness:
    """The process is up. Never touches dependencies."""
    return Liveness(status="ok", version=__version__)


@router.get("/readyz", responses={503: {"model": Readiness}})
def readyz(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Readiness:
    """The service can handle requests: its database answers."""
    if settings.database_url is None:
        return Readiness(status="ok", database="not_configured")
    if db.ping(settings.database_url):
        return Readiness(status="ok", database="ok")
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return Readiness(status="unavailable", database="unreachable")
