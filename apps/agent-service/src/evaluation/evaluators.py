from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.evaluation.dataset import EvaluationCase, EvaluationReference
from courtroom_domain import TranscriptTurn
from src.utils.types import RunTrialResponse

EVALUATOR_VERSION = "v1"
Severity = Literal["info", "low", "medium", "high", "critical"]


class EvaluatorFinding(BaseModel):
    code: str
    message: str
    severity: Severity = "medium"
    related_turn_ids: list[int] = Field(default_factory=list)
    related_evidence_ids: list[str] = Field(default_factory=list)


class EvaluatorResult(BaseModel):
    evaluator_name: str
    version: str = EVALUATOR_VERSION
    passed: bool
    severity: Severity = "info"
    findings: list[EvaluatorFinding] = Field(default_factory=list)
    related_turn_ids: list[int] = Field(default_factory=list)
    related_evidence_ids: list[str] = Field(default_factory=list)
    summary: str


def _all_text(transcript: list[TranscriptTurn]) -> str:
    return " ".join(turn.text for turn in transcript).lower()


def _turn_ids_with_phrase(
    transcript: list[TranscriptTurn], phrase: str
) -> list[int]:
    phrase_lower = phrase.lower()
    return [
        index
        for index, turn in enumerate(transcript)
        if phrase_lower in turn.text.lower()
    ]


def _result(
    evaluator_name: str,
    findings: list[EvaluatorFinding],
    *,
    pass_summary: str,
) -> EvaluatorResult:
    if not findings:
        return EvaluatorResult(
            evaluator_name=evaluator_name,
            passed=True,
            summary=pass_summary,
        )
    severity_rank = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    max_severity = max(findings, key=lambda item: severity_rank[item.severity]).severity
    return EvaluatorResult(
        evaluator_name=evaluator_name,
        passed=False,
        severity=max_severity,
        findings=findings,
        related_turn_ids=sorted(
            {turn_id for finding in findings for turn_id in finding.related_turn_ids}
        ),
        related_evidence_ids=sorted(
            {
                evidence_id
                for finding in findings
                for evidence_id in finding.related_evidence_ids
            }
        ),
        summary=f"{evaluator_name} found {len(findings)} issue(s).",
    )


def check_evidence_references(
    transcript: list[TranscriptTurn],
    reference: EvaluationReference,
    valid_evidence_ids: set[str],
) -> EvaluatorResult:
    findings: list[EvaluatorFinding] = []
    for index, turn in enumerate(transcript):
        for evidence_id in turn.cited_chunk_ids or []:
            if evidence_id not in valid_evidence_ids:
                findings.append(
                    EvaluatorFinding(
                        code="unsupported_evidence_reference",
                        message=f"Turn {index} cites unknown evidence id {evidence_id}.",
                        severity="high",
                        related_turn_ids=[index],
                        related_evidence_ids=[evidence_id],
                    )
                )

    cited_evidence_ids = {
        evidence_id
        for turn in transcript
        for evidence_id in (turn.cited_chunk_ids or [])
    }
    for evidence_id in reference.required_evidence_ids:
        if evidence_id not in cited_evidence_ids:
            findings.append(
                EvaluatorFinding(
                    code="missing_required_evidence",
                    message=f"Required evidence {evidence_id} was not cited.",
                    severity="medium",
                    related_evidence_ids=[evidence_id],
                )
            )

    return _result(
        "evidence_reference",
        findings,
        pass_summary="Evidence references are supported and required evidence appears.",
    )


