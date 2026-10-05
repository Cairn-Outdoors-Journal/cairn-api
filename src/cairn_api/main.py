"""Application entry point: ``uvicorn cairn_api.main:app``."""

from fastapi import FastAPI

from cairn_api import __version__
from cairn_api.routers import health


def create_app() -> FastAPI:
    app = FastAPI(
        title="Cairn API",
        version=__version__,
        description=(
            "Accounts, sync coordination, share links and print orders for Cairn. "
            "Journal content never passes through this API: it is encrypted on the phone and "
            "uploaded directly to storage."
        ),
    )
    app.include_router(health.router)
    return app


app = create_app()
