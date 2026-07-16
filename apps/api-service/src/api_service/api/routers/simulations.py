from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ...api.deps import (
    get_case_file_repository,
    get_simulation_queue,
    get_simulation_run_repository,
)
from ...repositories.case_files import CaseFileRepository
from ...repositories.simulation_runs import (
    SimulationRunRepository,
    StoredSimulationRun,
)
from ...schemas.simulations import StartSimulationRequest, StartSimulationResponse
from ...services.simulation_queue import SimulationQueue


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
