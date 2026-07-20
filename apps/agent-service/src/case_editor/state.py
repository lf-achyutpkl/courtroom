from __future__ import annotations

from operator import add
from typing import Annotated, Protocol
from uuid import UUID

from courtroom_domain import CaseEditResult
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class StoredCaseFileLike(Protocol):
    case_file: object
    revision: int


class CaseFileStore(Protocol):
    def get(self, case_file_id: UUID) -> StoredCaseFileLike | None: ...

    def apply_operation(
        self,
        case_file_id: UUID,
        operation: object,
        *,
        expected_revision: int,
    ) -> StoredCaseFileLike: ...

    def replace_case_file(
        self,
        case_file_id: UUID,
        case_file: object,
        *,
        expected_revision: int,
        status: str | None = None,
    ) -> StoredCaseFileLike: ...


class CaseEditorState(BaseModel):
    case_file_id: str
    user_message: str
    selected_card_type: str | None = None
    selected_card_id: str | None = None
    messages: Annotated[list[BaseMessage], add] = Field(default_factory=list)
    edit_result: CaseEditResult | None = None
    narration_text: str | None = None
