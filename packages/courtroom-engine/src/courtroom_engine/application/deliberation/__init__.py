from __future__ import annotations

from courtroom_engine.domain.case import CaseKind, PartySide
from courtroom_engine.domain.deliberation import (
    BurdenApplication,
    CandidateFinding,
    DeliberationReport,
    ElementEvaluation,
    FindingStatus,
    JudgeRecord,
    LegalQuestion,
    Verdict,
    VerdictOutcome,
    VerdictValidationCode,
    VerdictValidationIssue,
    VerdictValidationResult,
    WitnessCredibilityFinding,
)
from courtroom_engine.domain.evaluation import CitationKind, RecordCitation
from courtroom_engine.domain.events import CourtroomEventType
from courtroom_engine.domain.procedure import EvidenceAdmissionStatus
from courtroom_engine.domain.trial import CompiledCasePackage, TrialRuntimeState
from courtroom_engine.domain.visibility import VisibilityScope


def run_judicial_deliberation(
    *,
    case_package: CompiledCasePackage,
    state: TrialRuntimeState,
) -> DeliberationReport:
    judge_record = build_judge_record(case_package=case_package, state=state)
    legal_questions = identify_legal_questions(case_package)
    element_evaluations = evaluate_elements(
        case_package=case_package,
        judge_record=judge_record,
    )
    credibility_findings = assess_witness_credibility(
        case_package=case_package,
        judge_record=judge_record,
    )
    burden_applications = apply_burden(
        case_package=case_package,
        element_evaluations=element_evaluations,
    )
    candidate_findings = generate_findings(
        element_evaluations=element_evaluations,
        burden_applications=burden_applications,
    )
    challenged_findings = challenge_findings(candidate_findings)
    finalized_findings = tuple(
        finding for finding in challenged_findings if not finding.challenge_messages
    )
    verdict = generate_verdict(
        case_package=case_package,
        finalized_findings=finalized_findings,
    )
    validation = validate_verdict(
        case_package=case_package,
        judge_record=judge_record,
        legal_questions=legal_questions,
        element_evaluations=element_evaluations,
        burden_applications=burden_applications,
        finalized_findings=finalized_findings,
        verdict=verdict,
    )
    return DeliberationReport(
        report_id=f"DLB-{case_package.metadata.case_id}",
        judge_record=judge_record,
        legal_questions=legal_questions,
        element_evaluations=element_evaluations,
        credibility_findings=credibility_findings,
        burden_applications=burden_applications,
        candidate_findings=challenged_findings,
        finalized_findings=finalized_findings,
        verdict=verdict,
        validation=validation,
    )


def build_judge_record(
    *,
    case_package: CompiledCasePackage,
    state: TrialRuntimeState,
) -> JudgeRecord:
    admitted_evidence_ids = tuple(
        record.evidence_id
        for record in state.procedure.evidence_admissions
        if record.status == EvidenceAdmissionStatus.ADMITTED
    ) or state.admitted_evidence_ids
    admitted_evidence = tuple(
        evidence
        for evidence in case_package.evidence
        if evidence.evidence_id in admitted_evidence_ids
    )
    admitted_fact_ids = list(
        dict.fromkeys(
            fact_id
            for evidence in admitted_evidence
            for fact_id in evidence.supports_fact_ids
        )
    )
    admitted_knowledge_atom_ids: list[str] = []
    testimony_event_ids: list[str] = []
    for event in state.events:
        if event.event_type != CourtroomEventType.WITNESS_ANSWERED:
            continue
        testimony_event_ids.append(str(event.event_id))
        for cited_id in event.cited_object_ids:
            atom = next(
                (
                    atom
                    for atom in case_package.witness_knowledge
                    if atom.knowledge_atom_id == cited_id
                ),
                None,
            )
            if atom is None:
                continue
            admitted_knowledge_atom_ids.append(atom.knowledge_atom_id)
            admitted_fact_ids.extend(atom.related_fact_ids)
    ruling_ids = tuple(ruling.ruling_id for ruling in state.procedure.rulings)
    permitted_argument_event_ids = tuple(
        str(event.event_id)
        for event in state.events
        if event.event_type == CourtroomEventType.CLOSING_DELIVERED
    )
    excluded_object_ids = _excluded_from_judge_record(
        case_package=case_package,
        admitted_evidence_ids=admitted_evidence_ids,
        admitted_fact_ids=tuple(dict.fromkeys(admitted_fact_ids)),
    )
    return JudgeRecord(
        record_id=f"JREC-{case_package.metadata.case_id}",
        case_id=case_package.metadata.case_id,
        admitted_evidence_ids=tuple(dict.fromkeys(admitted_evidence_ids)),
        admitted_fact_ids=tuple(dict.fromkeys(admitted_fact_ids)),
        testimony_event_ids=tuple(dict.fromkeys(testimony_event_ids)),
        admitted_knowledge_atom_ids=tuple(dict.fromkeys(admitted_knowledge_atom_ids)),
        ruling_ids=ruling_ids,
        permitted_argument_event_ids=permitted_argument_event_ids,
        excluded_object_ids=excluded_object_ids,
    )