def check_verdict_support(
    transcript: list[TranscriptTurn],
    reference: EvaluationReference,
) -> EvaluatorResult:
    findings: list[EvaluatorFinding] = []
    verdict_turns = [
        (index, turn) for index, turn in enumerate(transcript) if turn.scene == "verdict"
    ]
    verdict_citations = {
        evidence_id
        for _, turn in verdict_turns
        for evidence_id in (turn.cited_chunk_ids or [])
    }
    verdict_text = " ".join(turn.text for _, turn in verdict_turns).lower()

    for evidence_id in reference.verdict_must_reference_evidence_ids:
        if evidence_id not in verdict_citations:
            findings.append(
                EvaluatorFinding(
                    code="verdict_missing_evidence_support",
                    message=f"Verdict did not cite required evidence {evidence_id}.",
                    severity="high",
                    related_turn_ids=[index for index, _ in verdict_turns],
                    related_evidence_ids=[evidence_id],
                )
            )

    for phrase in reference.required_fact_phrases:
        if phrase.lower() not in verdict_text:
            findings.append(
                EvaluatorFinding(
                    code="verdict_missing_required_fact",
                    message=f"Verdict did not reference required fact phrase '{phrase}'.",
                    severity="medium",
                    related_turn_ids=[index for index, _ in verdict_turns],
                )
            )

    return _result(
        "verdict_support",
        findings,
        pass_summary="Verdict reasoning references required evidence and facts.",
    )


def check_contradiction_probes(
    transcript: list[TranscriptTurn],
    reference: EvaluationReference,
) -> EvaluatorResult:
    findings: list[EvaluatorFinding] = []
    text = _all_text(transcript)

    for probe in reference.contradiction_probes:
        if probe.contradicting_claim.lower() not in text:
            continue
        challenge_markers = [
            "contradict",
            "challenge",
            "impeach",
            "but the",
            probe.expected_fact.lower(),
        ]
        if not any(marker in text for marker in challenge_markers):
            findings.append(
                EvaluatorFinding(
                    code="unresolved_contradiction_probe",
                    message=(
                        f"Contradicting claim '{probe.contradicting_claim}' "
                        "appeared without a challenge."
                    ),
                    severity="high",
                    related_turn_ids=_turn_ids_with_phrase(
                        transcript, probe.contradicting_claim
                    ),
                )
            )

    return _result(
        "contradiction_probe",
        findings,
        pass_summary="Contradiction probes are absent or challenged.",
    )


def check_unsupported_legal_claims(
    transcript: list[TranscriptTurn],
    reference: EvaluationReference,
) -> EvaluatorResult:
    findings: list[EvaluatorFinding] = []
    for phrase in reference.forbidden_unsupported_claims:
        turn_ids = _turn_ids_with_phrase(transcript, phrase)
        if turn_ids:
            findings.append(
                EvaluatorFinding(
                    code="unsupported_legal_or_fact_claim",
                    message=f"Transcript contains forbidden unsupported claim '{phrase}'.",
                    severity="high",
                    related_turn_ids=turn_ids,
                )
            )

    return _result(
        "unsupported_claim",
        findings,
        pass_summary="No forbidden unsupported legal or fact claims were found.",
    )


def check_phase_coverage(
    transcript: list[TranscriptTurn],
    reference: EvaluationReference,
) -> EvaluatorResult:
    seen_phases = {turn.scene for turn in transcript}
    findings = [
        EvaluatorFinding(
            code="missing_required_phase",
            message=f"Transcript missing required phase '{phase}'.",
            severity="medium",
        )
        for phase in reference.expected_phases
        if phase not in seen_phases
    ]
    return _result(
        "phase_coverage",
        findings,
        pass_summary="Transcript includes required phases.",
    )


def evaluate_rule_reference(
    *,
    response: RunTrialResponse,
    case: EvaluationCase,
) -> list[EvaluatorResult]:
    if not response.run.deterministic_validation_passed:
        return []

    valid_evidence_ids = {
        evidence.evidence_id for evidence in case.case_file.evidence
    }
    transcript = response.full_trial_transcript
    return [
        check_evidence_references(transcript, case.reference, valid_evidence_ids),
        check_verdict_support(transcript, case.reference),
        check_contradiction_probes(transcript, case.reference),
        check_unsupported_legal_claims(transcript, case.reference),
        check_phase_coverage(transcript, case.reference),
    ]
