from __future__ import annotations

import unittest

from courtroom_engine import (
    ActorRole,
    CaseCompiler,
    ContextBoundaryService,
    ContextRequest,
    EvidenceItem,
    Fact,
    FactContextDTO,
    KnowledgeAtom,
    NodePurpose,
    PartySide,
    TrialRuntimeState,
    VisibilityScope,
    Witness,
    WitnessKnowledgeContextDTO,
)
from courtroom_engine.domain.evidence import Fact as CanonicalFact
from courtroom_engine.domain.witnesses import KnowledgeAtom as CanonicalKnowledgeAtom
from courtroom_engine.fixtures import build_reference_case


class ContextBoundaryRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.compiler = CaseCompiler()
        self.boundary = ContextBoundaryService()

    def _runtime(self, case_id: str, phase: str = "strategy") -> TrialRuntimeState:
        return TrialRuntimeState(
            case_id=case_id,
            phase=phase,
            public_event_summaries=("Session initialized.",),
        )

    def test_unknown_visibility_is_excluded_and_audited(self) -> None:
        template = build_reference_case()
        hidden_fact = Fact(
            fact_id="FAC-UNKNOWN-VISIBILITY",
            text="This fact has an unsupported visibility label.",
            visibility="chambers_only",
        )
        package = self.compiler.compile(
            template.model_copy(update={"facts": (*template.facts, hidden_fact)})
        )
        runtime = self._runtime(package.metadata.case_id)
        plaintiff = next(
            actor
            for actor in package.actors
            if actor.role == ActorRole.PLAINTIFF_LAWYER
        )

        context = self.boundary.build(
            case_package=package,
            state=runtime,
            request=ContextRequest(
                session_id=runtime.session_id,
                node_purpose=NodePurpose.GLOBAL_STRATEGY,
                requesting_actor_id=plaintiff.actor_id,
            ),
        )

        fact_ids = {fact.fact_id for fact in context.case_view.facts}
        self.assertNotIn("FAC-UNKNOWN-VISIBILITY", fact_ids)
        self.assertEqual(context.audit.violation_status, "violation_detected")
        self.assertIn("unknown_visibility", context.audit.excluded_categories)

    def test_evaluator_only_material_does_not_leak_to_trial_actors(self) -> None:
        template = build_reference_case()
        evaluator_fact = Fact(
            fact_id="FAC-EVALUATOR-ONLY",
            text="Evaluator-only reconstruction of what really happened.",
            visibility=VisibilityScope.EVALUATOR_ONLY,
        )
        evaluator_evidence = EvidenceItem(
            evidence_id="EVD-EVALUATOR-ONLY",
            title="Evaluator packet",
            description="Internal evaluator-only evidence.",
            offered_by=PartySide.PLAINTIFF,
            visibility=VisibilityScope.EVALUATOR_ONLY,
        )
        package = self.compiler.compile(
            template.model_copy(
                update={
                    "facts": (*template.facts, evaluator_fact),
                    "evidence": (*template.evidence, evaluator_evidence),
                }
            )
        )
        runtime = self._runtime(package.metadata.case_id)

        for actor in package.actors:
            context = self.boundary.build(
                case_package=package,
                state=runtime,
                request=ContextRequest(
                    session_id=runtime.session_id,
                    node_purpose=(
                        NodePurpose.WITNESS_ANSWER
                        if actor.role == ActorRole.WITNESS
                        else NodePurpose.GLOBAL_STRATEGY
                    ),
                    requesting_actor_id=actor.actor_id,
                ),
            )
            self.assertNotIn(
                "FAC-EVALUATOR-ONLY",
                {fact.fact_id for fact in context.case_view.facts},
            )
            self.assertNotIn(
                "EVD-EVALUATOR-ONLY",
                {evidence.evidence_id for evidence in context.case_view.evidence},
            )

        evaluator_context = self.boundary.build(
            case_package=package,
            state=runtime,
            request=ContextRequest(
                session_id=runtime.session_id,
                node_purpose=NodePurpose.ACTOR_EVALUATION,
            ),
        )
        self.assertIn(
            "FAC-EVALUATOR-ONLY",
            {fact.fact_id for fact in evaluator_context.case_view.facts},
        )

    def test_opposing_private_material_does_not_cross_party_boundary(self) -> None:
        package = self.compiler.compile(build_reference_case())
        runtime = self._runtime(package.metadata.case_id)
        plaintiff = next(
            actor
            for actor in package.actors
            if actor.role == ActorRole.PLAINTIFF_LAWYER
        )
        defense = next(
            actor for actor in package.actors if actor.role == ActorRole.DEFENSE_LAWYER
        )

        plaintiff_context = self.boundary.build(
            case_package=package,
            state=runtime,
            request=ContextRequest(
                session_id=runtime.session_id,
                node_purpose=NodePurpose.GLOBAL_STRATEGY,
                requesting_actor_id=plaintiff.actor_id,
            ),
        )
        defense_context = self.boundary.build(
            case_package=package,
            state=runtime,
            request=ContextRequest(
                session_id=runtime.session_id,
                node_purpose=NodePurpose.GLOBAL_STRATEGY,
                requesting_actor_id=defense.actor_id,
            ),
        )

        self.assertNotIn(
            "FAC-DEFENSE-INSPECTION",
            {fact.fact_id for fact in plaintiff_context.case_view.facts},
        )
        self.assertIn(
            "FAC-DEFENSE-INSPECTION",
            {fact.fact_id for fact in defense_context.case_view.facts},
        )

    def test_witness_does_not_receive_non_target_witness_knowledge(self) -> None:
        template = build_reference_case()
        other_witness = Witness(
            witness_id="WIT-MANAGER",
            name="Jordan Patel",
            called_by=PartySide.DEFENSE,
            public_summary="Store manager on duty.",
            knowledge_atom_ids=("KNO-MANAGER-LOG",),
        )
        other_atom = KnowledgeAtom(
            knowledge_atom_id="KNO-MANAGER-LOG",
            witness_id="WIT-MANAGER",
            text="The manager knows about a separate inspection log.",
            related_fact_ids=("FAC-DEFENSE-INSPECTION",),
        )
        package = self.compiler.compile(
            template.model_copy(
                update={
                    "witnesses": (*template.witnesses, other_witness),
                    "witness_knowledge": (*template.witness_knowledge, other_atom),
                }
            )
        )
        runtime = self._runtime(package.metadata.case_id, phase="witness_answer")
        witness = next(
            actor for actor in package.actors if actor.role == ActorRole.WITNESS
        )

        context = self.boundary.build(
            case_package=package,
            state=runtime,
            request=ContextRequest(
                session_id=runtime.session_id,
                node_purpose=NodePurpose.WITNESS_ANSWER,
                requesting_actor_id=witness.actor_id,
            ),
        )

        self.assertEqual(
            {atom.knowledge_atom_id for atom in context.case_view.witness_knowledge},
            {"KNO-CASHIER-SAW-SPILL"},
        )

    def test_model_context_uses_dtos_not_canonical_models(self) -> None:
        package = self.compiler.compile(build_reference_case())
        runtime = self._runtime(package.metadata.case_id)
        plaintiff = next(
            actor
            for actor in package.actors
            if actor.role == ActorRole.PLAINTIFF_LAWYER
        )

        context = self.boundary.build(
            case_package=package,
            state=runtime,
            request=ContextRequest(
                session_id=runtime.session_id,
                node_purpose=NodePurpose.GLOBAL_STRATEGY,
                requesting_actor_id=plaintiff.actor_id,
            ),
        )

        self.assertIsInstance(context.case_view.facts[0], FactContextDTO)
        self.assertNotIsInstance(context.case_view.facts[0], CanonicalFact)
        self.assertFalse(hasattr(context, "case_package"))
        self.assertFalse(hasattr(context, "private_truth"))

        witness = next(
            actor for actor in package.actors if actor.role == ActorRole.WITNESS
        )
        witness_context = self.boundary.build(
            case_package=package,
            state=self._runtime(package.metadata.case_id, phase="witness_answer"),
            request=ContextRequest(
                session_id=runtime.session_id,
                node_purpose=NodePurpose.WITNESS_ANSWER,
                requesting_actor_id=witness.actor_id,
            ),
        )
        self.assertIsInstance(
            witness_context.case_view.witness_knowledge[0],
            WitnessKnowledgeContextDTO,
        )
        self.assertNotIsInstance(
            witness_context.case_view.witness_knowledge[0],
            CanonicalKnowledgeAtom,
        )

    def test_context_audit_record_contains_required_fields(self) -> None:
        package = self.compiler.compile(build_reference_case())
        runtime = self._runtime(package.metadata.case_id)

        context = self.boundary.build(
            case_package=package,
            state=runtime,
            request=ContextRequest(
                session_id=runtime.session_id,
                node_purpose=NodePurpose.INITIAL_CASE_ANALYSIS,
            ),
        )

        self.assertEqual(context.audit.session_id, runtime.session_id)
        self.assertEqual(context.audit.case_id, package.metadata.case_id)
        self.assertIn("FAC-SPILL-NOTICED", context.audit.included_object_ids)
        self.assertIn("canonical_case_package", context.audit.excluded_categories)
        self.assertTrue(context.audit.policy_version)
        self.assertTrue(context.audit.projection_version)
        self.assertGreater(context.audit.estimated_context_size, 0)
        self.assertEqual(context.audit.violation_status, "clean")


if __name__ == "__main__":
    unittest.main()
