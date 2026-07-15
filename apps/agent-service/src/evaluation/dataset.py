from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from courtroom_domain import CaseFile

DEFAULT_DATASET_VERSION = "domain-eval-v1"
DEFAULT_DATASET_PATH = (
    Path(__file__).resolve().parents[2] / "evals" / "domain_evaluation_dataset.json"
)

CoverageTag = Literal[
    "normal_evidence_backed",
    "contradiction_or_unsupported_claim",
    "adversarial_or_unsafe_content",
]


class ContradictionProbe(BaseModel):
    probe_id: str
    expected_fact: str
    contradicting_claim: str
    should_be_challenged: bool = True


class EvaluationReference(BaseModel):
    expected_phases: list[str] = Field(default_factory=list)
    required_evidence_ids: list[str] = Field(default_factory=list)
    verdict_must_reference_evidence_ids: list[str] = Field(default_factory=list)
    required_fact_phrases: list[str] = Field(default_factory=list)
    forbidden_unsupported_claims: list[str] = Field(default_factory=list)
    contradiction_probes: list[ContradictionProbe] = Field(default_factory=list)
    unsafe_content_policy: str | None = None
    evaluator_notes: str | None = None


class ExpectedSignals(BaseModel):
    should_pass_rule_reference: bool = True
    expected_failure_categories: list[str] = Field(default_factory=list)
    expected_queue_route: str | None = None
    expected_alert: bool = False


class EvaluationCase(BaseModel):
    eval_case_id: str
    dataset_version: str
    active: bool = True
    case_file: CaseFile
    reference: EvaluationReference
    tags: list[str] = Field(default_factory=list)
    expected_signals: ExpectedSignals = Field(default_factory=ExpectedSignals)


class EvaluationDataset(BaseModel):
    dataset_version: str
    cases: list[EvaluationCase]

    @property
    def active_cases(self) -> list[EvaluationCase]:
        return [case for case in self.cases if case.active]


def load_dataset(path: Path = DEFAULT_DATASET_PATH) -> EvaluationDataset:
    with path.open() as handle:
        payload = json.load(handle)
    dataset = EvaluationDataset.model_validate(payload)
    for case in dataset.cases:
        if case.dataset_version != dataset.dataset_version:
            raise ValueError(
                f"{case.eval_case_id} dataset_version does not match dataset"
            )
    return dataset
