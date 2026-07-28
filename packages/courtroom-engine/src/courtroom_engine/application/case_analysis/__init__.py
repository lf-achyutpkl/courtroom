from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from courtroom_engine.domain.case import CaseKind, PartySide
from courtroom_engine.domain.case_intelligence import (
    AnalyzerDiagnostic,
    CaseGap,
    CaseGapType,
    CaseGraph,
    CaseGraphEdge,
    CaseGraphEdgeType,
    CaseGraphNode,
    CaseGraphNodeType,
    CaseIntelligenceReport,
    ContradictionGraph,
    ContradictionRecord,
    ContradictionType,
    DisputeStatus,
    EvidenceGraph,
    EvidenceRelationship,
    EvidenceRelationshipType,
    MaterialFactMap,
    MaterialFactRecord,
    ProofStatus,
    TimelineEvent,
    TimelineGraph,
    WitnessKnowledgeGraph,
    WitnessKnowledgeRelationship,
)
from courtroom_engine.domain.evidence import Fact
from courtroom_engine.domain.legal import LegalElement
from courtroom_engine.domain.trial import AuthoredCaseTemplate, CompiledCasePackage

DERIVATION_METHOD = "deterministic_reference_mapping"
HIGH_CONFIDENCE = 1.0
MEDIUM_CONFIDENCE = 0.75


@dataclass(frozen=True)
class NormalizedCase:
    template: AuthoredCaseTemplate
    facts_by_id: dict[str, Fact]
    elements_by_id: dict[str, LegalElement]
    fact_ids_by_element: dict[str, tuple[str, ...]]
    evidence_ids_by_fact: dict[str, tuple[str, ...]]
    witness_ids_by_fact: dict[str, tuple[str, ...]]
    knowledge_ids_by_witness_fact: dict[tuple[str, str], tuple[str, ...]]
    diagnostics: tuple[AnalyzerDiagnostic, ...] = ()


def analyze_case(
    template_or_package: AuthoredCaseTemplate | CompiledCasePackage,
) -> CaseIntelligenceReport:
    """Deterministically derive case intelligence from authored references."""
    template = (
        _template_from_package(template_or_package)
        if isinstance(template_or_package, CompiledCasePackage)
        else template_or_package
    )
    normalized = normalize_case(template)
    case_graph = identify_legal_issues(normalized)
    case_graph = map_legal_elements(normalized, case_graph)
    material_fact_map = classify_material_facts(normalized)
    evidence_graph = build_evidence_graph(normalized)
    timeline_graph = build_timeline_graph(normalized)
    witness_graph = build_witness_knowledge_graph(normalized)
    contradiction_graph = detect_contradictions(normalized, evidence_graph)
    gaps = analyze_case_gaps(
        normalized,
        material_fact_map,
        evidence_graph,
        witness_graph,
        contradiction_graph,
    )
    return validate_case_intelligence(
        normalized,
        CaseIntelligenceReport(
            case_graph=case_graph,
            evidence_graph=evidence_graph,
            timeline_graph=timeline_graph,
            contradiction_graph=contradiction_graph,
            material_fact_map=material_fact_map,
            witness_knowledge_graph=witness_graph,
            case_gaps=gaps,
            diagnostics=normalized.diagnostics,
        ),
    )


def normalize_case(template: AuthoredCaseTemplate) -> NormalizedCase:
    facts_by_id = {fact.fact_id: fact for fact in template.facts}
    elements_by_id = {
        element.element_id: element
        for matter in template.matters
        for element in matter.elements
    }
    fact_ids_by_element: dict[str, list[str]] = defaultdict(list)
    for fact in template.facts:
        for element_id in fact.supports_element_ids:
            fact_ids_by_element[element_id].append(fact.fact_id)

    evidence_ids_by_fact: dict[str, list[str]] = defaultdict(list)
    for item in template.evidence:
        for fact_id in item.supports_fact_ids:
            evidence_ids_by_fact[fact_id].append(item.evidence_id)

    witness_ids_by_fact: dict[str, set[str]] = defaultdict(set)
    knowledge_ids_by_witness_fact: dict[tuple[str, str], list[str]] = defaultdict(list)
    for atom in template.witness_knowledge:
        for fact_id in atom.related_fact_ids:
            witness_ids_by_fact[fact_id].add(atom.witness_id)
            knowledge_ids_by_witness_fact[(atom.witness_id, fact_id)].append(
                atom.knowledge_atom_id
            )

    diagnostics: list[AnalyzerDiagnostic] = []
    for matter in template.matters:
        if not matter.elements:
            diagnostics.append(
                AnalyzerDiagnostic(
                    code="matter_without_elements",
                    message=f"Matter {matter.matter_id} has no burden elements.",
                    source_ids=(matter.matter_id,),
                    severity="error",
                )
            )

    return NormalizedCase(
        template=template,
        facts_by_id=facts_by_id,
        elements_by_id=elements_by_id,
        fact_ids_by_element={
            key: tuple(dict.fromkeys(value))
            for key, value in fact_ids_by_element.items()
        },
        evidence_ids_by_fact={
            key: tuple(dict.fromkeys(value))
            for key, value in evidence_ids_by_fact.items()
        },
        witness_ids_by_fact={
            key: tuple(sorted(value)) for key, value in witness_ids_by_fact.items()
        },
        knowledge_ids_by_witness_fact={
            key: tuple(dict.fromkeys(value))
            for key, value in knowledge_ids_by_witness_fact.items()
        },
        diagnostics=tuple(diagnostics),
    )


