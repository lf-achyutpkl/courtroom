from operator import add

from pydantic import BaseModel, Field
from typing import Literal, Optional, Annotated

from .types import CaseFile, RulingOutput, TranscriptTurn, VerdictOutput


class TrialState(BaseModel):
    case_file: CaseFile
    prosecution_witness_plan: list[str]
    defense_witness_plan: list[str]
    witness_queue: list[str] = Field(default_factory=list)
    current_witness_id: str | None = None
    examination_phase: Literal["direct", "cross"] = "direct"
    examining_attorney: Literal["prosecution", "defense"]
    turn_count: int = 0
    current_witness_transcript: list[TranscriptTurn] = Field(default_factory=list)
    full_trial_transcript: Annotated[list[TranscriptTurn], add] = Field(
        default_factory=list
    )
    objection_pending: bool = False
    last_objection_type: str | None = None
    last_ruling: Optional[RulingOutput] = None
    active_question_text: str | None = None
    trial_summary: str | None = None
    verdict: Optional[VerdictOutput] = None
    attorney_is_done: bool
