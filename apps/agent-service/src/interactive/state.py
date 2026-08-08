"""State owned by the checkpointed AI-vs-human trial graph."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from ..utils import types
from ..utils.state import TrialState


class InteractiveTrialState(TrialState):
    """Trial state plus the durable state of the active witness examination.

    These fields intentionally belong only to the interactive graph.  The
    existing AI-vs-AI graph continues to use ``TrialState`` and its existing
    witness subgraph unchanged.
    """

    examination_phase: Literal["direct", "cross"] = "direct"
    examining_attorney: Literal["prosecution", "defense"] | None = None
    turn_count: int = 0
    current_witness_transcript: list[types.TranscriptTurn] = Field(default_factory=list)
    objection_pending: bool = False
    last_objection_type: str | None = None
    last_objection_text: str | None = None
    last_ruling: types.RulingOutput | None = None
    active_question_text: str | None = None
    attorney_is_done: bool = False