def identify_legal_issues(normalized: NormalizedCase) -> CaseGraph:
    template = normalized.template
    nodes: list[CaseGraphNode] = []
    edges: list[CaseGraphEdge] = []
    for party in template.parties:
        nodes.append(
            _node(
                party.party_id,
                CaseGraphNodeType.PARTY,
                party.name,
                (party.party_id,),
            )
        )
    for matter in template.matters:
        matter_type = (
            CaseGraphNodeType.CLAIM_OR_CHARGE
            if matter.case_kind in {CaseKind.CIVIL, CaseKind.CRIMINAL}
            else CaseGraphNodeType.MATTER
        )
        nodes.append(
            _node(matter.matter_id, matter_type, matter.title, (matter.matter_id,))
        )
        asserting_side = (
            PartySide.PLAINTIFF
            if matter.case_kind == CaseKind.CIVIL
            else PartySide.PROSECUTION
        )
        for party in template.parties:
            if party.side == asserting_side:
                edges.append(
                    _edge(
                        f"EDGE-{party.party_id}-{matter.matter_id}-ASSERTS",
                        CaseGraphEdgeType.ASSERTS,
                        party.party_id,
                        matter.matter_id,
                        (party.party_id, matter.matter_id),
                    )
                )
    return CaseGraph(nodes=tuple(nodes), edges=tuple(edges))


def map_legal_elements(normalized: NormalizedCase, case_graph: CaseGraph) -> CaseGraph:
    nodes = list(case_graph.nodes)
    edges = list(case_graph.edges)
    for matter in normalized.template.matters:
        for element in matter.elements:
            nodes.append(
                _node(
                    element.element_id,
                    CaseGraphNodeType.LEGAL_ELEMENT,
                    element.label,
                    (matter.matter_id, element.element_id),
                )
            )
            edges.append(
                _edge(
                    f"EDGE-{matter.matter_id}-{element.element_id}-HAS",
                    CaseGraphEdgeType.HAS_ELEMENT,
                    matter.matter_id,
                    element.element_id,
                    (matter.matter_id, element.element_id),
                )
            )
    for fact in normalized.template.facts:
        nodes.append(
            _node(fact.fact_id, CaseGraphNodeType.FACT, fact.text, (fact.fact_id,))
        )
        for element_id in fact.supports_element_ids:
            edges.append(
                _edge(
                    f"EDGE-{fact.fact_id}-{element_id}-SUPPORTS",
                    CaseGraphEdgeType.SUPPORTS_ELEMENT,
                    fact.fact_id,
                    element_id,
                    (fact.fact_id, element_id),
                )
            )
    for item in normalized.template.evidence:
        nodes.append(
            _node(
                item.evidence_id,
                CaseGraphNodeType.EVIDENCE,
                item.title,
                (item.evidence_id,),
            )
        )
        for fact_id in item.supports_fact_ids:
            edges.append(
                _edge(
                    f"EDGE-{item.evidence_id}-{fact_id}-SUPPORTS",
                    CaseGraphEdgeType.SUPPORTS_FACT,
                    item.evidence_id,
                    fact_id,
                    (item.evidence_id, fact_id),
                )
            )
    for witness in normalized.template.witnesses:
        nodes.append(
            _node(
                witness.witness_id,
                CaseGraphNodeType.WITNESS,
                witness.name,
                (witness.witness_id,),
            )
        )
    return CaseGraph(nodes=tuple(nodes), edges=tuple(edges))


