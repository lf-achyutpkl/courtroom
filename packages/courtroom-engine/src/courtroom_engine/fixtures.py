from __future__ import annotations

from .models import (
    Actor,
    ActorRole,
    AuthoredCaseTemplate,
    CaseKind,
    CaseMetadata,
    ClaimOrCharge,
    CoachingReference,
    EvidenceItem,
    ExpectedContradiction,
    Fact,
    KnowledgeAtom,
    LegalElement,
    Party,
    PartySide,
    PrivateSimulationTruth,
    VisibilityScope,
    Witness,
)


def build_reference_case() -> AuthoredCaseTemplate:
    plaintiff = Party(
        party_id="PTY-PLAINTIFF",
        name="Morgan Lee",
        side=PartySide.PLAINTIFF,
    )
    defense = Party(
        party_id="PTY-DEFENSE",
        name="Harbor Market LLC",
        side=PartySide.DEFENSE,
    )
    element = LegalElement(
        element_id="ELM-NOTICE",
        label="Notice",
        description="Defendant had actual or constructive notice of the hazard.",
        burden="preponderance",
        proving_side=PartySide.PLAINTIFF,
    )
    fact = Fact(
        fact_id="FAC-SPILL-NOTICED",
        text="A store employee saw the spill before the fall.",
        visibility=VisibilityScope.PUBLIC_CASE,
        supports_element_ids=("ELM-NOTICE",),
    )
    private_fact = Fact(
        fact_id="FAC-DEFENSE-INSPECTION",
        text="Defense log says the aisle was inspected ten minutes earlier.",
        visibility=VisibilityScope.DEFENSE_PRIVATE,
        supports_element_ids=("ELM-NOTICE",),
    )
    evidence = EvidenceItem(
        evidence_id="EVD-CAMERA",
        title="Aisle camera clip",
        description="Video shows an employee walking past the spill.",
        offered_by=PartySide.PLAINTIFF,
        supports_fact_ids=("FAC-SPILL-NOTICED",),
    )
    knowledge = KnowledgeAtom(
        knowledge_atom_id="KNO-CASHIER-SAW-SPILL",
        witness_id="WIT-CASHIER",
        text="The cashier remembers seeing liquid near aisle three.",
        related_fact_ids=("FAC-SPILL-NOTICED",),
    )
    return AuthoredCaseTemplate(
        metadata=CaseMetadata(
            case_id="CASE-HARBOR-MARKET",
            title="Lee v. Harbor Market",
            case_kind=CaseKind.CIVIL,
        ),
        parties=(plaintiff, defense),
        actors=(
            Actor(
                actor_id="ACT-PLAINTIFF-LAWYER",
                role=ActorRole.PLAINTIFF_LAWYER,
                name="Plaintiff counsel",
                party_id=plaintiff.party_id,
            ),
            Actor(
                actor_id="ACT-DEFENSE-LAWYER",
                role=ActorRole.DEFENSE_LAWYER,
                name="Defense counsel",
                party_id=defense.party_id,
            ),
            Actor(
                actor_id="ACT-CASHIER",
                role=ActorRole.WITNESS,
                name="Riley Chen",
                witness_id="WIT-CASHIER",
            ),
            Actor(
                actor_id="ACT-JUDGE",
                role=ActorRole.TRIAL_JUDGE,
                name="Judge",
            ),
        ),
        matters=(
            ClaimOrCharge(
                matter_id="CLM-NEGLIGENCE",
                case_kind=CaseKind.CIVIL,
                title="Negligence",
                elements=(element,),
            ),
        ),
        facts=(fact, private_fact),
        evidence=(evidence,),
        witnesses=(
            Witness(
                witness_id="WIT-CASHIER",
                name="Riley Chen",
                called_by=PartySide.PLAINTIFF,
                public_summary="Cashier working during the incident.",
                knowledge_atom_ids=("KNO-CASHIER-SAW-SPILL",),
            ),
        ),
        witness_knowledge=(knowledge,),
        private_truth=PrivateSimulationTruth(
            ground_truth_summary="The employee saw the spill and did not clean it.",
            expected_contradictions=(
                ExpectedContradiction(
                    contradiction_id="CON-INSPECTION-VIDEO",
                    description="Inspection log timing conflicts with the camera clip.",
                    involved_fact_ids=("FAC-SPILL-NOTICED", "FAC-DEFENSE-INSPECTION"),
                ),
            ),
            coaching_references=(
                CoachingReference(
                    objective_id="OBJ-AUTHENTICATE-CAMERA",
                    label="Authenticate camera clip through cashier",
                    ideal_action="Establish the cashier recognizes the camera angle before using the clip.",
                ),
            ),
        ),
    )
