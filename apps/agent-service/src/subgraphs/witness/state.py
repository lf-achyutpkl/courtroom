from typing import Literal, Optional

from pydantic import BaseModel, Field

from ...utils.types import CaseFile, RulingOutput, TranscriptTurn


class WitnessExaminationState(BaseModel):
    case_file: CaseFile
    current_witness_id: str
    examination_phase: Literal["direct", "cross"] = "direct"
    examining_attorney: Literal["prosecution", "defense"]
    turn_count: int = 0
    current_witness_transcript: list[TranscriptTurn] = Field(default_factory=list)
    objection_pending: bool = False
    last_objection_type: str | None = None
    last_ruling: Optional[RulingOutput] = None
    active_question_text: str | None = None
    attorney_is_done: bool = False
