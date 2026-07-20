from operator import add
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field


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


class DisputedFact(BaseModel):
    fact_id: str
    text: str


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
    case_title: str
    case_type: Literal["criminal", "civil"]
    charge_or_claim: str
    jurisdiction: CaseJurisdiction = Field(default_factory=CaseJurisdiction)
    parties: Parties
    ground_truth: str
    disputed_facts: list[DisputedFact] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    witnesses: list[WitnessProfile] = Field(default_factory=list)


class TrialState(BaseModel):
    case_file: CaseFile
    run_id: str | None = None
    run_started_at: str | None = None
    prosecution_witness_plan: list[str] = Field(default_factory=list)
    defense_witness_plan: list[str] = Field(default_factory=list)
    witness_queue: list[str] = Field(default_factory=list)
    current_witness_id: str | None = None
    full_trial_transcript: Annotated[list[TranscriptTurn], add] = Field(
        default_factory=list
    )
    node_telemetry: Annotated[list[NodeTelemetry], add] = Field(default_factory=list)
    trial_summary: str | None = None
    verdict: Optional[VerdictOutput] = None
