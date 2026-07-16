from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class SimulationJob(BaseModel):
    simulation_run_id: UUID
    case_file_id: UUID
