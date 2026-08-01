from __future__ import annotations

import unittest

from pydantic import ValidationError

from courtroom_engine import (
    ActorRole,
    CaseCompiler,
    CaseKind,
    ClaimOrCharge,
    ContextBoundaryService,
    ContextRequest,
    EvidenceItem,
    LegalElement,
    NodePurpose,
    PartySide,
    TrialRuntimeState,
)
from courtroom_engine.application.case_analysis import analyze_case
from courtroom_engine.domain.case_intelligence import (
    CaseGapType,
    CaseGraphEdgeType,
    CaseGraphNodeType,
    ContradictionRecord,
    ContradictionType,
    EvidenceRelationship,
    EvidenceRelationshipType,
)
from courtroom_engine.fixtures import (
    build_balanced_prototype_theft_case,
    build_case_intelligence_civil_case,
    build_case_intelligence_criminal_case,
)


class CaseIntelligenceAnalyzerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.compiler = CaseCompiler()

    def test_builds_civil_claim_case_graph(self) -> None:
        report = analyze_case(build_case_intelligence_civil_case())

        nodes = {node.node_id: node.node_type for node in report.case_graph.nodes}
        edges = {
            (edge.source_node_id, edge.target_node_id, edge.edge_type)
            for edge in report.case_graph.edges
        }

        self.assertEqual(nodes["CLM-NEGLIGENCE"], CaseGraphNodeType.CLAIM_OR_CHARGE)
        self.assertIn(
            ("CLM-NEGLIGENCE", "ELM-NOTICE", CaseGraphEdgeType.HAS_ELEMENT),
            edges,
        )
        self.assertIn(
            ("FAC-SPILL-NOTICED", "ELM-NOTICE", CaseGraphEdgeType.SUPPORTS_ELEMENT),
            edges,
        )

    def test_builds_criminal_charge_case_graph(self) -> None:
        report = analyze_case(build_case_intelligence_criminal_case())

        nodes = {node.node_id: node.node_type for node in report.case_graph.nodes}
        material = {
            (record.fact_id, record.matter_id, record.supporting_side)
            for record in report.material_fact_map.facts
        }

        self.assertEqual(nodes["CHG-THEFT"], CaseGraphNodeType.CLAIM_OR_CHARGE)
        self.assertIn(
            ("FAC-CAMERA-MATCH", "CHG-THEFT", PartySide.PROSECUTION),
            material,
        )

    def test_balanced_prototype_theft_fixture_compiles_with_contested_evidence(self) -> None:
        package = self.compiler.compile(build_balanced_prototype_theft_case())

        self.assertEqual(package.metadata.case_id, "CASE-KEENE-PROTOTYPE-THEFT")
        self.assertEqual(
            {party.side for party in package.parties},
            {PartySide.PROSECUTION, PartySide.DEFENSE},
        )
        self.assertGreaterEqual(
            len({evidence.offered_by for evidence in package.evidence}),
            2,
        )
        contradictions = {
            contradiction.contradiction_id
            for contradiction in package.intelligence.contradiction_graph.contradictions
        }
        self.assertIn("CON-ACCESS-CLOCKS", contradictions)

    def test_compiler_validates_reference_errors(self) -> None:
        template = build_case_intelligence_civil_case()
        with self.assertRaisesRegex(ValueError, "unknown evidence fact id"):
            self.compiler.compile(
                template.model_copy(
                    update={
                        "evidence": (
                            EvidenceItem(
                                evidence_id="EVD-DANGLING",
                                title="Dangling",
                                description="Bad reference.",
                                offered_by=PartySide.PLAINTIFF,
                                supports_fact_ids=("FAC-NOPE",),
                            ),
                        )
                    }
                )
            )

        with self.assertRaisesRegex(ValueError, "unknown knowledge fact id"):
            self.compiler.compile(
                template.model_copy(
                    update={
                        "witness_knowledge": (
                            template.witness_knowledge[0].model_copy(
                                update={"related_fact_ids": ("FAC-NOPE",)}
                            ),
                        )
                    }
                )
            )

    def test_compiler_validates_duplicate_ids_and_case_kind(self) -> None:
        template = build_case_intelligence_civil_case()
        with self.assertRaisesRegex(ValueError, "duplicate evidence ids"):
            self.compiler.compile(
                template.model_copy(
                    update={"evidence": (template.evidence[0], template.evidence[0])}
                )
            )

        bad_matter = template.matters[0].model_copy(
            update={"case_kind": CaseKind.CRIMINAL}
        )
        with self.assertRaisesRegex(ValueError, "matter case kind must match"):
            self.compiler.compile(
                template.model_copy(update={"matters": (bad_matter,)})
            )

        with self.assertRaises(ValidationError):
            ClaimOrCharge(
                matter_id="CLM-BAD",
                case_kind=CaseKind.CRIMINAL,
                title="Bad charge prefix",
                elements=template.matters[0].elements,
            )

    def test_missing_burden_element_support_creates_gap(self) -> None:
        template = build_case_intelligence_civil_case()
        unsupported = LegalElement(
            element_id="ELM-BREACH",
            label="Breach",
            description="Defendant breached the duty of care.",
            burden="preponderance",
            proving_side=PartySide.PLAINTIFF,
        )
        matter = template.matters[0].model_copy(
            update={"elements": (*template.matters[0].elements, unsupported)}
        )

        report = analyze_case(template.model_copy(update={"matters": (matter,)}))

        self.assertIn(
            ("ELM-BREACH", CaseGapType.MISSING_BURDEN_PROOF),
            {(gap.element_id, gap.gap_type) for gap in report.case_gaps},
        )

    def test_golden_civil_intelligence_edges_and_gaps(self) -> None:
        package = self.compiler.compile(build_case_intelligence_civil_case())
        report = package.intelligence

        self.assertIn(
            ("FAC-SPILL-NOTICED", "ELM-NOTICE"),
            {
                (record.fact_id, record.element_id)
                for record in report.material_fact_map.facts
            },
        )
        self.assertIn(
            ("EVD-CAMERA", "FAC-SPILL-NOTICED"),
            {
                (relationship.evidence_id, relationship.fact_id)
                for relationship in report.evidence_graph.relationships
                if relationship.relationship_type
                == EvidenceRelationshipType.EVIDENCE_TO_FACT
            },
        )
        self.assertIn(
            ("WIT-CASHIER", "FAC-SPILL-NOTICED"),
            {
                (relationship.witness_id, relationship.fact_id)
                for relationship in report.witness_knowledge_graph.relationships
            },
        )
        self.assertIn(
            "CON-INSPECTION-VIDEO",
            {
                contradiction.contradiction_id
                for contradiction in report.contradiction_graph.contradictions
            },
        )
        self.assertIn(
            CaseGapType.CONTRADICTION_OPPORTUNITY,
            {gap.gap_type for gap in report.case_gaps},
        )

    def test_provenance_confidence_and_contradiction_sources(self) -> None:
        report = self.compiler.compile(
            build_case_intelligence_criminal_case()
        ).intelligence

        for record in report.material_fact_map.facts:
            self.assertTrue(record.source_ids)
            self.assertIsNotNone(record.confidence_score)
        for relationship in report.evidence_graph.relationships:
            self.assertTrue(relationship.source_ids)
            self.assertIsNotNone(relationship.confidence_score)
        for contradiction in report.contradiction_graph.contradictions:
            self.assertTrue(contradiction.source_ids)
            self.assertTrue(contradiction.fact_ids)

    def test_intelligence_validation_fails_closed_on_unsupported_claims(self) -> None:
        template = build_case_intelligence_civil_case()
        report = analyze_case(template)
        bad_report = report.model_copy(
            update={
                "evidence_graph": report.evidence_graph.model_copy(
                    update={
                        "relationships": (
                            *report.evidence_graph.relationships,
                            EvidenceRelationship(
                                relationship_id="REL-EVD-CAMERA-FAC-NOPE",
                                relationship_type=(
                                    EvidenceRelationshipType.EVIDENCE_TO_FACT
                                ),
                                evidence_id="EVD-CAMERA",
                                fact_id="FAC-NOPE",
                                source_ids=("EVD-CAMERA", "FAC-NOPE"),
                                derivation_method="test",
                                confidence_score=1.0,
                            ),
                        )
                    }
                )
            }
        )

        with self.assertRaisesRegex(ValueError, "dangling evidence fact"):
            from courtroom_engine.application.case_analysis import (
                normalize_case,
                validate_case_intelligence,
            )

            validate_case_intelligence(normalize_case(template), bad_report)

    def test_contradiction_validation_requires_valid_sources(self) -> None:
        template = build_case_intelligence_civil_case()
        report = analyze_case(template)
        bad_report = report.model_copy(
            update={
                "contradiction_graph": report.contradiction_graph.model_copy(
                    update={
                        "contradictions": (
                            ContradictionRecord(
                                contradiction_id="CON-BAD-SOURCE",
                                contradiction_type=(
                                    ContradictionType.WITNESS_VS_DOCUMENT
                                ),
                                description="Bad source",
                                fact_ids=("FAC-NOPE",),
                                source_ids=("FAC-NOPE",),
                                derivation_method="test",
                                confidence_score=1.0,
                            ),
                        )
                    }
                )
            }
        )

        with self.assertRaisesRegex(ValueError, "dangling contradiction fact"):
            from courtroom_engine.application.case_analysis import (
                normalize_case,
                validate_case_intelligence,
            )

            validate_case_intelligence(normalize_case(template), bad_report)

    def test_actor_context_excludes_hidden_intelligence_labels(self) -> None:
        package = self.compiler.compile(build_case_intelligence_criminal_case())
        runtime = TrialRuntimeState(case_id=package.metadata.case_id)
        boundary = ContextBoundaryService()
        security = next(
            actor for actor in package.actors if actor.actor_id == "ACT-SECURITY"
        )

        context = boundary.build(
            case_package=package,
            state=runtime,
            request=ContextRequest(
                session_id=runtime.session_id,
                node_purpose=NodePurpose.WITNESS_ANSWER,
                requesting_actor_id=security.actor_id,
            ),
        )

        dumped = context.model_dump()
        self.assertNotIn("CON-VIDEO-RECEIPT", str(dumped))
        self.assertNotIn("witness_vs_document", str(dumped))
        self.assertNotIn("KNO-DEFENDANT-RECEIPT", str(dumped))
        self.assertEqual(
            {
                rel.witness_id
                for rel in context.case_view.intelligence.witness_fact_relationships
            },
            {"WIT-SECURITY"},
        )
        self.assertFalse(hasattr(context.case_view.intelligence, "contradiction_graph"))

    def test_evaluator_truth_stays_out_of_actor_facing_intelligence(self) -> None:
        package = self.compiler.compile(build_case_intelligence_civil_case())
        runtime = TrialRuntimeState(case_id=package.metadata.case_id)
        boundary = ContextBoundaryService()
        plaintiff = next(
            actor
            for actor in package.actors
            if actor.role == ActorRole.PLAINTIFF_LAWYER
        )

        context = boundary.build(
            case_package=package,
            state=runtime,
            request=ContextRequest(
                session_id=runtime.session_id,
                node_purpose=NodePurpose.GLOBAL_STRATEGY,
                requesting_actor_id=plaintiff.actor_id,
            ),
        )

        dumped = context.model_dump()
        self.assertNotIn("ground_truth_summary", str(dumped))
        self.assertNotIn("expected_contradictions", str(dumped))
        self.assertNotIn("ideal_action", str(dumped))


if __name__ == "__main__":
    unittest.main()
