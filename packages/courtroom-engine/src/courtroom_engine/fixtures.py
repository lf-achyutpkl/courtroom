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


def build_balanced_prototype_theft_case() -> AuthoredCaseTemplate:
    """Return a contested criminal case where advocacy around timing is decisive."""
    prosecution = Party(
        party_id="PTY-PROSECUTION",
        name="People of California",
        side=PartySide.PROSECUTION,
    )
    defense = Party(
        party_id="PTY-DEFENSE",
        name="Rowan Keene",
        side=PartySide.DEFENSE,
    )
    identity = LegalElement(
        element_id="ELM-IDENTITY",
        label="Identity",
        description="Rowan Keene was the person who removed the prototype.",
        burden="beyond_reasonable_doubt",
        proving_side=PartySide.PROSECUTION,
    )
    intent = LegalElement(
        element_id="ELM-INTENT",
        label="Intent to deprive",
        description="The removal was without permission and intended to deprive the owner.",
        burden="beyond_reasonable_doubt",
        proving_side=PartySide.PROSECUTION,
    )
    badge_log = Fact(
        fact_id="FAC-BADGE-ACCESS",
        text="A badge assigned to Rowan Keene opened the incubator lab at 9:17 p.m.",
        supports_element_ids=("ELM-IDENTITY",),
    )
    corridor_video = Fact(
        fact_id="FAC-CORRIDOR-VIDEO",
        text="Corridor video shows a person in Rowan's distinctive jacket leaving with a hard case.",
        supports_element_ids=("ELM-IDENTITY", "ELM-INTENT"),
    )
    payment_dispute = Fact(
        fact_id="FAC-PAYMENT-DISPUTE",
        text="Rowan had argued that the startup owed overdue consulting fees.",
        supports_element_ids=("ELM-INTENT",),
    )
    shared_badge = Fact(
        fact_id="FAC-SHARED-BADGE",
        text="The lab team sometimes shared badges when working late.",
        visibility=VisibilityScope.DEFENSE_PRIVATE,
        supports_element_ids=("ELM-IDENTITY",),
    )
    clock_offset = Fact(
        fact_id="FAC-CLOCK-OFFSET",
        text="The access-control server may have run eleven minutes ahead of the corridor camera.",
        visibility=VisibilityScope.DEFENSE_PRIVATE,
        supports_element_ids=("ELM-IDENTITY",),
    )
    consent_message = Fact(
        fact_id="FAC-CONSENT-MESSAGE",
        text="A project lead had previously told Rowan to collect personal equipment from the lab.",
        visibility=VisibilityScope.DEFENSE_PRIVATE,
        supports_element_ids=("ELM-INTENT",),
    )
    access_log = EvidenceItem(
        evidence_id="EVD-ACCESS-LOG",
        title="Incubator badge-access export",
        description="System export recording the badge event at 9:17 p.m.",
        offered_by=PartySide.PROSECUTION,
        supports_fact_ids=("FAC-BADGE-ACCESS",),
    )
    video = EvidenceItem(
        evidence_id="EVD-CORRIDOR-VIDEO",
        title="Corridor camera clip",
        description="Low-resolution footage of a person carrying a hard case.",
        offered_by=PartySide.PROSECUTION,
        supports_fact_ids=("FAC-CORRIDOR-VIDEO",),
    )
    colleague_message = EvidenceItem(
        evidence_id="EVD-PAYMENT-MESSAGES",
        title="Consulting-fee messages",
        description="Messages reflecting the parties' dispute over unpaid consulting fees.",
        offered_by=PartySide.PROSECUTION,
        supports_fact_ids=("FAC-PAYMENT-DISPUTE",),
    )
    system_report = EvidenceItem(
        evidence_id="EVD-SYSTEM-REPORT",
        title="Access-control maintenance report",
        description="Maintenance report relevant to whether the access and camera clocks matched.",
        offered_by=PartySide.DEFENSE,
        visibility=VisibilityScope.DEFENSE_PRIVATE,
        supports_fact_ids=("FAC-CLOCK-OFFSET",),
    )
    project_message = EvidenceItem(
        evidence_id="EVD-PROJECT-MESSAGE",
        title="Project lead message",
        description="Message about Rowan retrieving personal equipment from the lab.",
        offered_by=PartySide.DEFENSE,
        visibility=VisibilityScope.DEFENSE_PRIVATE,
        supports_fact_ids=("FAC-CONSENT-MESSAGE",),
    )
    security_knowledge = KnowledgeAtom(
        knowledge_atom_id="KNO-SECURITY-BADGES",
        witness_id="WIT-SECURITY-ADMIN",
        text="The security administrator knows the badge export procedure and that badges were sometimes shared informally.",
        related_fact_ids=("FAC-BADGE-ACCESS", "FAC-SHARED-BADGE"),
    )
    technician_knowledge = KnowledgeAtom(
        knowledge_atom_id="KNO-TECHNICIAN-CLOCKS",
        witness_id="WIT-SYSTEMS-TECHNICIAN",
        text="The systems technician can explain whether the two systems were synchronized on the relevant date.",
        related_fact_ids=("FAC-CLOCK-OFFSET", "FAC-CORRIDOR-VIDEO"),
    )
    project_lead_knowledge = KnowledgeAtom(
        knowledge_atom_id="KNO-PROJECT-LEAD-CONSENT",
        witness_id="WIT-PROJECT-LEAD",
        text="The project lead remembers the payment dispute and the prior message about personal equipment.",
        related_fact_ids=("FAC-PAYMENT-DISPUTE", "FAC-CONSENT-MESSAGE"),
    )
    return AuthoredCaseTemplate(
        metadata=CaseMetadata(
            case_id="CASE-KEENE-PROTOTYPE-THEFT",
            title="People v. Keene",
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
                actor_id="ACT-SECURITY-ADMIN",
                role=ActorRole.WITNESS,
                name="Morgan Ibarra",
                witness_id="WIT-SECURITY-ADMIN",
            ),
            Actor(
                actor_id="ACT-SYSTEMS-TECHNICIAN",
                role=ActorRole.WITNESS,
                name="Samira Holt",
                witness_id="WIT-SYSTEMS-TECHNICIAN",
            ),
            Actor(
                actor_id="ACT-PROJECT-LEAD",
                role=ActorRole.WITNESS,
                name="Devon Price",
                witness_id="WIT-PROJECT-LEAD",
            ),
            Actor(actor_id="ACT-JUDGE", role=ActorRole.TRIAL_JUDGE, name="Judge"),
        ),
        matters=(
            ClaimOrCharge(
                matter_id="CHG-PROTOTYPE-THEFT",
                case_kind=CaseKind.CRIMINAL,
                title="Theft of a prototype",
                elements=(identity, intent),
            ),
        ),
        facts=(badge_log, corridor_video, payment_dispute, shared_badge, clock_offset, consent_message),
        evidence=(access_log, video, colleague_message, system_report, project_message),
        witnesses=(
            Witness(
                witness_id="WIT-SECURITY-ADMIN",
                name="Morgan Ibarra",
                called_by=PartySide.PROSECUTION,
                public_summary="Security administrator familiar with badge access records.",
                knowledge_atom_ids=("KNO-SECURITY-BADGES",),
            ),
            Witness(
                witness_id="WIT-SYSTEMS-TECHNICIAN",
                name="Samira Holt",
                called_by=PartySide.DEFENSE,
                public_summary="Systems technician familiar with the access and camera clocks.",
                knowledge_atom_ids=("KNO-TECHNICIAN-CLOCKS",),
            ),
            Witness(
                witness_id="WIT-PROJECT-LEAD",
                name="Devon Price",
                called_by=PartySide.DEFENSE,
                public_summary="Project lead who discussed payment and equipment with Rowan.",
                knowledge_atom_ids=("KNO-PROJECT-LEAD-CONSENT",),
            ),
        ),
        witness_knowledge=(security_knowledge, technician_knowledge, project_lead_knowledge),
        private_truth=PrivateSimulationTruth(
            ground_truth_summary=(
                "The available record does not resolve who entered the lab or whether the removal was authorized; "
                "the access-and-timing evidence must be tested at trial."
            ),
            expected_contradictions=(
                ExpectedContradiction(
                    contradiction_id="CON-ACCESS-CLOCKS",
                    description="The badge record and corridor video support identity only if their timestamps can be reliably aligned.",
                    involved_fact_ids=("FAC-BADGE-ACCESS", "FAC-CORRIDOR-VIDEO", "FAC-CLOCK-OFFSET"),
                ),
                ExpectedContradiction(
                    contradiction_id="CON-MOTIVE-CONSENT",
                    description="The payment dispute can suggest motive, but the project-lead message may support authorized retrieval.",
                    involved_fact_ids=("FAC-PAYMENT-DISPUTE", "FAC-CONSENT-MESSAGE"),
                ),
            ),
            coaching_references=(
                CoachingReference(
                    objective_id="OBJ-AUTHENTICATE-TIMELINE",
                    label="Authenticate the timeline",
                    ideal_action="Establish or challenge synchronization before relying on the access-and-video timeline.",
                ),
                CoachingReference(
                    objective_id="OBJ-TEST-CONSENT",
                    label="Test authorization",
                    ideal_action="Connect any authorization message to the prototype and the relevant time window before arguing intent.",
                ),
            ),
        ),
    )