def classify_material_facts(normalized: NormalizedCase) -> MaterialFactMap:
    records: list[MaterialFactRecord] = []
    opposing_side_by_supporting = {
        PartySide.PLAINTIFF: PartySide.DEFENSE,
        PartySide.PROSECUTION: PartySide.DEFENSE,
        PartySide.DEFENSE: (
            PartySide.PLAINTIFF
            if normalized.template.metadata.case_kind == CaseKind.CIVIL
            else PartySide.PROSECUTION
        ),
    }
    matter_by_element = {
        element.element_id: matter
        for matter in normalized.template.matters
        for element in matter.elements
    }
    for fact in normalized.template.facts:
        for element_id in fact.supports_element_ids:
            element = normalized.elements_by_id[element_id]
            matter = matter_by_element[element_id]
            evidence_ids = normalized.evidence_ids_by_fact.get(fact.fact_id, ())
            witness_ids = normalized.witness_ids_by_fact.get(fact.fact_id, ())
            proof_status = ProofStatus.UNSUPPORTED
            if evidence_ids and witness_ids:
                proof_status = (
                    ProofStatus.CONTESTED if fact.disputed else ProofStatus.SUPPORTED
                )
            elif evidence_ids or witness_ids:
                proof_status = ProofStatus.CONTESTED
            records.append(
                MaterialFactRecord(
                    fact_id=fact.fact_id,
                    matter_id=matter.matter_id,
                    element_id=element_id,
                    supporting_side=element.proving_side,
                    opposing_side=opposing_side_by_supporting[element.proving_side],
                    dispute_status=(
                        DisputeStatus.DISPUTED
                        if fact.disputed
                        else DisputeStatus.UNDISPUTED
                    ),
                    supporting_evidence_ids=evidence_ids,
                    knowledgeable_witness_ids=witness_ids,
                    proof_status=proof_status,
                    source_ids=(fact.fact_id, element_id, matter.matter_id),
                    derivation_method=DERIVATION_METHOD,
                    confidence_score=HIGH_CONFIDENCE,
                )
            )
    return MaterialFactMap(facts=tuple(records))


def build_evidence_graph(normalized: NormalizedCase) -> EvidenceGraph:
    relationships: list[EvidenceRelationship] = []
    for item in normalized.template.evidence:
        for fact_id in item.supports_fact_ids:
            relationships.append(
                EvidenceRelationship(
                    relationship_id=f"REL-{item.evidence_id}-{fact_id}",
                    relationship_type=EvidenceRelationshipType.EVIDENCE_TO_FACT,
                    evidence_id=item.evidence_id,
                    fact_id=fact_id,
                    source_ids=(item.evidence_id, fact_id),
                    derivation_method=DERIVATION_METHOD,
                    confidence_score=HIGH_CONFIDENCE,
                )
            )
            for element_id in normalized.facts_by_id[fact_id].supports_element_ids:
                relationships.append(
                    EvidenceRelationship(
                        relationship_id=f"REL-{item.evidence_id}-{element_id}",
                        relationship_type=EvidenceRelationshipType.EVIDENCE_TO_ELEMENT,
                        evidence_id=item.evidence_id,
                        element_id=element_id,
                        source_ids=(item.evidence_id, fact_id, element_id),
                        derivation_method=DERIVATION_METHOD,
                        confidence_score=HIGH_CONFIDENCE,
                    )
                )
        if item.foundation_required:
            witness_ids = tuple(
                sorted(
                    {
                        witness_id
                        for fact_id in item.supports_fact_ids
                        for witness_id in normalized.witness_ids_by_fact.get(
                            fact_id, ()
                        )
                    }
                )
            )
            for witness_id in witness_ids:
                relationships.append(
                    EvidenceRelationship(
                        relationship_id=(
                            f"REL-{item.evidence_id}-{witness_id}-FOUNDATION"
                        ),
                        relationship_type=EvidenceRelationshipType.EVIDENCE_TO_WITNESS,
                        evidence_id=item.evidence_id,
                        witness_id=witness_id,
                        description=(
                            "Witness has knowledge tied to a fact supported by this "
                            "evidence."
                        ),
                        source_ids=(item.evidence_id, witness_id),
                        derivation_method=DERIVATION_METHOD,
                        confidence_score=MEDIUM_CONFIDENCE,
                    )
                )
    return EvidenceGraph(relationships=tuple(relationships))


