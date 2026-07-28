from __future__ import annotations

from pydantic import Field

from courtroom_engine.application.planning import (
    build_question_execution_brief,
    build_tactical_action_plan,
)
from courtroom_engine.context import QuestionExecutionBriefDTO, TacticalActionPlanDTO
from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.events import CourtroomEvent, CourtroomEventType
from courtroom_engine.domain.procedure import AnswerValidationStatus, ExaminationMode
from courtroom_engine.domain.strategy import ObjectiveStatus, PartyStrategy
from courtroom_engine.domain.trial import CompiledCasePackage, TrialRuntimeState


class WitnessAnswerValidation(DomainModel):
    status: AnswerValidationStatus
    supported_knowledge_ids: tuple[str, ...] = ()
    contradiction_ids: tuple[str, ...] = ()
    message: str


class WitnessExaminationOutput(DomainModel):
    examination_id: str
    witness_id: str
    mode: ExaminationMode
    objective_id: str
    tactical_action: TacticalActionPlanDTO
    question_brief: QuestionExecutionBriefDTO
    question_text: str
    answer_text: str
    answer_validation: WitnessAnswerValidation
    objective_status: ObjectiveStatus
    event_summaries: tuple[str, ...] = ()
    events: tuple[CourtroomEvent, ...] = Field(default_factory=tuple)


def run_witness_examination(
    *,
    case_package: CompiledCasePackage,
    state: TrialRuntimeState,
    strategy: PartyStrategy,
    witness_id: str,
    mode: ExaminationMode = ExaminationMode.DIRECT,
) -> WitnessExaminationOutput:
    action = build_tactical_action_plan(strategy, witness_id)
    brief = build_question_execution_brief(action)
    question = _generate_question(brief)
    answer = _deterministic_answer(case_package, brief)
    validation = validate_witness_answer(
        case_package=case_package,
        witness_id=witness_id,
        answer_text=answer,
        allowed_fact_ids=brief.allowed_fact_ids,
    )
    objective_status = (
        ObjectiveStatus.SATISFIED
        if validation.status
        in {
            AnswerValidationStatus.SUPPORTED,
            AnswerValidationStatus.INTENTIONAL_CONTRADICTION,
        }
        else ObjectiveStatus.ACTIVE
    )
    summaries = (
        f"Question asked of {witness_id} for {brief.objective_id}.",
        f"Witness answer validation: {validation.status.value}.",
        f"Objective {brief.objective_id} is {objective_status.value}.",
    )
    events = (
        CourtroomEvent(
            event_type=CourtroomEventType.QUESTION_ASKED,
            phase=state.procedure.phase,
            summary=summaries[0],
            cited_object_ids=(brief.action_id, *brief.allowed_fact_ids),
        ),
        CourtroomEvent(
            event_type=CourtroomEventType.WITNESS_ANSWERED,
            phase=state.procedure.phase,
            summary=summaries[1],
            cited_object_ids=validation.supported_knowledge_ids,
        ),
        CourtroomEvent(
            event_type=CourtroomEventType.OBJECTIVE_ASSESSED,
            phase=state.procedure.phase,
            summary=summaries[2],
            cited_object_ids=(brief.objective_id,),
        ),
    )
    return WitnessExaminationOutput(
        examination_id=f"EXAM-{witness_id}-{mode.value.upper()}",
        witness_id=witness_id,
        mode=mode,
        objective_id=brief.objective_id,
        tactical_action=action,
        question_brief=brief,
        question_text=question,
        answer_text=answer,
        answer_validation=validation,
        objective_status=objective_status,
        event_summaries=summaries,
        events=events,
    )


def validate_witness_answer(
    *,
    case_package: CompiledCasePackage,
    witness_id: str,
    answer_text: str,
    allowed_fact_ids: tuple[str, ...],
) -> WitnessAnswerValidation:
    supported_atoms = tuple(
        atom.knowledge_atom_id
        for atom in case_package.witness_knowledge
        if atom.witness_id == witness_id
        and any(fact_id in allowed_fact_ids for fact_id in atom.related_fact_ids)
    )
    if supported_atoms:
        return WitnessAnswerValidation(
            status=AnswerValidationStatus.SUPPORTED,
            supported_knowledge_ids=supported_atoms,
            message="Answer is supported by supplied witness knowledge.",
        )
    matching_contradictions = tuple(
        contradiction.contradiction_id
        for contradiction in case_package.intelligence.contradiction_graph.contradictions
        if any(fact_id in allowed_fact_ids for fact_id in contradiction.fact_ids)
        and witness_id in contradiction.witness_ids
    )
    if matching_contradictions:
        return WitnessAnswerValidation(
            status=AnswerValidationStatus.INTENTIONAL_CONTRADICTION,
            contradiction_ids=matching_contradictions,
            message="Answer conflicts with known contradiction sources.",
        )
    return WitnessAnswerValidation(
        status=AnswerValidationStatus.HALLUCINATION,
        message="Answer is not grounded in witness knowledge or contradiction records.",
    )


def _generate_question(brief: QuestionExecutionBriefDTO) -> str:
    target = brief.allowed_fact_ids[0] if brief.allowed_fact_ids else "the key fact"
    return f"What can you tell the court about {target}?"


def _deterministic_answer(
    case_package: CompiledCasePackage,
    brief: QuestionExecutionBriefDTO,
) -> str:
    atom = next(
        (
            atom
            for atom in case_package.witness_knowledge
            if atom.witness_id == brief.target_witness_id
            and any(fact_id in brief.allowed_fact_ids for fact_id in atom.related_fact_ids)
        ),
        None,
    )
    if atom is None:
        return "I do not have personal knowledge of that point."
    return atom.text
