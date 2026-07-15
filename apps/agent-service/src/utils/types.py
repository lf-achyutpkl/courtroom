from pydantic import BaseModel, Field
from typing import Literal, Optional


class NodeTelemetry(BaseModel):
    """Structured telemetry for one graph node execution."""

    node_name: str
    stage: Literal["trial", "witness"]
    started_at: str
    completed_at: str
    duration_ms: int
    phase: Optional[str] = None
    witness_id: Optional[str] = None
    model_name: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None
    cache_write_tokens: Optional[int] = None
    parse_success: Optional[bool] = None
    error_type: Optional[str] = None


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


class Parties(BaseModel):
    plaintiff_or_prosecution: str
    defendant: str


class Evidence(BaseModel):
    evidence_id: str
    description: str
    submitted_by: Literal["prosecution", "defense"]


class WitnessProfile(BaseModel):
    witness_id: str
    name: str
    persona: str
    called_by: Literal["prosecution", "defense"]
    knowledge_scope: str
    contradicts: str | None = None


class CaseJurisdiction(BaseModel):
    country: Literal["US"] = "US"
    state: Literal["California"] = "California"
    court: Literal["Superior Court"] = "Superior Court"
    trial_type: Literal["jury"] = "jury"


class TranscriptTurn(BaseModel):
    scene: Literal[
        "opening", "direct", "cross", "objection", "closing", "ruling", "verdict"
    ]
    speaker_id: str
    text: str
    objection_type: Optional[str] = None
    ruling: Optional[Literal["sustained", "overruled"]] = None
    cited_chunk_ids: Optional[list[str]] = None


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


class VerdictOutput(BaseModel):
    outcome: Literal["guilty", "not guilty", "liable", "not liable"]
    reasoning: str = Field(
        description=(
            "Short spoken verdict reasoning with inline delivery tags like [measured], "
            "[somber], or [firm]. It must name the decisive facts and explain how "
            "the cited evidence supports the outcome."
        )
    )
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    cited_chunk_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Evidence IDs from the case file that directly support the verdict. "
            "Include every decisive evidence_id used in the reasoning, and do not "
            "invent IDs."
        ),
    )


class CaseFile(BaseModel):
    case_id: str
    case_type: Literal["criminal", "civil"]
    charge_or_claim: str
    jurisdiction: CaseJurisdiction = Field(default_factory=CaseJurisdiction)
    parties: Parties
    ground_truth: str
    disputed_facts: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    witnesses: list[WitnessProfile] = Field(default_factory=list)


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
