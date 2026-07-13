from operator import add

from pydantic import BaseModel, Field
from typing import Annotated, Optional

from .types import CaseFile, TranscriptTurn, VerdictOutput


class TrialState(BaseModel):
    case_file: CaseFile
    prosecution_witness_plan: list[str]
    defense_witness_plan: list[str]
    witness_queue: list[str] = Field(default_factory=list)
    current_witness_id: str | None = None
    full_trial_transcript: Annotated[list[TranscriptTurn], add] = Field(
        default_factory=list
    )
    trial_summary: str | None = None
    verdict: Optional[VerdictOutput] = None
