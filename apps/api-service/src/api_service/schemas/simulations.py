from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from ..repositories.simulation_runs import SimulationRunStatus


class StartSimulationRequest(BaseModel):
    case_file_id: UUID


class StartSimulationResponse(BaseModel):
    simulation_run_id: UUID
    case_file_id: UUID
    status: SimulationRunStatus