def build_timeline_graph(normalized: NormalizedCase) -> TimelineGraph:
    events = tuple(
        TimelineEvent(
            event_id=f"TL-{fact.fact_id.removeprefix('FAC-')}",
            label=fact.text,
            source_fact_ids=(fact.fact_id,),
            source_ids=(fact.fact_id,),
            derivation_method=DERIVATION_METHOD,
            confidence_score=MEDIUM_CONFIDENCE,
        )
        for fact in normalized.template.facts
    )
    return TimelineGraph(events=events)


def build_witness_knowledge_graph(normalized: NormalizedCase) -> WitnessKnowledgeGraph:
    relationships: list[WitnessKnowledgeRelationship] = []
    for (
        witness_id,
        fact_id,
    ), atom_ids in normalized.knowledge_ids_by_witness_fact.items():
        relationships.append(
            WitnessKnowledgeRelationship(
                relationship_id=f"REL-{witness_id}-{fact_id}",
                witness_id=witness_id,
                fact_id=fact_id,
                knowledge_atom_ids=atom_ids,
                source_ids=atom_ids,
                derivation_method=DERIVATION_METHOD,
                confidence_score=HIGH_CONFIDENCE,
            )
        )
    return WitnessKnowledgeGraph(relationships=tuple(relationships))


def detect_contradictions(
    normalized: NormalizedCase, evidence_graph: EvidenceGraph
) -> ContradictionGraph:
    if normalized.template.private_truth is None:
        return ContradictionGraph()
    evidence_by_fact = normalized.evidence_ids_by_fact
    witnesses_by_fact = normalized.witness_ids_by_fact
    contradictions: list[ContradictionRecord] = []
    for expected in normalized.template.private_truth.expected_contradictions:
        evidence_ids = tuple(
            dict.fromkeys(
                evidence_id
                for fact_id in expected.involved_fact_ids
                for evidence_id in evidence_by_fact.get(fact_id, ())
            )
        )
        witness_ids = tuple(
            dict.fromkeys(
                witness_id
                for fact_id in expected.involved_fact_ids
                for witness_id in witnesses_by_fact.get(fact_id, ())
            )
        )
        contradiction_type = (
            ContradictionType.WITNESS_VS_DOCUMENT
            if evidence_ids and witness_ids
            else ContradictionType.CLAIM_VS_EVIDENCE
        )
        contradictions.append(
            ContradictionRecord(
                contradiction_id=expected.contradiction_id,
                contradiction_type=contradiction_type,
                description=expected.description,
                fact_ids=expected.involved_fact_ids,
                evidence_ids=evidence_ids,
                witness_ids=witness_ids,
                source_ids=(
                    expected.contradiction_id,
                    *expected.involved_fact_ids,
                    *evidence_ids,
                    *witness_ids,
                ),
                derivation_method=DERIVATION_METHOD,
                confidence_score=MEDIUM_CONFIDENCE,
            )
        )
    return ContradictionGraph(contradictions=tuple(contradictions))


