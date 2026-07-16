from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class SimulationCompletion(BaseModel):
    simulation_run_id: UUID
    status: Literal["completed", "failed"]
    result: dict[str, object] | None = None
    error_message: str | None = None
