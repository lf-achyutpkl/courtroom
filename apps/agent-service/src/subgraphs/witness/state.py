from operator import add
from typing import Literal, Optional

from pydantic import BaseModel, Field
from typing import Annotated

from ...utils.types import CaseFile, NodeTelemetry, RulingOutput, TranscriptTurn


class WitnessExaminationState(BaseModel):
    case_file: CaseFile
    run_id: str | None = None
    current_witness_id: str
    examination_phase: Literal["direct", "cross"] = "direct"
    examining_attorney: Literal["prosecution", "defense"]
    turn_count: int = 0
    current_witness_transcript: list[TranscriptTurn] = Field(default_factory=list)
    node_telemetry: Annotated[list[NodeTelemetry], add] = Field(default_factory=list)
    objection_pending: bool = False
    last_objection_type: str | None = None
    last_ruling: Optional[RulingOutput] = None
    active_question_text: str | None = None
    attorney_is_done: bool = False
