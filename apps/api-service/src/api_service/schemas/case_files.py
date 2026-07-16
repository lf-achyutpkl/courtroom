from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from courtroom_domain import CaseFile


class CaseFileResponse(BaseModel):
    id: UUID
    case_file: CaseFile
    created_at: datetime
