from __future__ import annotations

from fastapi import FastAPI

from .api.routers.case_files import router as case_files_router
from .api.routers.simulations import router as simulations_router


def create_app() -> FastAPI:
    app = FastAPI(title="Courtroom API Service")
    app.include_router(case_files_router)
    app.include_router(simulations_router)
    return app


app = create_app()