def identify_legal_questions(
    case_package: CompiledCasePackage,
) -> tuple[LegalQuestion, ...]:
    questions: list[LegalQuestion] = []
    for matter in case_package.matters:
        proving_side = matter.elements[0].proving_side if matter.elements else PartySide.PLAINTIFF
        standard = matter.elements[0].burden if matter.elements else "preponderance"
        verdict_options = (
            (VerdictOutcome.GUILTY, VerdictOutcome.NOT_GUILTY)
            if matter.case_kind == CaseKind.CRIMINAL
            else (VerdictOutcome.PLAINTIFF, VerdictOutcome.DEFENSE)
        )
        questions.append(
            LegalQuestion(
                question_id=f"LQ-{matter.matter_id}",
                matter_id=matter.matter_id,
                element_ids=tuple(element.element_id for element in matter.elements),
                burden_holder=proving_side,
                standard=standard,
                verdict_options=verdict_options,
            )
        )
    return tuple(questions)


def evaluate_elements(
    *,
    case_package: CompiledCasePackage,
    judge_record: JudgeRecord,
) -> tuple[ElementEvaluation, ...]:
    admitted_fact_ids = set(judge_record.admitted_fact_ids)
    admitted_evidence_ids = set(judge_record.admitted_evidence_ids)
    evaluations: list[ElementEvaluation] = []
    for matter in case_package.matters:
        for element in matter.elements:
            supporting_citations: list[RecordCitation] = []
            contrary_citations: list[RecordCitation] = []
            for fact in case_package.facts:
                if (
                    fact.fact_id in admitted_fact_ids
                    and element.element_id in fact.supports_element_ids
                ):
                    supporting_citations.append(
                        RecordCitation(kind=CitationKind.FACT, record_id=fact.fact_id)
                    )
            for evidence in case_package.evidence:
                if evidence.evidence_id not in admitted_evidence_ids:
                    continue
                if any(fact_id in admitted_fact_ids for fact_id in evidence.supports_fact_ids):
                    supporting_citations.append(
                        RecordCitation(
                            kind=CitationKind.EVIDENCE,
                            record_id=evidence.evidence_id,
                        )
                    )
            status = (
                FindingStatus.PROVED
                if supporting_citations
                else FindingStatus.NOT_PROVED
            )
            evaluations.append(
                ElementEvaluation(
                    element_id=element.element_id,
                    matter_id=matter.matter_id,
                    burden_holder=element.proving_side,
                    standard=element.burden,
                    supporting_citations=tuple(dict.fromkeys(supporting_citations)),
                    contrary_citations=tuple(contrary_citations),
                    unresolved_gaps=()
                    if supporting_citations
                    else (f"No admitted support for {element.element_id}.",),
                    status=status,
                    confidence=0.82 if supporting_citations else 0.7,
                )
            )
    return tuple(evaluations)


def assess_witness_credibility(
    *,
    case_package: CompiledCasePackage,
    judge_record: JudgeRecord,
) -> tuple[WitnessCredibilityFinding, ...]:
    findings: list[WitnessCredibilityFinding] = []
    for witness in case_package.witnesses:
        atom_citations = tuple(
            RecordCitation(kind=CitationKind.KNOWLEDGE_ATOM, record_id=atom_id)
            for atom_id in judge_record.admitted_knowledge_atom_ids
            if any(
                atom.knowledge_atom_id == atom_id and atom.witness_id == witness.witness_id
                for atom in case_package.witness_knowledge
            )
        )
        if not atom_citations:
            continue
        findings.append(
            WitnessCredibilityFinding(
                witness_id=witness.witness_id,
                finding_id=f"CRD-{witness.witness_id}",
                summary="Credibility assessed from admitted testimony.",
                supporting_citations=atom_citations,
                confidence=0.72,
            )
        )
    return tuple(findings)


