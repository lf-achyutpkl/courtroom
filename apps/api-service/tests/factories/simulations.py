from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from api_service.repositories.simulation_runs import StoredSimulationRun


def build_stored_simulation_run(
    case_file_id: UUID,
    status: str = "pending",
) -> StoredSimulationRun:
    return StoredSimulationRun(
        id=uuid4(),
        case_file_id=case_file_id,
        status=status,  # type: ignore[arg-type]
        result=None,
        error_message=None,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        started_at=None,
        completed_at=None,
    )