def analyze_case_gaps(
    normalized: NormalizedCase,
    material_fact_map: MaterialFactMap,
    evidence_graph: EvidenceGraph,
    witness_graph: WitnessKnowledgeGraph,
    contradiction_graph: ContradictionGraph,
) -> tuple[CaseGap, ...]:
    gaps: list[CaseGap] = []
    material_by_element: dict[str, list[MaterialFactRecord]] = defaultdict(list)
    for record in material_fact_map.facts:
        material_by_element[record.element_id].append(record)

    for matter in normalized.template.matters:
        if not matter.elements:
            gaps.append(
                CaseGap(
                    gap_id=f"GAP-{matter.matter_id}-NO-ELEMENTS",
                    gap_type=CaseGapType.UNRESOLVED_LEGAL_ISSUE,
                    description="Matter has no legal elements to map burden proof.",
                    matter_id=matter.matter_id,
                    source_ids=(matter.matter_id,),
                    derivation_method=DERIVATION_METHOD,
                    confidence_score=HIGH_CONFIDENCE,
                    severity=1.0,
                )
            )
        for element in matter.elements:
            records = material_by_element.get(element.element_id, [])
            if not records:
                gaps.append(
                    CaseGap(
                        gap_id=f"GAP-{element.element_id}-NO-FACTS",
                        gap_type=CaseGapType.MISSING_BURDEN_PROOF,
                        description=(
                            "No authored material facts support this burden element."
                        ),
                        side=element.proving_side,
                        matter_id=matter.matter_id,
                        element_id=element.element_id,
                        source_ids=(matter.matter_id, element.element_id),
                        derivation_method=DERIVATION_METHOD,
                        confidence_score=HIGH_CONFIDENCE,
                        severity=1.0,
                    )
                )

    for record in material_fact_map.facts:
        if not record.supporting_evidence_ids:
            gaps.append(
                CaseGap(
                    gap_id=f"GAP-{record.fact_id}-NO-EVIDENCE",
                    gap_type=CaseGapType.UNSUPPORTED_MATERIAL_FACT,
                    description="Material fact has no supporting evidence item.",
                    side=record.supporting_side,
                    matter_id=record.matter_id,
                    element_id=record.element_id,
                    fact_ids=(record.fact_id,),
                    witness_ids=record.knowledgeable_witness_ids,
                    source_ids=(record.fact_id, record.element_id),
                    derivation_method=DERIVATION_METHOD,
                    confidence_score=HIGH_CONFIDENCE,
                    severity=0.8,
                )
            )
        if not record.knowledgeable_witness_ids:
            gaps.append(
                CaseGap(
                    gap_id=f"GAP-{record.fact_id}-NO-WITNESS",
                    gap_type=CaseGapType.MISSING_FOUNDATION,
                    description="Material fact has no witness knowledge source.",
                    side=record.supporting_side,
                    matter_id=record.matter_id,
                    element_id=record.element_id,
                    fact_ids=(record.fact_id,),
                    evidence_ids=record.supporting_evidence_ids,
                    source_ids=(record.fact_id, record.element_id),
                    derivation_method=DERIVATION_METHOD,
                    confidence_score=HIGH_CONFIDENCE,
                    severity=0.8,
                )
            )
        if len(record.knowledgeable_witness_ids) == 1:
            gaps.append(
                CaseGap(
                    gap_id=f"GAP-{record.fact_id}-ONE-WITNESS",
                    gap_type=CaseGapType.ONE_WITNESS_DEPENDENCY,
                    description="Material fact depends on one witness.",
                    side=record.supporting_side,
                    matter_id=record.matter_id,
                    element_id=record.element_id,
                    fact_ids=(record.fact_id,),
                    witness_ids=record.knowledgeable_witness_ids,
                    source_ids=(record.fact_id, *record.knowledgeable_witness_ids),
                    derivation_method=DERIVATION_METHOD,
                    confidence_score=HIGH_CONFIDENCE,
                    severity=0.5,
                )
            )
        if len(record.supporting_evidence_ids) == 1:
            gaps.append(
                CaseGap(
                    gap_id=f"GAP-{record.fact_id}-WEAK-CORROBORATION",
                    gap_type=CaseGapType.WEAK_CORROBORATION,
                    description=(
                        "Material fact has only one corroborating evidence item."
                    ),
                    side=record.supporting_side,
                    matter_id=record.matter_id,
                    element_id=record.element_id,
                    fact_ids=(record.fact_id,),
                    evidence_ids=record.supporting_evidence_ids,
                    source_ids=(record.fact_id, *record.supporting_evidence_ids),
                    derivation_method=DERIVATION_METHOD,
                    confidence_score=HIGH_CONFIDENCE,
                    severity=0.4,
                )
            )

    for contradiction in contradiction_graph.contradictions:
        gaps.append(
            CaseGap(
                gap_id=f"GAP-{contradiction.contradiction_id}-OPPORTUNITY",
                gap_type=CaseGapType.CONTRADICTION_OPPORTUNITY,
                description="Expected contradiction should be tested through strategy.",
                fact_ids=contradiction.fact_ids,
                evidence_ids=contradiction.evidence_ids,
                witness_ids=contradiction.witness_ids,
                source_ids=(contradiction.contradiction_id, *contradiction.source_ids),
                derivation_method=DERIVATION_METHOD,
                confidence_score=MEDIUM_CONFIDENCE,
                severity=0.7,
            )
        )
    return tuple(gaps)