def apply_burden(
    *,
    case_package: CompiledCasePackage,
    element_evaluations: tuple[ElementEvaluation, ...],
) -> tuple[BurdenApplication, ...]:
    applications: list[BurdenApplication] = []
    for evaluation in element_evaluations:
        conclusion = (
            f"{evaluation.burden_holder.value} satisfied {evaluation.standard}."
            if evaluation.status == FindingStatus.PROVED
            else f"{evaluation.burden_holder.value} did not satisfy {evaluation.standard}."
        )
        applications.append(
            BurdenApplication(
                application_id=f"BUR-{evaluation.element_id}",
                element_id=evaluation.element_id,
                matter_id=evaluation.matter_id,
                burden_holder=evaluation.burden_holder,
                standard=evaluation.standard,
                element_status=evaluation.status,
                conclusion=conclusion,
                citations=evaluation.supporting_citations
                or (
                    RecordCitation(
                        kind=CitationKind.ELEMENT,
                        record_id=evaluation.element_id,
                        note="No admitted support found.",
                    ),
                ),
            )
        )
    return tuple(applications)


def generate_findings(
    *,
    element_evaluations: tuple[ElementEvaluation, ...],
    burden_applications: tuple[BurdenApplication, ...],
) -> tuple[CandidateFinding, ...]:
    burden_by_element = {
        application.element_id: application for application in burden_applications
    }
    findings: list[CandidateFinding] = []
    for evaluation in element_evaluations:
        application = burden_by_element[evaluation.element_id]
        findings.append(
            CandidateFinding(
                finding_id=f"FND-{evaluation.element_id}",
                matter_id=evaluation.matter_id,
                element_id=evaluation.element_id,
                status=evaluation.status,
                explanation=application.conclusion,
                citations=application.citations,
            )
        )
    return tuple(findings)


def challenge_findings(
    findings: tuple[CandidateFinding, ...],
) -> tuple[CandidateFinding, ...]:
    challenged: list[CandidateFinding] = []
    for finding in findings:
        messages: tuple[str, ...] = ()
        if finding.status == FindingStatus.PROVED and not finding.citations:
            messages = ("Proved finding lacks admitted-record citations.",)
        challenged.append(
            finding.model_copy(
                update={
                    "challenged": True,
                    "challenge_messages": messages,
                }
            )
        )
    return tuple(challenged)


def generate_verdict(
    *,
    case_package: CompiledCasePackage,
    finalized_findings: tuple[CandidateFinding, ...],
) -> Verdict:
    matter = case_package.matters[0]
    matter_findings = [
        finding for finding in finalized_findings if finding.matter_id == matter.matter_id
    ]
    all_proved = bool(matter_findings) and all(
        finding.status == FindingStatus.PROVED for finding in matter_findings
    )
    if matter.case_kind == CaseKind.CRIMINAL:
        outcome = VerdictOutcome.GUILTY if all_proved else VerdictOutcome.NOT_GUILTY
    else:
        outcome = VerdictOutcome.PLAINTIFF if all_proved else VerdictOutcome.DEFENSE
    citations = tuple(
        citation for finding in matter_findings for citation in finding.citations
    )
    return Verdict(
        verdict_id=f"VER-{matter.matter_id}",
        outcome=outcome,
        matter_id=matter.matter_id,
        explanation=f"Verdict for {outcome.value} based on finalized element findings.",
        finding_ids=tuple(finding.finding_id for finding in matter_findings),
        citations=tuple(dict.fromkeys(citations)),
    )


