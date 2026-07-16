from pydantic import BaseModel, Field
from typing import Literal, Optional

from courtroom_domain import (
    CaseFile,
    NodeTelemetry,
    TranscriptTurn,
    WitnessProfile,
)


class RunMetadata(BaseModel):
    """Stable metadata envelope for one generated trial run."""

    run_id: str = Field(description="Stable identifier for this trial run.")
    case_id: str = Field(description="Case identifier from the input case file.")
    graph_version: str = Field(description="Version label for the trial graph.")
    prompt_version: str = Field(description="Version label for prompt templates.")
    model_name: str = Field(description="Primary model used for most trial nodes.")
    judge_model_name: str = Field(
        description="Model used for judge/ruling/verdict-oriented nodes."
    )
    environment: str = "local"
    langsmith_trace_id: Optional[str] = None
    deterministic_validation_passed: bool = True
    started_at: str = Field(description="Run start time in UTC ISO-8601 format.")
    completed_at: str = Field(description="Run end time in UTC ISO-8601 format.")
    duration_ms: int = Field(description="Elapsed runtime for the full trial run.")


class RunTrialRequest(BaseModel):
    case_file: "CaseFile"


class RunTrialResponse(BaseModel):
    full_trial_transcript: list[TranscriptTurn]
    # Added as a separate object so callers can correlate outputs with traces and evals.
    run: RunMetadata


class RulingOutput(BaseModel):
    decision: Literal["sustained", "overruled"]
    reasoning: str = Field(
        description="Short spoken judicial reasoning with inline delivery tags like [measured], [firm], or [calm]."
    )
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    cited_chunk_ids: list[str] = Field(default_factory=list)


class WitnessPlan(BaseModel):
    witness_ids: list[str] = Field(
        description="Ordered witness_ids to call. Empty list is valid for defense."
    )
    reasoning: str = Field(description="Internal rationale, never shown at trial.")


class OpeningStatement(BaseModel):
    statement: str = Field(
        description="Short spoken courtroom statement with inline delivery tags like [steady], [firm], or [measured]."
    )


class ExaminationQuestion(BaseModel):
    question_text: str
    references_evidence_id: Optional[str] = None
    is_final: bool = Field(
        default=False,
        description="True if this attorney has no more questions for this witness in this phase.",
    )


class ObjectionDecision(BaseModel):
    objection: bool
    objection_type: Optional[
        Literal[
            "hearsay",
            "leading",
            "relevance",
            "speculation",
            "character_evidence",
            "argumentative",
        ]
    ] = None
    reasoning: str


class WitnessAnswer(BaseModel):
    answer_text: str = Field(
        description="Short spoken witness answer with inline delivery tags like [nervous], [careful], or [flat]."
    )


class TrialSummary(BaseModel):
    summary_text: str


class ClosingArgument(BaseModel):
    statement: str = Field(
        description="Short spoken closing argument with inline delivery tags like [firm], [controlled], or [urgent]."
    )
