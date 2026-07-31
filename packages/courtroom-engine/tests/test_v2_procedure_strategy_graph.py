from __future__ import annotations

import unittest

from courtroom_engine import (
    ActionType,
    Actor,
    ActorRole,
    CaseCompiler,
    ContextBoundaryService,
    ContextRequest,
    NodePurpose,
    PartySide,
    ProcedureState,
    TrialPhase,
    TrialRuntimeState,
)
from courtroom_engine.application.examination import run_witness_examination
from courtroom_engine.application.planning import (
    build_question_execution_brief,
    build_tactical_action_plan,
    plan_party_strategy,
    validate_party_strategy,
)
from courtroom_engine.domain.procedure import ObjectionRecord
from courtroom_engine.domain.strategy import StrategyValidationStatus
from courtroom_engine.fixtures import build_reference_case
from courtroom_engine.policies.procedure import validate_action_allowed


class ProcedurePolicyTests(unittest.TestCase):
    def test_invalid_action_is_rejected_for_witness(self) -> None:
        package = CaseCompiler().compile(build_reference_case())
        witness = next(actor for actor in package.actors if actor.role == ActorRole.WITNESS)
        result = validate_action_allowed(
            actor=witness,
            node_purpose=NodePurpose.WITNESS_ANSWER,
            action_type=ActionType.ASK_QUESTION,
            procedure=ProcedureState(phase=TrialPhase.WITNESS_EXAMINATION),
        )

        self.assertFalse(result.valid)
        self.assertIn("ask_question is not allowed", result.reason)

    def test_jury_context_excludes_unadmitted_evidence(self) -> None:
        template = build_reference_case()
        jury = Actor(actor_id="ACT-JURY", role=ActorRole.JURY, name="Jury")
        package = CaseCompiler().compile(
            template.model_copy(update={"actors": (*template.actors, jury)})
        )
        runtime = TrialRuntimeState(
            case_id=package.metadata.case_id,
            phase=TrialPhase.WITNESS_EXAMINATION.value,
            procedure=ProcedureState(phase=TrialPhase.WITNESS_EXAMINATION),
        )

        context = ContextBoundaryService().build(
            case_package=package,
            state=runtime,
            request=ContextRequest(
                session_id=runtime.session_id,
                node_purpose=NodePurpose.GLOBAL_STRATEGY,
                requesting_actor_id=jury.actor_id,
            ),
        )

        self.assertEqual(context.case_view.evidence, ())

    def test_judge_ruling_context_can_see_pending_evidence(self) -> None:
        package = CaseCompiler().compile(build_reference_case())
        judge = next(actor for actor in package.actors if actor.role == ActorRole.TRIAL_JUDGE)
        runtime = TrialRuntimeState(
            case_id=package.metadata.case_id,
            phase=TrialPhase.WITNESS_EXAMINATION.value,
            procedure=ProcedureState(
                phase=TrialPhase.WITNESS_EXAMINATION,
                pending_objection=ObjectionRecord(
                    objection_id="OBJN-001",
                    objecting_actor_id="ACT-DEFENSE-LAWYER",
                    target_evidence_id="EVD-CAMERA",
                    grounds="foundation",
                ),
            ),
        )

        context = ContextBoundaryService().build(
            case_package=package,
            state=runtime,
            request=ContextRequest(
                session_id=runtime.session_id,
                node_purpose=NodePurpose.OBJECTION_RULING,
                requesting_actor_id=judge.actor_id,
            ),
        )

        self.assertEqual(
            {evidence.evidence_id for evidence in context.case_view.evidence},
            {"EVD-CAMERA"},
        )


class StrategyPlannerTests(unittest.TestCase):
    def test_strategy_validation_fails_on_hidden_fact_reference(self) -> None:
        package = CaseCompiler().compile(build_reference_case())
        runtime = TrialRuntimeState(case_id=package.metadata.case_id)
        strategy = plan_party_strategy(
            case_package=package,
            state=runtime,
            side=PartySide.PLAINTIFF,
        )
        hidden_objective = strategy.objectives[0].model_copy(
            update={"target_fact_ids": ("FAC-DEFENSE-INSPECTION",)}
        )
        invalid_strategy = strategy.model_copy(update={"objectives": (hidden_objective,)})
        plaintiff = next(
            actor for actor in package.actors if actor.role == ActorRole.PLAINTIFF_LAWYER
        )
        context = ContextBoundaryService().build(
            case_package=package,
            state=runtime,
            request=ContextRequest(
                session_id=runtime.session_id,
                node_purpose=NodePurpose.GLOBAL_STRATEGY,
                requesting_actor_id=plaintiff.actor_id,
            ),
        )

        validation = validate_party_strategy(invalid_strategy, context)

        self.assertEqual(validation.status, StrategyValidationStatus.INVALID)
        self.assertIn("fact:FAC-DEFENSE-INSPECTION", validation.invalid_references)

    def test_question_generation_brief_excludes_party_strategy(self) -> None:
        package = CaseCompiler().compile(build_reference_case())
        runtime = TrialRuntimeState(case_id=package.metadata.case_id)
        strategy = plan_party_strategy(
            case_package=package,
            state=runtime,
            side=PartySide.PLAINTIFF,
        )
        action = build_tactical_action_plan(strategy, "WIT-CASHIER")
        brief = build_question_execution_brief(action)

        dumped = brief.model_dump()
        self.assertNotIn("theory", dumped)
        self.assertNotIn("objectives", dumped)
        self.assertIn("party_strategy", brief.prohibited_reference_ids)


class WitnessExaminationTests(unittest.TestCase):
    def test_witness_examination_produces_supported_answer_update(self) -> None:
        package = CaseCompiler().compile(build_reference_case())
        runtime = TrialRuntimeState(
            case_id=package.metadata.case_id,
            phase=TrialPhase.WITNESS_EXAMINATION.value,
            procedure=ProcedureState(phase=TrialPhase.WITNESS_EXAMINATION),
        )
        strategy = plan_party_strategy(
            case_package=package,
            state=runtime,
            side=PartySide.PLAINTIFF,
        )

        output = run_witness_examination(
            case_package=package,
            state=runtime,
            strategy=strategy,
            witness_id="WIT-CASHIER",
        )

        self.assertEqual(output.answer_validation.status.value, "supported")
        self.assertEqual(output.objective_status.value, "satisfied")
        self.assertGreaterEqual(len(output.events), 3)


if __name__ == "__main__":
    unittest.main()
