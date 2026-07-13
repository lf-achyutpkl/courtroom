from pydantic import BaseModel, Field
from typing import Literal, Optional


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


class TranscriptTurn(BaseModel):
    scene: Literal["opening", "direct", "cross", "closing", "ruling", "verdict"]
    speaker_id: str
    text: str
    objection_type: Optional[str] = None
    ruling: Optional[Literal["sustained", "overruled"]] = None
    cited_chunk_ids: Optional[list[str]] = None


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
        description="Short spoken verdict reasoning with inline delivery tags like [measured], [somber], or [firm]."
    )
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    cited_chunk_ids: list[str] = Field(default_factory=list)


class CaseFile(BaseModel):
    case_id: str
    case_type: Literal["criminal", "civil"]
    charge_or_claim: str
    jurisdiction: Literal["US"] = "US"
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
