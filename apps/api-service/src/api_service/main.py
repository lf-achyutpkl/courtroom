from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel

from courtroom_domain import CaseFile

from .config import get_database_url, get_redis_url
from .dummy_case_file import build_dummy_case_file
from .repository import CaseFileRepository, PostgresCaseFileRepository, StoredCaseFile
from .simulation_queue import RqSimulationQueue, SimulationQueue
from .simulation_repository import (
    PostgresSimulationRunRepository,
    SimulationRunRepository,
    SimulationRunStatus,
    StoredSimulationRun,
)


class CaseFileResponse(BaseModel):
    id: UUID
    case_file: CaseFile
    created_at: datetime


class StartSimulationRequest(BaseModel):
    case_file_id: UUID


class StartSimulationResponse(BaseModel):
    simulation_run_id: UUID
    case_file_id: UUID
    status: SimulationRunStatus


def _response_from_record(record: StoredCaseFile) -> CaseFileResponse:
    return CaseFileResponse(
        id=record.id,
        case_file=record.case_file,
        created_at=record.created_at,
    )


def _simulation_response_from_record(
    record: StoredSimulationRun,
) -> StartSimulationResponse:
    return StartSimulationResponse(
        simulation_run_id=record.id,
        case_file_id=record.case_file_id,
        status=record.status,
    )


def get_case_file_repository() -> CaseFileRepository:
    return PostgresCaseFileRepository(get_database_url())


def get_simulation_run_repository() -> SimulationRunRepository:
    return PostgresSimulationRunRepository(get_database_url())


def get_simulation_queue() -> SimulationQueue:
    return RqSimulationQueue(get_redis_url())


def create_app(
    repository: CaseFileRepository | None = None,
    simulation_repository: SimulationRunRepository | None = None,
    simulation_queue: SimulationQueue | None = None,
) -> FastAPI:
    app = FastAPI(title="Courtroom API Service")

    def repository_dependency() -> CaseFileRepository:
        return repository if repository is not None else get_case_file_repository()

    def simulation_repository_dependency() -> SimulationRunRepository:
        return (
            simulation_repository
            if simulation_repository is not None
            else get_simulation_run_repository()
        )

    def simulation_queue_dependency() -> SimulationQueue:
        return simulation_queue if simulation_queue is not None else get_simulation_queue()

    @app.post(
        "/case-files",
        response_model=CaseFileResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_case_file(
        case_file_repository: CaseFileRepository = Depends(repository_dependency),
    ) -> CaseFileResponse:
        case_file = build_dummy_case_file()
        record = case_file_repository.create(case_file)
        return _response_from_record(record)

    @app.get("/case-files/{case_file_id}", response_model=CaseFileResponse)
    def get_case_file(
        case_file_id: UUID,
        case_file_repository: CaseFileRepository = Depends(repository_dependency),
    ) -> CaseFileResponse:
        record = case_file_repository.get(case_file_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case file not found.",
            )
        return _response_from_record(record)

    @app.post(
        "/start-simulation",
        response_model=StartSimulationResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    def start_simulation(
        request: StartSimulationRequest,
        case_file_repository: CaseFileRepository = Depends(repository_dependency),
        run_repository: SimulationRunRepository = Depends(
            simulation_repository_dependency
        ),
        queue: SimulationQueue = Depends(simulation_queue_dependency),
    ) -> StartSimulationResponse:
        case_file = case_file_repository.get(request.case_file_id)
        if case_file is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case file not found.",
            )

        run = run_repository.create_pending(request.case_file_id)
        try:
            queue.enqueue_simulation(run.id, request.case_file_id)
        except Exception as exc:
            run_repository.mark_failed(run.id, f"Failed to enqueue simulation: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Simulation could not be queued.",
            ) from exc
        return _simulation_response_from_record(run)

    return app


app = create_app()
