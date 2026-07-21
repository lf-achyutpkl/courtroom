from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from courtroom_domain import CaseEditOperation, CaseFile, CardType, SelectedCard


class CaseFileResponse(BaseModel):
    id: UUID
    status: str
    revision: int
    case_file: CaseFile
    created_at: datetime
    updated_at: datetime


class CaseFileListItemResponse(BaseModel):
    id: UUID
    status: str
    revision: int
    case_file: CaseFile
    created_at: datetime
    updated_at: datetime


class ManualMutationRequest(BaseModel):
    action: Literal["add_card", "edit_card", "delete_card"]
    card_type: CardType
    card_id: str | None = None
    content: dict[str, object] | None = None
    expected_revision: int


class ManualMutationResponse(BaseModel):
    operation: CaseEditOperation
    revision: int


class CaseFileMessageRequest(BaseModel):
    message: str
    selected_card: SelectedCard | None = None


class CaseFileMessageResponse(BaseModel):
    id: UUID
    case_file_id: UUID
    role: Literal["human", "ai"]
    content: str
    created_at: datetime
