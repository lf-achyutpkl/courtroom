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
                    ideal_action=(
                        "Establish the cashier recognizes the camera angle before "
                        "using the clip."
                    ),
                ),
            ),
        ),
    )


def build_case_intelligence_civil_case() -> AuthoredCaseTemplate:
    return build_reference_case()


def build_case_intelligence_criminal_case() -> AuthoredCaseTemplate:
    prosecution = Party(
        party_id="PTY-PROSECUTION",
        name="People of California",
        side=PartySide.PROSECUTION,
    )
    defense = Party(
        party_id="PTY-DEFENSE",
        name="Alex Rivera",
        side=PartySide.DEFENSE,
    )
    identity = LegalElement(
        element_id="ELM-IDENTITY",
        label="Identity",
        description="Defendant was the person who took the property.",
        burden="beyond_reasonable_doubt",
        proving_side=PartySide.PROSECUTION,
    )
    intent = LegalElement(
        element_id="ELM-INTENT",
        label="Intent",
        description="Defendant intended to deprive the owner of the property.",
        burden="beyond_reasonable_doubt",
        proving_side=PartySide.PROSECUTION,
    )
    camera_fact = Fact(
        fact_id="FAC-CAMERA-MATCH",
        text="Security footage shows a jacket matching Alex Rivera.",
        visibility=VisibilityScope.PUBLIC_CASE,
        supports_element_ids=("ELM-IDENTITY",),
    )
    receipt_fact = Fact(
        fact_id="FAC-RECEIPT-ALIBI",
        text="A receipt places Alex across town near the same time.",
        visibility=VisibilityScope.DEFENSE_PRIVATE,
        supports_element_ids=("ELM-IDENTITY",),
    )
    intent_fact = Fact(
        fact_id="FAC-CONCEALED-ITEM",
        text="The item was placed inside a backpack before exit.",
        visibility=VisibilityScope.PUBLIC_CASE,
        supports_element_ids=("ELM-INTENT",),
    )
    video = EvidenceItem(
        evidence_id="EVD-STORE-VIDEO",
        title="Store security video",
        description="Video captures the suspect at the aisle and exit.",
        offered_by=PartySide.PROSECUTION,
        supports_fact_ids=("FAC-CAMERA-MATCH", "FAC-CONCEALED-ITEM"),
    )
    receipt = EvidenceItem(
        evidence_id="EVD-RECEIPT",
        title="Cafe receipt",
        description="Timestamped receipt from a cafe across town.",
        offered_by=PartySide.DEFENSE,
        visibility=VisibilityScope.DEFENSE_PRIVATE,
        supports_fact_ids=("FAC-RECEIPT-ALIBI",),
    )
    guard_atom = KnowledgeAtom(
        knowledge_atom_id="KNO-GUARD-VIDEO",
        witness_id="WIT-SECURITY",
        text="The guard can identify the store camera system and timestamp.",
        related_fact_ids=("FAC-CAMERA-MATCH", "FAC-CONCEALED-ITEM"),
    )
    defendant_atom = KnowledgeAtom(
        knowledge_atom_id="KNO-DEFENDANT-RECEIPT",
        witness_id="WIT-DEFENDANT",
        text="Alex says the cafe receipt is his and matches his card.",
        related_fact_ids=("FAC-RECEIPT-ALIBI",),
    )
    return AuthoredCaseTemplate(
        metadata=CaseMetadata(
            case_id="CASE-RIVERA-THEFT",
            title="People v. Rivera",
            case_kind=CaseKind.CRIMINAL,
        ),
        parties=(prosecution, defense),
        actors=(
            Actor(
                actor_id="ACT-PROSECUTOR",
                role=ActorRole.PROSECUTION_LAWYER,
                name="Prosecutor",
                party_id=prosecution.party_id,
            ),
            Actor(
                actor_id="ACT-DEFENSE-LAWYER",
                role=ActorRole.DEFENSE_LAWYER,
                name="Defense counsel",
                party_id=defense.party_id,
            ),
            Actor(
                actor_id="ACT-SECURITY",
                role=ActorRole.WITNESS,
                name="Nina Shah",
                witness_id="WIT-SECURITY",
            ),
            Actor(
                actor_id="ACT-DEFENDANT",
                role=ActorRole.WITNESS,
                name="Alex Rivera",
                witness_id="WIT-DEFENDANT",
            ),
        ),
        matters=(
            ClaimOrCharge(
                matter_id="CHG-THEFT",
                case_kind=CaseKind.CRIMINAL,
                title="Theft",
                elements=(identity, intent),
            ),
        ),
        facts=(camera_fact, receipt_fact, intent_fact),
        evidence=(video, receipt),
        witnesses=(
            Witness(
                witness_id="WIT-SECURITY",
                name="Nina Shah",
                called_by=PartySide.PROSECUTION,
                public_summary="Security guard familiar with the store cameras.",
                knowledge_atom_ids=("KNO-GUARD-VIDEO",),
            ),
            Witness(
                witness_id="WIT-DEFENDANT",
                name="Alex Rivera",
                called_by=PartySide.DEFENSE,
                public_summary="Defendant with alibi receipt knowledge.",
                knowledge_atom_ids=("KNO-DEFENDANT-RECEIPT",),
            ),
        ),
        witness_knowledge=(guard_atom, defendant_atom),
        private_truth=PrivateSimulationTruth(
            ground_truth_summary=(
                "The video is ambiguous; the receipt may create doubt."
            ),
            expected_contradictions=(
                ExpectedContradiction(
                    contradiction_id="CON-VIDEO-RECEIPT",
                    description=(
                        "The receipt timing conflicts with the prosecution identity "
                        "theory."
                    ),
                    involved_fact_ids=("FAC-CAMERA-MATCH", "FAC-RECEIPT-ALIBI"),
                ),
            ),
        ),
    )