def validate_verdict(
    *,
    case_package: CompiledCasePackage,
    judge_record: JudgeRecord,
    legal_questions: tuple[LegalQuestion, ...],
    element_evaluations: tuple[ElementEvaluation, ...],
    burden_applications: tuple[BurdenApplication, ...],
    finalized_findings: tuple[CandidateFinding, ...],
    verdict: Verdict,
) -> VerdictValidationResult:
    issues: list[VerdictValidationIssue] = []
    element_ids = {
        element.element_id for matter in case_package.matters for element in matter.elements
    }
    evaluated_ids = {evaluation.element_id for evaluation in element_evaluations}
    finding_by_element = {finding.element_id: finding for finding in finalized_findings}
    for element_id in sorted(element_ids - evaluated_ids):
        issues.append(
            VerdictValidationIssue(
                code=VerdictValidationCode.MISSING_ELEMENT_FINDING,
                message=f"Missing element evaluation for {element_id}.",
                citations=(RecordCitation(kind=CitationKind.ELEMENT, record_id=element_id),),
            )
        )
    for element_id in sorted(element_ids - set(finding_by_element)):
        issues.append(
            VerdictValidationIssue(
                code=VerdictValidationCode.MISSING_ELEMENT_FINDING,
                message=f"Missing finalized finding for {element_id}.",
                citations=(RecordCitation(kind=CitationKind.ELEMENT, record_id=element_id),),
            )
        )
    expected_burdens = {
        element.element_id: element.burden
        for matter in case_package.matters
        for element in matter.elements
    }
    for application in burden_applications:
        if expected_burdens.get(application.element_id) != application.standard:
            issues.append(
                VerdictValidationIssue(
                    code=VerdictValidationCode.BURDEN_MISMATCH,
                    message=f"Burden mismatch for {application.element_id}.",
                    citations=(
                        RecordCitation(
                            kind=CitationKind.ELEMENT,
                            record_id=application.element_id,
                        ),
                    ),
                )
            )
    for finding in finalized_findings:
        if finding.status == FindingStatus.PROVED and not finding.citations:
            issues.append(
                VerdictValidationIssue(
                    code=VerdictValidationCode.UNSUPPORTED_DISPOSITIVE_FINDING,
                    message=f"Finding {finding.finding_id} is unsupported.",
                    citations=(
                        RecordCitation(
                            kind=CitationKind.FINDING,
                            record_id=finding.finding_id,
                        ),
                    ),
                )
            )
        for citation in finding.citations:
            if (
                citation.kind == CitationKind.EVIDENCE
                and citation.record_id not in judge_record.admitted_evidence_ids
            ):
                issues.append(
                    VerdictValidationIssue(
                        code=VerdictValidationCode.EXCLUDED_EVIDENCE_RELIANCE,
                        message=f"Finding {finding.finding_id} cites unadmitted evidence.",
                        citations=(citation,),
                    )
                )
            if citation.record_id in judge_record.excluded_object_ids:
                issues.append(
                    VerdictValidationIssue(
                        code=VerdictValidationCode.HIDDEN_RECORD_RELIANCE,
                        message=f"Finding {finding.finding_id} cites excluded material.",
                        citations=(citation,),
                    )
                )
    unresolved_questions = [
        question
        for question in legal_questions
        if any(element_id not in finding_by_element for element_id in question.element_ids)
    ]
    for question in unresolved_questions:
        issues.append(
            VerdictValidationIssue(
                code=VerdictValidationCode.UNRESOLVED_LEGAL_QUESTION,
                message=f"Legal question {question.question_id} is unresolved.",
                citations=(
                    RecordCitation(
                        kind=CitationKind.ELEMENT,
                        record_id=question.question_id,
                    ),
                ),
            )
        )
    question = next(
        (question for question in legal_questions if question.matter_id == verdict.matter_id),
        None,
    )
    if question is None or verdict.outcome not in question.verdict_options:
        issues.append(
            VerdictValidationIssue(
                code=VerdictValidationCode.INVALID_VERDICT_OPTION,
                message=f"Verdict outcome {verdict.outcome.value} is not permitted.",
                citations=(
                    RecordCitation(
                        kind=CitationKind.VERDICT,
                        record_id=verdict.verdict_id,
                    ),
                ),
            )
        )
    return VerdictValidationResult(valid=not issues, issues=tuple(issues))


def _excluded_from_judge_record(
    *,
    case_package: CompiledCasePackage,
    admitted_evidence_ids: tuple[str, ...],
    admitted_fact_ids: tuple[str, ...],
) -> tuple[str, ...]:
    excluded: list[str] = []
    admitted_evidence_set = set(admitted_evidence_ids)
    admitted_fact_set = set(admitted_fact_ids)
    for evidence in case_package.evidence:
        if evidence.evidence_id not in admitted_evidence_set:
            excluded.append(evidence.evidence_id)
    for fact in case_package.facts:
        if fact.fact_id in admitted_fact_set:
            continue
        if fact.visibility != VisibilityScope.PUBLIC_CASE:
            excluded.append(fact.fact_id)
    for contradiction in case_package.intelligence.contradiction_graph.contradictions:
        excluded.append(contradiction.contradiction_id)
    coaching_references = (
        case_package.private_truth.coaching_references
        if case_package.private_truth
        else ()
    )
    for strategy in coaching_references:
        excluded.append(strategy.objective_id)
    return tuple(dict.fromkeys(excluded))
