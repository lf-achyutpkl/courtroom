from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from ...api.deps import (
    get_case_file_repository,
    get_simulation_queue,
    get_simulation_run_repository,
)
from ...presenters.simulations import (
    build_simulation_catalog_item,
    build_simulation_playback_response,
)
from ...repositories.case_files import CaseFileRepository
from ...queue.simulation_pipeline import SimulationQueue
from ...repositories.simulation_runs import (
    DuplicateSimulationRunError,
    SimulationRunRepository,
    StoredSimulationRun,
)
from ...schemas.simulations import (
    SimulationRunCatalogItemResponse,
    SimulationRunPlaybackResponse,
    StartSimulationRequest,
    StartSimulationResponse,
)


router = APIRouter()


def _simulation_response_from_record(
    record: StoredSimulationRun,
) -> StartSimulationResponse:
    return StartSimulationResponse(
        simulation_run_id=record.id,
        case_file_id=record.case_file_id,
        status=record.status,
    )


@router.post(
    "/start-simulation",
    response_model=StartSimulationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_simulation(
    request: StartSimulationRequest,
    case_file_repository: CaseFileRepository = Depends(get_case_file_repository),
    run_repository: SimulationRunRepository = Depends(get_simulation_run_repository),
    queue: SimulationQueue = Depends(get_simulation_queue),
) -> StartSimulationResponse:
    case_file = case_file_repository.get(request.case_file_id)
    if case_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case file not found.",
        )
    if case_file.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Simulation has already been started for this case file.",
        )

    try:
        case_file_repository.replace_case_file(
            request.case_file_id,
            case_file.case_file,
            expected_revision=case_file.revision,
            status="simulation_started",
        )
        run = run_repository.create_pending(request.case_file_id)
    except DuplicateSimulationRunError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Simulation has already been started for this case file.",
        ) from exc
    try:
        queue.enqueue_simulation(run.id, request.case_file_id)
    except Exception as exc:
        run_repository.mark_failed(run.id, f"Failed to enqueue simulation: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Simulation could not be queued.",
        ) from exc
    return _simulation_response_from_record(run)


@router.get(
    "/simulation-runs",
    response_model=list[SimulationRunCatalogItemResponse],
)
def list_simulation_runs(
    case_file_repository: CaseFileRepository = Depends(get_case_file_repository),
    run_repository: SimulationRunRepository = Depends(get_simulation_run_repository),
) -> list[SimulationRunCatalogItemResponse]:
    catalog: list[SimulationRunCatalogItemResponse] = []

    for run in run_repository.list_for_dashboard():
        case_file = case_file_repository.get(run.case_file_id)
        if case_file is None:
            continue

        try:
            catalog.append(build_simulation_catalog_item(run, case_file))
        except ValueError:
            continue

    return catalog


@router.get(
    "/simulation-runs/{simulation_run_id}/playback",
    response_model=SimulationRunPlaybackResponse,
)
def get_simulation_run_playback(
    simulation_run_id: str,
    case_file_repository: CaseFileRepository = Depends(get_case_file_repository),
    run_repository: SimulationRunRepository = Depends(get_simulation_run_repository),
) -> SimulationRunPlaybackResponse:
    try:
        simulation_run_uuid = UUID(simulation_run_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation run not found.",
        ) from exc

    run = run_repository.get(simulation_run_uuid)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation run not found.",
        )

    if run.status != "completed" or not run.audio_manifest:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Simulation run playback is not available.",
        )

    case_file = case_file_repository.get(run.case_file_id)
    if case_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case file not found.",
        )

    try:
        return build_simulation_playback_response(run, case_file)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
