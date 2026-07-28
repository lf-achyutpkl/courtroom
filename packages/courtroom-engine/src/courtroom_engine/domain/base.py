from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DomainModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", validate_assignment=True)