def validate_case_intelligence(
    normalized: NormalizedCase, report: CaseIntelligenceReport
) -> CaseIntelligenceReport:
    fact_ids = set(normalized.facts_by_id)
    evidence_ids = {item.evidence_id for item in normalized.template.evidence}
    witness_ids = {witness.witness_id for witness in normalized.template.witnesses}
    element_ids = set(normalized.elements_by_id)
    node_ids = {node.node_id for node in report.case_graph.nodes}

    for edge in report.case_graph.edges:
        _require(
            edge.confidence_score is not None,
            "case graph edge missing confidence",
        )
        _require(
            edge.source_node_id in node_ids,
            f"dangling graph source: {edge.edge_id}",
        )
        _require(
            edge.target_node_id in node_ids,
            f"dangling graph target: {edge.edge_id}",
        )
    for record in report.material_fact_map.facts:
        _require(
            record.fact_id in fact_ids,
            f"dangling material fact: {record.fact_id}",
        )
        _require(
            record.element_id in element_ids,
            f"dangling material element: {record.element_id}",
        )
        _require(
            bool(record.source_ids),
            f"material fact missing provenance: {record.fact_id}",
        )
        for evidence_id in record.supporting_evidence_ids:
            _require(
                evidence_id in evidence_ids,
                f"dangling material evidence: {evidence_id}",
            )
        for witness_id in record.knowledgeable_witness_ids:
            _require(
                witness_id in witness_ids,
                f"dangling material witness: {witness_id}",
            )
    for relationship in report.evidence_graph.relationships:
        _require(
            relationship.evidence_id in evidence_ids,
            f"dangling evidence relationship source: {relationship.relationship_id}",
        )
        if relationship.fact_id is not None:
            _require(
                relationship.fact_id in fact_ids,
                f"dangling evidence fact: {relationship.fact_id}",
            )
        if relationship.element_id is not None:
            _require(
                relationship.element_id in element_ids,
                f"dangling evidence element: {relationship.element_id}",
            )
        if relationship.witness_id is not None:
            _require(
                relationship.witness_id in witness_ids,
                f"dangling evidence witness: {relationship.witness_id}",
            )
    for relationship in report.witness_knowledge_graph.relationships:
        _require(
            relationship.witness_id in witness_ids,
            f"dangling witness knowledge witness: {relationship.relationship_id}",
        )
        _require(
            relationship.fact_id in fact_ids,
            f"dangling witness knowledge fact: {relationship.fact_id}",
        )
        _require(
            bool(relationship.source_ids),
            f"witness edge missing provenance: {relationship.relationship_id}",
        )
    for contradiction in report.contradiction_graph.contradictions:
        _require(
            bool(contradiction.source_ids),
            f"contradiction missing provenance: {contradiction.contradiction_id}",
        )
        for fact_id in contradiction.fact_ids:
            _require(fact_id in fact_ids, f"dangling contradiction fact: {fact_id}")
        for evidence_id in contradiction.evidence_ids:
            _require(
                evidence_id in evidence_ids,
                f"dangling contradiction evidence: {evidence_id}",
            )
        for witness_id in contradiction.witness_ids:
            _require(
                witness_id in witness_ids,
                f"dangling contradiction witness: {witness_id}",
            )
    for gap in report.case_gaps:
        _require(bool(gap.source_ids), f"gap missing provenance: {gap.gap_id}")
    return report


def _template_from_package(package: CompiledCasePackage) -> AuthoredCaseTemplate:
    return AuthoredCaseTemplate(
        metadata=package.metadata,
        parties=package.parties,
        actors=package.actors,
        matters=package.matters,
        facts=package.facts,
        evidence=package.evidence,
        witnesses=package.witnesses,
        witness_knowledge=package.witness_knowledge,
        private_truth=package.private_truth,
    )


def _node(
    node_id: str,
    node_type: CaseGraphNodeType,
    label: str,
    source_ids: tuple[str, ...],
) -> CaseGraphNode:
    return CaseGraphNode(
        node_id=node_id,
        node_type=node_type,
        label=label,
        source_ids=source_ids,
        derivation_method=DERIVATION_METHOD,
        confidence_score=HIGH_CONFIDENCE,
    )


def _edge(
    edge_id: str,
    edge_type: CaseGraphEdgeType,
    source_node_id: str,
    target_node_id: str,
    source_ids: tuple[str, ...],
) -> CaseGraphEdge:
    return CaseGraphEdge(
        edge_id=edge_id,
        edge_type=edge_type,
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        source_ids=source_ids,
        derivation_method=DERIVATION_METHOD,
        confidence_score=HIGH_CONFIDENCE,
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


__all__ = [
    "analyze_case",
    "analyze_case_gaps",
    "build_evidence_graph",
    "build_timeline_graph",
    "build_witness_knowledge_graph",
    "classify_material_facts",
    "detect_contradictions",
    "identify_legal_issues",
    "map_legal_elements",
    "normalize_case",
    "validate_case_intelligence",
]
