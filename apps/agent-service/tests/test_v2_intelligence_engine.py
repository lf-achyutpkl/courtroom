import unittest

from courtroom_engine import (
    ActorRole,
    CaseCompiler,
    ContextBoundaryService,
    ContextRequest,
    NodePurpose,
    TrialRuntimeState,
    VisibilityScope,
)
from courtroom_engine.fixtures import build_reference_case
from courtroom_engine.graph import V2AiAiState, build_v2_ai_ai_graph


class V2CaseCompilerTests(unittest.TestCase):
    def test_compiles_reference_case_with_derived_edges(self):
        case_package = CaseCompiler().compile(build_reference_case())

        self.assertEqual(case_package.metadata.case_id, "CASE-HARBOR-MARKET")
        self.assertEqual(
            case_package.intelligence.evidence_fact_edges,
            (("EVD-CAMERA", "FAC-SPILL-NOTICED"),),
        )
        self.assertEqual(
            case_package.intelligence.witness_fact_edges,
            (("WIT-CASHIER", "FAC-SPILL-NOTICED"),),
        )
        self.assertEqual(
            case_package.intelligence.initial_contradiction_ids,
            ("CON-INSPECTION-VIDEO",),
        )

    def test_rejects_witness_knowledge_with_public_visibility(self):
        template = build_reference_case()
        bad_atom = template.witness_knowledge[0].model_copy(
            update={"visibility": VisibilityScope.PUBLIC_CASE}
        )
        bad_template = template.model_copy(update={"witness_knowledge": (bad_atom,)})

        with self.assertRaisesRegex(ValueError, "witness-private"):
            CaseCompiler().compile(bad_template)


class V2ContextBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.case_package = CaseCompiler().compile(build_reference_case())
        self.runtime = TrialRuntimeState(
            case_id=self.case_package.metadata.case_id,
            phase="strategy",
            public_event_summaries=("Session initialized.",),
        )
        self.boundary = ContextBoundaryService()

    def test_plaintiff_lawyer_does_not_receive_defense_private_fact(self):
        actor = next(
            actor
            for actor in self.case_package.actors
            if actor.role == ActorRole.PLAINTIFF_LAWYER
        )

        context = self.boundary.build(
            case_package=self.case_package,
            state=self.runtime,
            request=ContextRequest(
                session_id=self.runtime.session_id,
                node_purpose=NodePurpose.GLOBAL_STRATEGY,
                requesting_actor_id=actor.actor_id,
            ),
        )

        fact_ids = {fact.fact_id for fact in context.case_view.facts}
        self.assertIn("FAC-SPILL-NOTICED", fact_ids)
        self.assertNotIn("FAC-DEFENSE-INSPECTION", fact_ids)
        self.assertEqual(context.case_view.witness_knowledge, ())

    def test_witness_receives_only_own_knowledge(self):
        actor = next(
            actor
            for actor in self.case_package.actors
            if actor.role == ActorRole.WITNESS
        )

        context = self.boundary.build(
            case_package=self.case_package,
            state=self.runtime.model_copy(update={"phase": "witness_answer"}),
            request=ContextRequest(
                session_id=self.runtime.session_id,
                node_purpose=NodePurpose.WITNESS_ANSWER,
                requesting_actor_id=actor.actor_id,
            ),
        )

        self.assertEqual(len(context.case_view.witness_knowledge), 1)
        self.assertEqual(
            context.case_view.witness_knowledge[0].knowledge_atom_id,
            "KNO-CASHIER-SAW-SPILL",
        )
        self.assertIn("synthetic_truth", context.metadata.excluded_categories)


class V2GraphSmokeTests(unittest.TestCase):
    def test_v2_ai_ai_graph_initializes_and_verifies_boundaries(self):
        result = build_v2_ai_ai_graph().invoke(V2AiAiState())

        self.assertEqual(result["status"], "context_boundaries_verified")
        self.assertIn("FAC-SPILL-NOTICED", result["boundary_context_ids"])
        self.assertIn("KNO-CASHIER-SAW-SPILL", result["boundary_context_ids"])


if __name__ == "__main__":
    unittest.main()
