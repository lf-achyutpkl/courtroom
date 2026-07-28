# V2 Case Model and Context Boundary Design

## 1. V2 Scope

V2 is a controlled courtroom training and coaching platform built around internally authored case templates.

A V2 case should provide enough information to support:

* Plaintiff and defense case analysis.
* Legal element mapping.
* Competing case theories.
* Witness planning.
* Direct and cross-examination.
* Evidence authentication and objections.
* Contradiction detection.
* Jury instructions.
* Jury deliberation.
* Verdict validation.
* Lawyer evaluation.
* Missed-opportunity detection.
* Actionable coaching.
* Reproducible simulations.

The case package should be designed for:

```text
Case authors
    ↓
Canonical case package
    ↓
Validation and compilation
    ↓
Role-specific views
    ↓
Node-specific context packages
    ↓
LLM calls
```

The canonical package must never be passed directly to an actor model.

---

# 2. Recommended Model Layers

Do not place everything in one `CaseFile`.

Use five separate layers:

```text
1. Authored Case Template
       ↓
2. Compiled Case Model
       ↓
3. Derived Case Intelligence
       ↓
4. Private Simulation Truth
       ↓
5. Runtime Trial State
```

## Layer 1: Authored Case Template

What your case author enters.

It should be readable, editable, and relatively simple.

## Layer 2: Compiled Case Model

A normalized and validated version with stable IDs and resolved relationships.

## Layer 3: Derived Case Intelligence

Case graphs, contradiction candidates, legal-element matrices, and generated planning inputs.

## Layer 4: Private Simulation Truth

Evaluator-only truth, intended witness behaviour, expected strategies, and coaching references.

## Layer 5: Runtime Trial State

What actually happens during one simulation.

Keeping these layers separate prevents authored expectations from being confused with facts established during the trial.

---

# 3. Package Structure

```text
courtroom_engine/
└── domain/
    ├── common/
    │   ├── identifiers.py
    │   ├── provenance.py
    │   └── visibility.py
    │
    ├── case/
    │   ├── template.py
    │   ├── metadata.py
    │   ├── parties.py
    │   ├── claims.py
    │   ├── facts.py
    │   ├── events.py
    │   └── compiled.py
    │
    ├── evidence/
    │   ├── evidence.py
    │   ├── foundation.py
    │   ├── admissibility.py
    │   └── runtime.py
    │
    ├── witnesses/
    │   ├── profile.py
    │   ├── knowledge.py
    │   ├── statements.py
    │   └── runtime.py
    │
    ├── legal/
    │   ├── jurisdiction.py
    │   ├── authority.py
    │   ├── jury_instruction.py
    │   └── legal_snapshot.py
    │
    ├── strategy/
    │   ├── theory.py
    │   ├── objective.py
    │   ├── plans.py
    │   └── runtime.py
    │
    ├── simulation/
    │   ├── hidden_truth.py
    │   ├── expected_paths.py
    │   └── coaching_reference.py
    │
    ├── trial/
    │   ├── procedure.py
    │   ├── record.py
    │   ├── events.py
    │   └── state.py
    │
    └── context/
        ├── role_views.py
        ├── node_contexts.py
        ├── policies.py
        └── boundaries.py
```

---

# 4. Shared Base Types

```python
from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
```

Use immutable domain models where practical:

```python
class DomainModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=True,
    )
```

`extra="forbid"` is important because a misspelled field should fail validation rather than silently disappear.

---

# 5. IDs and References

Do not use unrestricted strings everywhere.

```python
CaseId = Annotated[str, Field(pattern=r"^CASE-[A-Z0-9-]+$")]
PartyId = Annotated[str, Field(pattern=r"^PTY-[A-Z0-9-]+$")]
ActorId = Annotated[str, Field(pattern=r"^ACT-[A-Z0-9-]+$")]
ClaimId = Annotated[str, Field(pattern=r"^CLM-[A-Z0-9-]+$")]
ElementId = Annotated[str, Field(pattern=r"^ELM-[A-Z0-9-]+$")]
FactId = Annotated[str, Field(pattern=r"^FAC-[A-Z0-9-]+$")]
EventId = Annotated[str, Field(pattern=r"^EVT-[A-Z0-9-]+$")]
EvidenceId = Annotated[str, Field(pattern=r"^EVD-[A-Z0-9-]+$")]
WitnessId = Annotated[str, Field(pattern=r"^WIT-[A-Z0-9-]+$")]
StatementId = Annotated[str, Field(pattern=r"^STM-[A-Z0-9-]+$")]
ObjectiveId = Annotated[str, Field(pattern=r"^OBJ-[A-Z0-9-]+$")]
AuthorityId = Annotated[str, Field(pattern=r"^LAW-[A-Z0-9-]+$")]
InstructionId = Annotated[str, Field(pattern=r"^INS-[A-Z0-9-]+$")]
```

This improves:

* Referential integrity.
* Logging.
* Evaluation citations.
* Prompt grounding.
* Test readability.
* Event replay.

---

# 6. Visibility and Information Control

Visibility must be explicit on information-bearing objects.

```python
class VisibilityScope(StrEnum):
    PUBLIC_CASE = "public_case"
    PLAINTIFF_PRIVATE = "plaintiff_private"
    DEFENSE_PRIVATE = "defense_private"
    WITNESS_PRIVATE = "witness_private"
    JUDGE_ONLY = "judge_only"
    JURY_RECORD_ONLY = "jury_record_only"
    EVALUATOR_ONLY = "evaluator_only"
    COACH_ONLY = "coach_only"
```

```python
class DisclosureRule(DomainModel):
    initial_scopes: frozenset[VisibilityScope]

    disclosed_to_actor_ids: frozenset[ActorId] = frozenset()
    disclosed_to_party_ids: frozenset[PartyId] = frozenset()

    becomes_public_on_event_types: frozenset[str] = frozenset()
    becomes_jury_visible_when_admitted: bool = False

    notes: str | None = None
```

Do not rely only on a simple `visible_to` list because visibility can change during the trial.

For example:

```text
Before testimony:
A prior statement is available only to defense counsel.

After proper impeachment:
Parts of the statement become part of the trial record.

After admission:
The jury may consider it for a configured purpose.
```

---

# 7. Case Metadata and Trial Profile

```python
class CaseCategory(StrEnum):
    CIVIL = "civil"
    CRIMINAL = "criminal"
```

```python
class FactFinder(StrEnum):
    JURY = "jury"
    JUDGE = "judge"
```

```python
class CaseMetadata(DomainModel):
    case_id: CaseId
    title: str
    summary: str
    category: CaseCategory

    difficulty: Literal[
        "introductory",
        "intermediate",
        "advanced",
        "expert",
    ]

    learning_tags: tuple[str, ...] = ()
    author_version: str
    schema_version: str
```

```python
class JurisdictionRef(DomainModel):
    country_code: str
    state_or_region: str | None
    court_system: str
    court_level: str
    venue: str | None = None

    jurisdiction_pack_id: str
    jurisdiction_pack_version: str
```

```python
class TrialScope(DomainModel):
    starts_at_phase: str
    ends_at_phase: str

    included_phases: tuple[str, ...]
    excluded_phases: tuple[str, ...]

    include_redirect: bool = True
    include_recross: bool = False
    include_rebuttal_case: bool = True
    include_closing_rebuttal: bool = True
```

```python
class TrialProfile(DomainModel):
    jurisdiction: JurisdictionRef
    fact_finder: FactFinder

    case_category: CaseCategory
    procedural_posture: str
    trial_scope: TrialScope

    burden_definition_ids: tuple[str, ...]
    jury_instruction_ids: tuple[InstructionId, ...] = ()
    verdict_form_id: str | None = None
```

For your initial implementation:

```python
CALIFORNIA_CIVIL_JURY_PROFILE = TrialProfile(
    jurisdiction=JurisdictionRef(
        country_code="US",
        state_or_region="California",
        court_system="California State Courts",
        court_level="Superior Court",
        jurisdiction_pack_id="JUR-US-CA-CIVIL",
        jurisdiction_pack_version="2026.1",
    ),
    fact_finder=FactFinder.JURY,
    case_category=CaseCategory.CIVIL,
    procedural_posture="civil_trial",
    trial_scope=TrialScope(
        starts_at_phase="preliminary_jury_instructions",
        ends_at_phase="verdict",
        included_phases=(
            "preliminary_jury_instructions",
            "opening_statements",
            "plaintiff_case_in_chief",
            "defense_case_in_chief",
            "rebuttal_case",
            "closing_arguments",
            "final_jury_instructions",
            "jury_deliberation",
            "verdict",
        ),
        excluded_phases=(
            "pleadings",
            "discovery",
            "summary_judgment",
            "motions_in_limine",
            "voir_dire",
            "post_trial_motions",
        ),
    ),
    burden_definition_ids=("BURDEN-PREPONDERANCE",),
)
```

California publishes official civil jury instructions and verdict forms through CACI. The current 2026 edition is therefore an appropriate authoritative foundation for a California civil jury training profile.

---

# 8. Parties and Actors

Separate legal parties from courtroom actors.

A company is a party. Its lawyer and employees are actors.

```python
class PartySide(StrEnum):
    PLAINTIFF = "plaintiff"
    DEFENSE = "defense"
    PROSECUTION = "prosecution"
```

```python
class PartyType(StrEnum):
    PERSON = "person"
    ORGANIZATION = "organization"
    GOVERNMENT = "government"
```

```python
class Party(DomainModel):
    party_id: PartyId
    name: str
    party_type: PartyType
    side: PartySide

    description: str
    represented_by_actor_ids: tuple[ActorId, ...] = ()
```

```python
class ActorRole(StrEnum):
    PLAINTIFF_LAWYER = "plaintiff_lawyer"
    DEFENSE_LAWYER = "defense_lawyer"
    PROSECUTOR = "prosecutor"

    WITNESS = "witness"
    TRIAL_JUDGE = "trial_judge"
    JUROR = "juror"

    EVALUATOR = "evaluator"
    COACH = "coach"
```

```python
class ActorProfile(DomainModel):
    actor_id: ActorId
    display_name: str
    role: ActorRole

    party_id: PartyId | None = None
    witness_id: WitnessId | None = None

    role_contract_id: str
    behavior_profile_id: str | None = None
```

---

# 9. Claims, Defenses, Elements, and Burdens

## 9.1 Burden definition

```python
class StandardOfProof(StrEnum):
    PREPONDERANCE = "preponderance_of_evidence"
    CLEAR_AND_CONVINCING = "clear_and_convincing"
    BEYOND_REASONABLE_DOUBT = "beyond_reasonable_doubt"
```

```python
class BurdenDefinition(DomainModel):
    burden_id: str
    bearer_party_id: PartyId
    standard: StandardOfProof

    description: str
    instruction_id: InstructionId | None = None
```

## 9.2 Legal element

```python
class ElementStatus(StrEnum):
    UNASSESSED = "unassessed"
    SUPPORTED = "supported"
    CONTESTED = "contested"
    WEAK = "weak"
    UNSUPPORTED = "unsupported"
    ESTABLISHED_AT_TRIAL = "established_at_trial"
    NOT_ESTABLISHED_AT_TRIAL = "not_established_at_trial"
```

```python
class LegalElement(DomainModel):
    element_id: ElementId
    name: str
    description: str

    burden_id: str
    defining_authority_ids: tuple[AuthorityId, ...]
    jury_instruction_ids: tuple[InstructionId, ...] = ()

    required_for_claim_ids: tuple[ClaimId, ...] = ()
    negated_by_defense_ids: tuple[str, ...] = ()
```

## 9.3 Claim

```python
class Claim(DomainModel):
    claim_id: ClaimId
    name: str
    description: str

    asserted_by_party_id: PartyId
    against_party_ids: tuple[PartyId, ...]

    element_ids: tuple[ElementId, ...]
    requested_relief_ids: tuple[str, ...]

    legal_authority_ids: tuple[AuthorityId, ...]
```

## 9.4 Defense

```python
class DefenseTheoryType(StrEnum):
    ELEMENT_DENIAL = "element_denial"
    AFFIRMATIVE_DEFENSE = "affirmative_defense"
    COMPARATIVE_FAULT = "comparative_fault"
    CREDIBILITY_ATTACK = "credibility_attack"
    ALTERNATIVE_CAUSATION = "alternative_causation"
```

```python
class Defense(DomainModel):
    defense_id: str
    name: str
    description: str

    asserted_by_party_id: PartyId
    defense_type: DefenseTheoryType

    affected_claim_ids: tuple[ClaimId, ...]
    affected_element_ids: tuple[ElementId, ...]

    own_element_ids: tuple[ElementId, ...] = ()
    legal_authority_ids: tuple[AuthorityId, ...] = ()
```

---

# 10. Facts and Propositions

Do not store only disputed facts.

Store every legally material proposition.

```python
class FactStatus(StrEnum):
    ALLEGED = "alleged"
    DENIED = "denied"
    ADMITTED = "admitted"
    STIPULATED = "stipulated"
    DISPUTED = "disputed"
    UNKNOWN = "unknown"
```

```python
class FactPolarity(StrEnum):
    SUPPORTS = "supports"
    UNDERMINES = "undermines"
    NEUTRAL = "neutral"
```

```python
class ElementRelevance(DomainModel):
    element_id: ElementId
    polarity: FactPolarity
    relevance_weight: float = Field(ge=0, le=1)
    explanation: str
```

```python
class FactProposition(DomainModel):
    fact_id: FactId
    proposition: str

    initial_status: FactStatus
    asserted_by_party_ids: tuple[PartyId, ...] = ()
    denied_by_party_ids: tuple[PartyId, ...] = ()

    element_relevance: tuple[ElementRelevance, ...]

    source_evidence_ids: tuple[EvidenceId, ...] = ()
    source_statement_ids: tuple[StatementId, ...] = ()
    source_event_ids: tuple[EventId, ...] = ()

    disclosure: DisclosureRule
```

Example:

```python
FactProposition(
    fact_id="FAC-ALARM-FAILED",
    proposition=(
        "The forklift backup alarm failed inspection "
        "two days before the incident."
    ),
    initial_status=FactStatus.DISPUTED,
    asserted_by_party_ids=("PTY-PLAINTIFF",),
    denied_by_party_ids=("PTY-DEFENDANT",),
    element_relevance=(
        ElementRelevance(
            element_id="ELM-BREACH",
            polarity=FactPolarity.SUPPORTS,
            relevance_weight=0.90,
            explanation=(
                "Operating equipment with a known failed safety "
                "alarm may support breach."
            ),
        ),
    ),
    source_evidence_ids=("EVD-MAINT-LOG",),
    disclosure=DisclosureRule(
        initial_scopes=frozenset(
            {
                VisibilityScope.PUBLIC_CASE,
                VisibilityScope.PLAINTIFF_PRIVATE,
                VisibilityScope.DEFENSE_PRIVATE,
                VisibilityScope.EVALUATOR_ONLY,
            }
        ),
    ),
)
```

---

# 11. Events and Timeline

Facts are propositions. Events are occurrences.

```python
class TemporalPrecision(StrEnum):
    EXACT = "exact"
    APPROXIMATE = "approximate"
    RANGE = "range"
    UNKNOWN = "unknown"
```

```python
class TimeWindow(DomainModel):
    precision: TemporalPrecision

    start: datetime | None = None
    end: datetime | None = None
    description: str | None = None
```

```python
class CaseEvent(DomainModel):
    event_id: EventId
    name: str
    description: str

    time_window: TimeWindow
    location: str | None

    participant_actor_ids: tuple[ActorId, ...]
    related_fact_ids: tuple[FactId, ...]

    supporting_evidence_ids: tuple[EvidenceId, ...] = ()
    supporting_statement_ids: tuple[StatementId, ...] = ()

    disclosure: DisclosureRule
```

This lets you distinguish:

```text
Event:
Forklift inspection occurred.

Facts:
The alarm failed.
Luis performed the inspection.
Dana was informed of the failure.
The forklift remained operational.
```

One event can contain multiple disputed propositions.

---

# 12. Evidence Model

Evidence requires identity, informational content, admissibility dependencies, and runtime status.

California evidence law treats personal knowledge, hearsay, and authentication as separate questions, supporting a model where each is represented independently rather than through one `admissible` flag.

## 12.1 Evidence types

```python
class EvidenceType(StrEnum):
    DOCUMENT = "document"
    PHOTOGRAPH = "photograph"
    VIDEO = "video"
    AUDIO = "audio"
    PHYSICAL_OBJECT = "physical_object"
    DIGITAL_RECORD = "digital_record"
    BUSINESS_RECORD = "business_record"
    DEMONSTRATIVE = "demonstrative"
    EXPERT_OPINION = "expert_opinion"
    TESTIMONY = "testimony"
    STIPULATION = "stipulation"
```

## 12.2 Evidence content

```python
class EvidenceContent(DomainModel):
    summary: str

    fact_ids_supported: tuple[FactId, ...] = ()
    fact_ids_undermined: tuple[FactId, ...] = ()

    statement_ids_contained: tuple[StatementId, ...] = ()
    event_ids_depicted: tuple[EventId, ...] = ()
```

## 12.3 Provenance

```python
class EvidenceProvenance(DomainModel):
    created_by_actor_id: ActorId | None = None
    created_at: datetime | None = None
    created_location: str | None = None

    custodian_actor_id: ActorId | None = None
    source_description: str

    chain_of_custody_event_ids: tuple[str, ...] = ()
```

## 12.4 Foundation

```python
class FoundationRequirementType(StrEnum):
    AUTHENTICATION = "authentication"
    PERSONAL_KNOWLEDGE = "personal_knowledge"
    BUSINESS_RECORD_FOUNDATION = "business_record_foundation"
    CHAIN_OF_CUSTODY = "chain_of_custody"
    EXPERT_QUALIFICATION = "expert_qualification"
    ORIGINAL_OR_DUPLICATE = "original_or_duplicate"
```

```python
class FoundationRequirement(DomainModel):
    requirement_id: str
    requirement_type: FoundationRequirementType
    description: str

    satisfiable_by_witness_ids: tuple[WitnessId, ...] = ()
    satisfiable_by_evidence_ids: tuple[EvidenceId, ...] = ()

    required_fact_ids: tuple[FactId, ...] = ()
    authority_ids: tuple[AuthorityId, ...] = ()
```

## 12.5 Hearsay profile

```python
class HearsayTreatment(StrEnum):
    NOT_HEARSAY = "not_hearsay"
    HEARSAY_NO_EXCEPTION = "hearsay_no_exception"
    POTENTIAL_EXCEPTION = "potential_exception"
    LIMITED_PURPOSE = "limited_purpose"
    NOT_APPLICABLE = "not_applicable"
```

```python
class HearsayProfile(DomainModel):
    treatment: HearsayTreatment
    declarant_actor_id: ActorId | None = None

    offered_purpose: str | None = None
    potential_exception_ids: tuple[str, ...] = ()
    authority_ids: tuple[AuthorityId, ...] = ()

    author_notes: str | None = None
```

## 12.6 Evidence item

```python
class EvidenceItem(DomainModel):
    evidence_id: EvidenceId
    title: str
    evidence_type: EvidenceType

    description: str
    content: EvidenceContent
    provenance: EvidenceProvenance

    owned_or_controlled_by_party_id: PartyId | None
    initially_available_to_party_ids: tuple[PartyId, ...]

    foundation_requirements: tuple[FoundationRequirement, ...] = ()
    hearsay_profile: HearsayProfile | None = None

    objection_ground_ids: tuple[str, ...] = ()
    permitted_use_notes: str | None = None

    disclosure: DisclosureRule
```

## 12.7 Runtime evidence state

Never mutate the authored evidence item to represent trial status.

```python
class EvidenceAdmissionStatus(StrEnum):
    AVAILABLE = "available"
    MARKED = "marked"
    FOUNDATION_IN_PROGRESS = "foundation_in_progress"
    OFFERED = "offered"
    OBJECTED = "objected"
    ADMITTED = "admitted"
    ADMITTED_LIMITED_PURPOSE = "admitted_limited_purpose"
    EXCLUDED = "excluded"
    WITHDRAWN = "withdrawn"
```

```python
class FoundationProgress(DomainModel):
    requirement_id: str
    satisfied: bool
    supporting_event_ids: tuple[str, ...] = ()
```

```python
class EvidenceRuntimeState(DomainModel):
    evidence_id: EvidenceId
    status: EvidenceAdmissionStatus

    foundation_progress: tuple[FoundationProgress, ...] = ()
    offered_by_actor_id: ActorId | None = None

    objection_event_ids: tuple[str, ...] = ()
    ruling_event_ids: tuple[str, ...] = ()

    permitted_purposes: tuple[str, ...] = ()
```

---

# 13. Witness Model

Witness modelling must separate:

```text
Who the witness is
What happened to the witness
What the witness knows
What the witness remembers
What the witness previously said
How the witness behaves
What the witness is expected to do in the scenario
What the witness actually says at runtime
```

## 13.1 Witness profile

```python
class WitnessRelationship(DomainModel):
    related_actor_id: ActorId
    relationship_type: str
    description: str
    potential_bias_weight: float = Field(ge=0, le=1)
```

```python
class WitnessProfile(DomainModel):
    witness_id: WitnessId
    actor_id: ActorId

    name: str
    occupation: str | None
    background: str

    called_by_party_id: PartyId | None
    available_to_party_ids: tuple[PartyId, ...]

    relationships: tuple[WitnessRelationship, ...] = ()
    knowledge_item_ids: tuple[str, ...] = ()
    prior_statement_ids: tuple[StatementId, ...] = ()

    authenticatable_evidence_ids: tuple[EvidenceId, ...] = ()
    expert_profile_id: str | None = None

    disclosure: DisclosureRule
```

## 13.2 Knowledge atom

```python
class KnowledgeSource(StrEnum):
    PERSONALLY_OBSERVED = "personally_observed"
    PERSONALLY_PERFORMED = "personally_performed"
    PERSONALLY_HEARD = "personally_heard"
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_MAINTAINED = "document_maintained"
    DOCUMENT_REVIEWED = "document_reviewed"
    TOLD_BY_ANOTHER = "told_by_another"
    INFERRED = "inferred"
```

```python
class WitnessKnowledgeItem(DomainModel):
    knowledge_item_id: str
    witness_id: WitnessId

    fact_id: FactId
    source: KnowledgeSource

    firsthand: bool

    believed_truth_value: Literal[
        "true",
        "false",
        "uncertain",
    ]

    memory_strength: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)

    accurate_against_synthetic_truth: bool | None = None
    distortion_note: str | None = None

    disclosure: DisclosureRule
```

The witness sees their belief and memory—not the evaluator field `accurate_against_synthetic_truth`.

## 13.3 Prior statements

```python
class StatementContext(StrEnum):
    INFORMAL = "informal"
    INTERVIEW = "interview"
    WRITTEN_STATEMENT = "written_statement"
    DEPOSITION = "deposition"
    EMAIL = "email"
    REPORT = "report"
    PRIOR_TESTIMONY = "prior_testimony"
```

```python
class PriorStatement(DomainModel):
    statement_id: StatementId
    witness_id: WitnessId

    text: str
    context: StatementContext

    made_at: datetime | None
    made_to_actor_ids: tuple[ActorId, ...]

    source_evidence_id: EvidenceId | None
    related_fact_ids: tuple[FactId, ...]

    signed: bool = False
    under_oath: bool = False

    disclosure: DisclosureRule
```

## 13.4 Behaviour profile

```python
class WitnessBehaviorProfile(DomainModel):
    behavior_profile_id: str

    cooperativeness: float = Field(ge=0, le=1)
    verbosity: float = Field(ge=0, le=1)
    anxiety: float = Field(ge=0, le=1)
    hostility: float = Field(ge=0, le=1)
    evasiveness: float = Field(ge=0, le=1)
    suggestibility: float = Field(ge=0, le=1)
    confidence_expression: float = Field(ge=0, le=1)

    speech_style: str
    behavior_notes: tuple[str, ...] = ()
```

The behaviour model must not be allowed to invent new knowledge.

```text
Knowledge model controls content.
Behaviour model controls expression.
```

## 13.5 Runtime witness state

```python
class WitnessRuntimeState(DomainModel):
    witness_id: WitnessId

    current_emotional_state: str
    current_confidence: float = Field(ge=0, le=1)

    revealed_knowledge_item_ids: tuple[str, ...] = ()
    testimony_event_ids: tuple[str, ...] = ()

    runtime_contradiction_ids: tuple[str, ...] = ()
    credibility_signal_ids: tuple[str, ...] = ()
```

---

# 14. Contradiction Model

Do not prewrite `contradicts: "may say..."`.

Model the underlying statements and let a contradiction service compare them.

```python
class AssertionReferenceType(StrEnum):
    FACT = "fact"
    PRIOR_STATEMENT = "prior_statement"
    TESTIMONY_EVENT = "testimony_event"
    EVIDENCE_CONTENT = "evidence_content"
    OPENING_COMMITMENT = "opening_commitment"
    ARGUMENT = "argument"
```

```python
class AssertionReference(DomainModel):
    reference_type: AssertionReferenceType
    reference_id: str
    proposition: str
```

```python
class ContradictionType(StrEnum):
    DIRECT = "direct"
    TIMELINE = "timeline"
    QUANTITY = "quantity"
    IDENTITY = "identity"
    LOCATION = "location"
    OMISSION = "omission"
    THEORY_INCONSISTENCY = "theory_inconsistency"
```

```python
class Contradiction(DomainModel):
    contradiction_id: str

    assertion_a: AssertionReference
    assertion_b: AssertionReference
    contradiction_type: ContradictionType

    materiality: float = Field(ge=0, le=1)
    affected_element_ids: tuple[ElementId, ...]

    discoverable_by_party_ids: tuple[PartyId, ...]
    usable_evidence_ids: tuple[EvidenceId, ...] = ()

    status: Literal[
        "latent",
        "available",
        "noticed",
        "used",
        "explained",
        "unresolved",
    ]

    evaluator_notes: str | None = None
```

For authored templates, you may include expected contradiction seeds, but the runtime contradiction graph should still be generated from actual testimony.

---

# 15. Legal Authority and Jury Instruction Models

The legal snapshot belongs to the case package, but actor contexts should receive only relevant excerpts.

```python
class AuthorityType(StrEnum):
    CONSTITUTION = "constitution"
    STATUTE = "statute"
    EVIDENCE_CODE = "evidence_code"
    PROCEDURAL_RULE = "procedural_rule"
    CASE_LAW = "case_law"
    JURY_INSTRUCTION = "jury_instruction"
    VERDICT_FORM = "verdict_form"
    LOCAL_RULE = "local_rule"
```

```python
class AuthorityLevel(StrEnum):
    BINDING = "binding"
    PERSUASIVE = "persuasive"
    TRAINING_GUIDANCE = "training_guidance"
```

```python
class LegalAuthority(DomainModel):
    authority_id: AuthorityId

    title: str
    citation: str | None
    authority_type: AuthorityType
    authority_level: AuthorityLevel

    jurisdiction_pack_id: str
    effective_from: date | None
    effective_to: date | None

    full_text_ref: str
    approved_excerpt: str

    issue_tags: tuple[str, ...]
    element_ids: tuple[ElementId, ...] = ()
    objection_ground_ids: tuple[str, ...] = ()
```

```python
class JuryInstruction(DomainModel):
    instruction_id: InstructionId
    title: str

    authority_id: AuthorityId
    instruction_text: str

    applicable_claim_ids: tuple[ClaimId, ...]
    applicable_element_ids: tuple[ElementId, ...]

    use_notes: str | None = None
```

```python
class LegalSnapshot(DomainModel):
    snapshot_id: str
    jurisdiction_pack_id: str
    jurisdiction_pack_version: str
    effective_at: date

    authority_ids: tuple[AuthorityId, ...]
    jury_instruction_ids: tuple[InstructionId, ...]
    verdict_form_ids: tuple[str, ...]
```

For V2 template cases, prefer **curated and frozen legal snapshots** over live RAG during every simulation.

You can still use retrieval inside that snapshot:

```text
Current issue
    ↓
Retrieve relevant authorities from approved snapshot
    ↓
Return excerpts to node
```

This is safer and more reproducible than unrestricted web retrieval.

---

# 16. Private Synthetic Truth

Synthetic truth must be isolated from all courtroom actors.

```python
class SyntheticTruthValue(StrEnum):
    TRUE = "true"
    FALSE = "false"
    PARTIALLY_TRUE = "partially_true"
    INDETERMINATE = "indeterminate"
```

```python
class SyntheticFactTruth(DomainModel):
    fact_id: FactId
    truth_value: SyntheticTruthValue

    author_explanation: str
    confidence: float = Field(default=1.0, ge=0, le=1)
```

```python
class SyntheticScenarioTruth(DomainModel):
    fact_truths: tuple[SyntheticFactTruth, ...]

    intended_causal_chain_fact_ids: tuple[FactId, ...]
    known_false_narrative_fact_ids: tuple[FactId, ...] = ()

    evaluator_only_notes: str
```

This object must be visible only to:

* Deterministic validators.
* Evaluation engine.
* Coaching engine.
* Case-authoring test tools.

It must never be available to:

* Plaintiff lawyer.
* Defense lawyer.
* Trial judge.
* Jury.
* Witnesses.

Even the trial judge should decide based on the admitted record, not synthetic truth.

---

# 17. Expected Learning and Coaching References

Because V2 uses authored training cases, each template can contain expert reference material.

Do not make it one “ideal transcript.”

Store multiple acceptable strategies.

```python
class ReferenceObjective(DomainModel):
    objective_id: ObjectiveId
    side: PartySide

    description: str
    priority_range: tuple[float, float]

    target_element_ids: tuple[ElementId, ...]
    target_fact_ids: tuple[FactId, ...]
    target_witness_ids: tuple[WitnessId, ...] = ()
    target_evidence_ids: tuple[EvidenceId, ...] = ()

    success_signals: tuple[str, ...]
    common_failure_modes: tuple[str, ...]
```

```python
class ReferenceTactic(DomainModel):
    tactic_id: str
    objective_id: ObjectiveId

    action_type: str
    preconditions: tuple[str, ...]

    strong_execution_pattern: tuple[str, ...]
    weak_execution_patterns: tuple[str, ...]

    risks: tuple[str, ...]
```

```python
class LearningMomentSeed(DomainModel):
    seed_id: str
    description: str

    trigger_event_types: tuple[str, ...]
    trigger_fact_ids: tuple[FactId, ...] = ()
    trigger_statement_ids: tuple[StatementId, ...] = ()
    trigger_contradiction_ids: tuple[str, ...] = ()

    affected_skill_ids: tuple[str, ...]
    expected_response_patterns: tuple[str, ...]
    coaching_note: str
```

```python
class CoachingReference(DomainModel):
    reference_objectives: tuple[ReferenceObjective, ...]
    reference_tactics: tuple[ReferenceTactic, ...]
    learning_moment_seeds: tuple[LearningMomentSeed, ...]

    known_bad_strategies: tuple[str, ...] = ()
    case_author_notes: str | None = None
```

These are evaluator references, not lawyer instructions.

---

# 18. Authored Case Template

The complete author-facing object can now be assembled.

```python
class AuthoredCaseTemplate(DomainModel):
    metadata: CaseMetadata
    trial_profile: TrialProfile

    parties: tuple[Party, ...]
    actors: tuple[ActorProfile, ...]

    burdens: tuple[BurdenDefinition, ...]
    claims: tuple[Claim, ...]
    defenses: tuple[Defense, ...]
    legal_elements: tuple[LegalElement, ...]

    facts: tuple[FactProposition, ...]
    events: tuple[CaseEvent, ...]

    evidence: tuple[EvidenceItem, ...]

    witnesses: tuple[WitnessProfile, ...]
    witness_knowledge: tuple[WitnessKnowledgeItem, ...]
    prior_statements: tuple[PriorStatement, ...]
    witness_behaviors: tuple[WitnessBehaviorProfile, ...]

    authorities: tuple[LegalAuthority, ...]
    jury_instructions: tuple[JuryInstruction, ...]
    legal_snapshot: LegalSnapshot

    synthetic_truth: SyntheticScenarioTruth
    coaching_reference: CoachingReference
```

---

# 19. Compiled Case Package

Do not repeatedly search tuples during runtime.

Compile the author model into indexed structures.

```python
class CompiledCasePackage(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
    )

    template: AuthoredCaseTemplate

    parties_by_id: dict[PartyId, Party]
    actors_by_id: dict[ActorId, ActorProfile]

    claims_by_id: dict[ClaimId, Claim]
    defenses_by_id: dict[str, Defense]
    elements_by_id: dict[ElementId, LegalElement]

    facts_by_id: dict[FactId, FactProposition]
    events_by_id: dict[EventId, CaseEvent]
    evidence_by_id: dict[EvidenceId, EvidenceItem]

    witnesses_by_id: dict[WitnessId, WitnessProfile]
    knowledge_by_id: dict[str, WitnessKnowledgeItem]
    statements_by_id: dict[StatementId, PriorStatement]

    authorities_by_id: dict[AuthorityId, LegalAuthority]
    instructions_by_id: dict[InstructionId, JuryInstruction]

    knowledge_ids_by_witness: dict[WitnessId, tuple[str, ...]]
    evidence_ids_by_fact: dict[FactId, tuple[EvidenceId, ...]]
    facts_by_element: dict[ElementId, tuple[FactId, ...]]
    statements_by_witness: dict[WitnessId, tuple[StatementId, ...]]
```

Compilation should:

* Validate references.
* Reject duplicate IDs.
* Create indexes.
* Confirm visibility consistency.
* Confirm every element belongs to a claim or defense.
* Confirm every knowledge item belongs to a witness.
* Confirm every evidence fact reference exists.
* Confirm jury instructions match the trial profile.
* Confirm synthetic truth covers all truth-sensitive facts.
* Confirm no evaluator-only information is accidentally public.

---

# 20. Derived Case Intelligence

```python
class ElementSupportLink(DomainModel):
    element_id: ElementId
    fact_id: FactId

    polarity: FactPolarity
    evidence_ids: tuple[EvidenceId, ...]

    initial_strength: float = Field(ge=0, le=1)
```

```python
class CaseGap(DomainModel):
    gap_id: str
    side: PartySide

    description: str
    affected_element_ids: tuple[ElementId, ...]

    missing_fact_ids: tuple[FactId, ...] = ()
    missing_evidence_types: tuple[EvidenceType, ...] = ()
    affected_witness_ids: tuple[WitnessId, ...] = ()

    severity: float = Field(ge=0, le=1)
```

```python
class CaseIntelligence(DomainModel):
    element_support_links: tuple[ElementSupportLink, ...]
    initial_contradictions: tuple[Contradiction, ...]
    case_gaps: tuple[CaseGap, ...]

    timeline_event_ids: tuple[EventId, ...]

    plaintiff_initial_position_summary: str
    defense_initial_position_summary: str
```

The summaries are derived conveniences. The structured links remain authoritative.

---

# 21. Runtime Trial Models

## 21.1 Fact runtime state

```python
class TrialFactStatus(StrEnum):
    NOT_PRESENTED = "not_presented"
    MENTIONED = "mentioned"
    CONTESTED = "contested"
    SUPPORTED_IN_RECORD = "supported_in_record"
    UNDERMINED_IN_RECORD = "undermined_in_record"
    STIPULATED = "stipulated"
    FOUND_TRUE = "found_true"
    FOUND_NOT_TRUE = "found_not_true"
```

```python
class FactRuntimeState(DomainModel):
    fact_id: FactId
    status: TrialFactStatus

    supporting_event_ids: tuple[str, ...] = ()
    undermining_event_ids: tuple[str, ...] = ()

    jury_visible: bool = False
```

## 21.2 Objective runtime state

```python
class ObjectiveStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    PARTIALLY_COMPLETED = "partially_completed"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    ABANDONED = "abandoned"
```

```python
class ObjectiveRuntimeState(DomainModel):
    objective_id: ObjectiveId
    status: ObjectiveStatus

    progress: float = Field(ge=0, le=1)
    supporting_event_ids: tuple[str, ...] = ()
    blocking_event_ids: tuple[str, ...] = ()
```

## 21.3 Trial state

```python
class TrialState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    case_package_id: CaseId

    phase: str
    active_actor_id: ActorId | None
    current_witness_id: WitnessId | None
    examination_type: str | None

    case_intelligence: CaseIntelligence

    plaintiff_strategy: object | None
    defense_strategy: object | None

    fact_states: dict[FactId, FactRuntimeState]
    evidence_states: dict[EvidenceId, EvidenceRuntimeState]
    objective_states: dict[ObjectiveId, ObjectiveRuntimeState]
    witness_states: dict[WitnessId, WitnessRuntimeState]

    event_ids: list[str]
    latest_event_ids: list[str]

    pending_objection_id: str | None = None
    pending_action_id: str | None = None
```

The full immutable case package does not need to be copied into every LangGraph checkpoint. State can hold the package ID, while the package is accessed through an injected repository.

LangGraph runtime context supports dependency injection rather than hardcoding repositories or services into graph nodes.

---

# 22. Context Boundary Architecture

## 22.1 Do not add unrestricted getters to domain models

Avoid:

```python
case.get_context_for_lawyer(...)
case.get_context_for_witness(...)
```

This couples the domain model to:

* Actor roles.
* Runtime state.
* LangGraph nodes.
* Prompt design.
* Security policy.
* Model-provider concerns.

Use a separate projection service:

```text
Canonical case package
       +
Runtime trial state
       +
Actor identity
       +
Node purpose
       +
Access policy
       ↓
ContextBoundaryService
       ↓
Typed context projection
```

The domain models remain passive and authoritative.

The boundary service becomes the only approved route for obtaining model context.

---

# 23. Context Request

```python
class NodePurpose(StrEnum):
    INITIAL_CASE_ANALYSIS = "initial_case_analysis"

    GLOBAL_STRATEGY = "global_strategy"
    WITNESS_SELECTION = "witness_selection"
    EXAMINATION_OBJECTIVE = "examination_objective"
    TACTICAL_ACTION_PLANNING = "tactical_action_planning"
    QUESTION_GENERATION = "question_generation"

    OBJECTION_DECISION = "objection_decision"
    OBJECTION_RULING = "objection_ruling"
    WITNESS_ANSWER = "witness_answer"

    OPENING_PLANNING = "opening_planning"
    OPENING_EXECUTION = "opening_execution"

    CLOSING_PLANNING = "closing_planning"
    CLOSING_EXECUTION = "closing_execution"

    JURY_INSTRUCTION = "jury_instruction"
    JURY_DELIBERATION = "jury_deliberation"

    ACTOR_EVALUATION = "actor_evaluation"
    MISSED_OPPORTUNITY_ANALYSIS = "missed_opportunity_analysis"
    COACHING = "coaching"
```

```python
class ContextRequest(DomainModel):
    session_id: UUID
    node_purpose: NodePurpose

    requesting_actor_id: ActorId | None = None
    target_actor_id: ActorId | None = None
    target_witness_id: WitnessId | None = None

    active_objective_id: ObjectiveId | None = None
    target_fact_ids: tuple[FactId, ...] = ()
    target_evidence_ids: tuple[EvidenceId, ...] = ()

    recent_event_limit: int = Field(default=8, ge=0, le=50)
```

---

# 24. Shared Context Envelope

Every LLM call should receive a typed envelope.

```python
class ContextMetadata(DomainModel):
    session_id: UUID
    node_purpose: NodePurpose
    actor_id: ActorId | None

    case_id: CaseId
    phase: str

    projection_version: str
    policy_version: str

    included_object_ids: tuple[str, ...]
    excluded_categories: tuple[str, ...]
```

```python
class ProceduralContext(DomainModel):
    current_phase: str
    active_actor_id: ActorId | None

    current_witness_id: WitnessId | None
    examination_type: str | None

    allowed_action_types: tuple[str, ...]
    prohibited_action_types: tuple[str, ...]

    pending_objection_id: str | None
    relevant_prior_ruling_ids: tuple[str, ...]
```

```python
class BaseNodeContext(DomainModel):
    metadata: ContextMetadata
    role_contract: str
    task_instruction: str
    procedure: ProceduralContext
```

Use specialized context models rather than one context model with dozens of optional fields.

---

# 25. Role-Level Boundaries

## 25.1 Plaintiff lawyer

May see:

* Public case information.
* Plaintiff-private facts.
* Evidence disclosed to plaintiff.
* Plaintiff witnesses’ preparation materials.
* Opposing evidence disclosed under the template.
* Plaintiff strategy.
* Public trial record.
* Applicable legal snapshot.
* Contradictions discoverable by plaintiff.
* Judge rulings.

May not see:

* Defense private strategy.
* Defense-private witness beliefs.
* Evaluator truth.
* Expected verdict.
* Coaching reference.
* Hidden contradiction labels not yet discoverable.
* Jury deliberation.

## 25.2 Defense lawyer

The equivalent defense projection.

## 25.3 Witness

May see:

* Their identity.
* Their behaviour profile.
* Their knowledge atoms.
* Their prior statements that they remember or are shown.
* Questions asked.
* Their previous testimony.
* Judge instructions directed to them.
* Admitted exhibits actually shown to them.

May not see:

* Complete case facts.
* Legal elements.
* Either party’s strategy.
* Other witnesses’ knowledge.
* Synthetic truth.
* Contradiction graph.
* Evaluation expectations.
* Ideal answers.
* Jury deliberation.

## 25.4 Trial judge

May see:

* Public case metadata.
* Claims and defenses.
* Legal elements.
* Applicable rules.
* Current question, objection, and evidence offer.
* Admitted trial record.
* Evidence foundation developed in court.
* Relevant party submissions.
* Prior rulings.

May not see:

* Synthetic truth.
* Private lawyer strategies.
* Witness hidden knowledge.
* Coaching reference.
* Expected verdict.
* Excluded evidence for fact-finding purposes.

The ruling context may include excluded or disputed material only to the extent necessary to rule on admissibility.

## 25.5 Jury

May see:

* Preliminary and final instructions.
* Admitted evidence.
* Trial testimony.
* Stipulated facts.
* Permitted arguments.
* Verdict form.

May not see:

* Party strategies.
* Synthetic truth.
* Excluded evidence.
* Private legal authorities.
* Evaluator data.
* Judge-only ruling analysis.
* Coaching data.

## 25.6 Evaluator

May see:

* Complete authored case.
* Synthetic truth.
* Both private strategies.
* Complete event stream.
* Admitted and excluded evidence.
* Coaching references.
* Expected learning moments.
* Model and prompt metadata.

## 25.7 Coach

May see:

* Evaluator findings.
* Human participant actions.
* Available information at each historical decision point.
* Reference objectives and tactics.
* Counterfactual candidates.
* Relevant case truth when explaining simulation correctness.

The coach should not expose hidden truth as though the human lawyer should have known it at the time.

---

# 26. Node-Level Context Models

Role boundaries are not enough. A plaintiff lawyer’s global strategy node and question-generation node should not receive identical context.

## 26.1 Global strategy context

```python
class ElementCaseView(DomainModel):
    element: LegalElement
    relevant_facts: tuple[FactProposition, ...]
    available_evidence: tuple[EvidenceItem, ...]
    available_witness_ids: tuple[WitnessId, ...]
```

```python
class GlobalStrategyContext(BaseNodeContext):
    party: Party

    claims: tuple[Claim, ...]
    defenses: tuple[Defense, ...]

    element_views: tuple[ElementCaseView, ...]

    accessible_witnesses: tuple[WitnessProfile, ...]
    accessible_evidence: tuple[EvidenceItem, ...]

    known_prior_statements: tuple[PriorStatement, ...]
    discoverable_contradictions: tuple[Contradiction, ...]

    relevant_authorities: tuple[LegalAuthority, ...]
    relevant_instructions: tuple[JuryInstruction, ...]

    initial_case_gaps: tuple[CaseGap, ...]
```

Receives broad party-accessible context because it must build the global plan.

Does not receive opponent private strategy or synthetic truth.

---

## 26.2 Witness-selection context

```python
class WitnessSelectionContext(BaseNodeContext):
    party: Party

    remaining_witnesses: tuple[WitnessProfile, ...]
    current_strategy_summary: str

    open_objective_states: tuple[ObjectiveRuntimeState, ...]
    element_position_summary: tuple[str, ...]

    evidence_dependency_summary: tuple[str, ...]
    prior_witness_results: tuple[str, ...]
```

It does not need all witness knowledge atoms or the complete transcript.

---

## 26.3 Examination-objective context

```python
class ExaminationObjectiveContext(BaseNodeContext):
    examining_party: Party
    witness: WitnessProfile
    examination_type: str

    witness_plan: object
    relevant_element_ids: tuple[ElementId, ...]

    relevant_fact_states: tuple[FactRuntimeState, ...]
    relevant_evidence_states: tuple[EvidenceRuntimeState, ...]

    known_prior_statements: tuple[PriorStatement, ...]
    available_contradictions: tuple[Contradiction, ...]

    completed_objective_ids: tuple[ObjectiveId, ...]
    blocked_objective_ids: tuple[ObjectiveId, ...]
```

---

## 26.4 Tactical-action context

```python
class TacticalActionContext(BaseNodeContext):
    active_objective: object
    witness: WitnessProfile

    relevant_fact_states: tuple[FactRuntimeState, ...]
    relevant_evidence_states: tuple[EvidenceRuntimeState, ...]
    relevant_prior_statements: tuple[PriorStatement, ...]
    available_contradictions: tuple[Contradiction, ...]

    recent_topic_events: tuple[object, ...]
    available_tactical_skills: tuple[str, ...]

    expected_answer_shapes: tuple[str, ...]
```

Task:

```text
Select the next tactical action.
Do not generate courtroom wording.
```

---

## 26.5 Question-generation context

```python
class ExecutionBrief(DomainModel):
    action_type: str
    objective_id: ObjectiveId

    target_fact_ids: tuple[FactId, ...]
    target_evidence_ids: tuple[EvidenceId, ...]

    desired_answer_shape: str
    procedural_constraints: tuple[str, ...]

    expected_effect: str
    risks: tuple[str, ...]
```

```python
class QuestionGenerationContext(BaseNodeContext):
    execution_brief: ExecutionBrief

    current_witness_name: str
    current_examination_type: str

    previous_question: str | None
    previous_answer: str | None

    permitted_fact_phrasings: tuple[str, ...]
    prohibited_content: tuple[str, ...]
```

This node should not receive the complete strategy or complete case.

---

## 26.6 Objection-decision context

```python
class ObjectionDecisionContext(BaseNodeContext):
    opposing_lawyer_role: ActorRole

    pending_question: str
    pending_action_type: str

    current_examination_type: str
    current_foundation_state: tuple[FoundationProgress, ...]

    candidate_objection_grounds: tuple[str, ...]
    relevant_authorities: tuple[LegalAuthority, ...]

    strategic_considerations: tuple[str, ...]
    recent_objection_history: tuple[str, ...]
```

---

## 26.7 Judge-ruling context

```python
class JudgeRulingContext(BaseNodeContext):
    pending_question_or_offer: str
    objection_ground: str

    offering_party_id: PartyId
    opposing_party_id: PartyId

    relevant_evidence: EvidenceItem | None
    foundation_state: tuple[FoundationProgress, ...]

    relevant_record_events: tuple[object, ...]
    relevant_authorities: tuple[LegalAuthority, ...]
    relevant_prior_rulings: tuple[object, ...]
```

It should not receive:

* Private strategy.
* Synthetic truth.
* Evaluator expected ruling.

---

## 26.8 Witness-answer context

```python
class WitnessAnswerContext(BaseNodeContext):
    witness: WitnessProfile
    behavior: WitnessBehaviorProfile

    pending_question: str
    judge_instruction: str | None

    relevant_knowledge: tuple[WitnessKnowledgeItem, ...]
    relevant_prior_statements: tuple[PriorStatement, ...]

    relevant_previous_testimony: tuple[object, ...]

    shown_evidence: tuple[EvidenceItem, ...]
```

This is one of the strictest boundaries in the system.

The context builder should retrieve only knowledge atoms relevant to the question, plus enough adjacent information to answer naturally.

It must remove:

```text
accurate_against_synthetic_truth
author notes
expected contradiction
expected answer
coaching reference
strategy objective
```

---

## 26.9 Opening-planning context

```python
class OpeningPlanningContext(BaseNodeContext):
    party: Party
    theory_of_case: object

    priority_objectives: tuple[object, ...]
    planned_witnesses: tuple[WitnessProfile, ...]
    planned_evidence: tuple[EvidenceItem, ...]

    legal_elements: tuple[LegalElement, ...]
    known_case_weaknesses: tuple[CaseGap, ...]

    opening_constraints: tuple[str, ...]
```

---

## 26.10 Closing-planning context

```python
class ClosingPlanningContext(BaseNodeContext):
    party: Party
    theory_of_case: object

    element_record_views: tuple[object, ...]
    admitted_evidence: tuple[EvidenceItem, ...]
    witness_result_summaries: tuple[object, ...]

    contradictions_used: tuple[Contradiction, ...]
    contradictions_unresolved: tuple[Contradiction, ...]

    opening_commitments: tuple[object, ...]
    applicable_jury_instructions: tuple[JuryInstruction, ...]
```

Only evidence admitted for a permitted purpose should be available as substantive closing material.

---

## 26.11 Jury-deliberation context

```python
class JuryDeliberationContext(BaseNodeContext):
    jury_instructions: tuple[JuryInstruction, ...]
    verdict_form: object

    admitted_record: object
    stipulated_facts: tuple[FactProposition, ...]

    plaintiff_closing: str
    defense_closing: str
    plaintiff_rebuttal: str | None

    credibility_relevant_testimony: tuple[object, ...]
```

The jury receives no legal RAG tools in V2. It applies the supplied instructions.

---

## 26.12 Evaluation context

```python
class EvaluationContext(BaseNodeContext):
    complete_case: AuthoredCaseTemplate
    case_intelligence: CaseIntelligence
    synthetic_truth: SyntheticScenarioTruth

    plaintiff_strategy: object
    defense_strategy: object

    complete_trial_events: tuple[object, ...]
    final_runtime_state: TrialState

    coaching_reference: CoachingReference
    deterministic_failures: tuple[object, ...]
```

The evaluator has broad access, but each specialist evaluator should still receive only relevant slices.

For example:

* Witness evaluator gets witness knowledge, testimony, and hidden truth.
* Judge evaluator gets legal snapshot, record, rulings, and verdict.
* Lawyer evaluator gets strategy, available historical context, and actions.

---

# 27. Boundary Policies

```python
class ContextPolicy(DomainModel):
    policy_id: str
    policy_version: str

    allowed_visibility_scopes: frozenset[VisibilityScope]

    allow_synthetic_truth: bool = False
    allow_private_strategy: bool = False
    allow_opponent_private_strategy: bool = False
    allow_coaching_reference: bool = False

    include_only_admitted_evidence: bool = False
    include_only_jury_visible_events: bool = False

    maximum_recent_events: int = 10
```

Example policies:

```python
PLAINTIFF_STRATEGY_POLICY = ContextPolicy(
    policy_id="POLICY-PLAINTIFF-STRATEGY",
    policy_version="1.0",
    allowed_visibility_scopes=frozenset(
        {
            VisibilityScope.PUBLIC_CASE,
            VisibilityScope.PLAINTIFF_PRIVATE,
        }
    ),
    allow_private_strategy=True,
)
```

```python
WITNESS_ANSWER_POLICY = ContextPolicy(
    policy_id="POLICY-WITNESS-ANSWER",
    policy_version="1.0",
    allowed_visibility_scopes=frozenset(
        {
            VisibilityScope.WITNESS_PRIVATE,
        }
    ),
    maximum_recent_events=8,
)
```

```python
JURY_POLICY = ContextPolicy(
    policy_id="POLICY-JURY",
    policy_version="1.0",
    allowed_visibility_scopes=frozenset(
        {
            VisibilityScope.JURY_RECORD_ONLY,
        }
    ),
    include_only_admitted_evidence=True,
    include_only_jury_visible_events=True,
)
```

```python
EVALUATOR_POLICY = ContextPolicy(
    policy_id="POLICY-EVALUATOR",
    policy_version="1.0",
    allowed_visibility_scopes=frozenset(VisibilityScope),
    allow_synthetic_truth=True,
    allow_private_strategy=True,
    allow_opponent_private_strategy=True,
    allow_coaching_reference=True,
    maximum_recent_events=50,
)
```

---

# 28. Context Boundary Service

```python
from typing import Protocol, TypeVar

ContextT = TypeVar("ContextT", bound=BaseNodeContext)
```

```python
class CasePackageRepository(Protocol):
    async def get(
        self,
        case_id: CaseId,
    ) -> CompiledCasePackage:
        ...
```

```python
class TrialEventRepository(Protocol):
    async def get_events(
        self,
        session_id: UUID,
        *,
        event_ids: tuple[str, ...] | None = None,
        limit: int | None = None,
    ) -> tuple[object, ...]:
        ...
```

```python
class ContextBoundaryService:
    def __init__(
        self,
        case_repository: CasePackageRepository,
        event_repository: TrialEventRepository,
        policy_registry: ContextPolicyRegistry,
    ) -> None:
        self._cases = case_repository
        self._events = event_repository
        self._policies = policy_registry

    async def build(
        self,
        request: ContextRequest,
        state: TrialState,
    ) -> BaseNodeContext:
        match request.node_purpose:
            case NodePurpose.GLOBAL_STRATEGY:
                return await self._build_global_strategy_context(
                    request,
                    state,
                )

            case NodePurpose.WITNESS_SELECTION:
                return await self._build_witness_selection_context(
                    request,
                    state,
                )

            case NodePurpose.EXAMINATION_OBJECTIVE:
                return await self._build_examination_objective_context(
                    request,
                    state,
                )

            case NodePurpose.TACTICAL_ACTION_PLANNING:
                return await self._build_tactical_action_context(
                    request,
                    state,
                )

            case NodePurpose.QUESTION_GENERATION:
                return await self._build_question_generation_context(
                    request,
                    state,
                )

            case NodePurpose.OBJECTION_DECISION:
                return await self._build_objection_context(
                    request,
                    state,
                )

            case NodePurpose.OBJECTION_RULING:
                return await self._build_judge_ruling_context(
                    request,
                    state,
                )

            case NodePurpose.WITNESS_ANSWER:
                return await self._build_witness_answer_context(
                    request,
                    state,
                )

            case NodePurpose.CLOSING_PLANNING:
                return await self._build_closing_context(
                    request,
                    state,
                )

            case NodePurpose.JURY_DELIBERATION:
                return await self._build_jury_context(
                    request,
                    state,
                )

            case NodePurpose.ACTOR_EVALUATION:
                return await self._build_evaluation_context(
                    request,
                    state,
                )

            case _:
                raise UnsupportedNodePurpose(
                    request.node_purpose
                )
```

---

# 29. Access Helpers

## 29.1 Visibility check

```python
class AccessDecision(DomainModel):
    allowed: bool
    reason: str
```

```python
def can_actor_access(
    disclosure: DisclosureRule,
    *,
    actor: ActorProfile | None,
    party: Party | None,
    policy: ContextPolicy,
    trial_events: tuple[object, ...],
) -> AccessDecision:
    visible_scopes = (
        disclosure.initial_scopes
        & policy.allowed_visibility_scopes
    )

    if visible_scopes:
        return AccessDecision(
            allowed=True,
            reason="Allowed by initial visibility scope.",
        )

    if actor and actor.actor_id in disclosure.disclosed_to_actor_ids:
        return AccessDecision(
            allowed=True,
            reason="Explicitly disclosed to actor.",
        )

    if party and party.party_id in disclosure.disclosed_to_party_ids:
        return AccessDecision(
            allowed=True,
            reason="Explicitly disclosed to party.",
        )

    triggered_event_types = {
        getattr(event, "event_type", None)
        for event in trial_events
    }

    if (
        disclosure.becomes_public_on_event_types
        & triggered_event_types
    ):
        return AccessDecision(
            allowed=True,
            reason="Disclosure activated by trial event.",
        )

    return AccessDecision(
        allowed=False,
        reason="No matching disclosure rule.",
    )
```

## 29.2 Get accessible evidence

```python
def get_accessible_evidence(
    package: CompiledCasePackage,
    *,
    actor: ActorProfile,
    party: Party | None,
    policy: ContextPolicy,
    events: tuple[object, ...],
    evidence_states: dict[EvidenceId, EvidenceRuntimeState],
) -> tuple[EvidenceItem, ...]:
    visible: list[EvidenceItem] = []

    for evidence in package.evidence_by_id.values():
        decision = can_actor_access(
            evidence.disclosure,
            actor=actor,
            party=party,
            policy=policy,
            trial_events=events,
        )

        if not decision.allowed:
            continue

        runtime = evidence_states[evidence.evidence_id]

        if (
            policy.include_only_admitted_evidence
            and runtime.status
            not in {
                EvidenceAdmissionStatus.ADMITTED,
                EvidenceAdmissionStatus.ADMITTED_LIMITED_PURPOSE,
            }
        ):
            continue

        visible.append(evidence)

    return tuple(visible)
```

## 29.3 Get witness knowledge

```python
def get_witness_knowledge_for_question(
    package: CompiledCasePackage,
    *,
    witness_id: WitnessId,
    relevant_fact_ids: set[FactId],
) -> tuple[WitnessKnowledgeItem, ...]:
    knowledge_ids = package.knowledge_ids_by_witness.get(
        witness_id,
        (),
    )

    result: list[WitnessKnowledgeItem] = []

    for knowledge_id in knowledge_ids:
        item = package.knowledge_by_id[knowledge_id]

        if item.fact_id in relevant_fact_ids:
            result.append(
                item.model_copy(
                    update={
                        "accurate_against_synthetic_truth": None,
                        "distortion_note": None,
                    }
                )
            )

    return tuple(result)
```

The witness-facing model should ideally be a separate DTO without evaluator fields rather than relying entirely on `model_copy`.

```python
class WitnessKnowledgeView(DomainModel):
    knowledge_item_id: str
    fact_id: FactId

    source: KnowledgeSource
    firsthand: bool

    believed_truth_value: Literal[
        "true",
        "false",
        "uncertain",
    ]

    memory_strength: float
    confidence: float
```

```python
def to_witness_knowledge_view(
    item: WitnessKnowledgeItem,
) -> WitnessKnowledgeView:
    return WitnessKnowledgeView(
        knowledge_item_id=item.knowledge_item_id,
        fact_id=item.fact_id,
        source=item.source,
        firsthand=item.firsthand,
        believed_truth_value=item.believed_truth_value,
        memory_strength=item.memory_strength,
        confidence=item.confidence,
    )
```

Separate DTOs make accidental leakage less likely.

---

# 30. Question Relevance Resolution

The witness context builder needs to determine which knowledge atoms are relevant to a question.

Use a two-stage process:

```text
Pending question
    ↓
Structured target references from question generator
    ↓
Known target facts/evidence/objective
    ↓
Retrieve matching knowledge atoms
    ↓
Optional semantic expansion to adjacent facts
```

Because the question generator already returns:

```python
class GeneratedQuestion(DomainModel):
    spoken_text: str

    objective_id: ObjectiveId
    action_type: str

    target_fact_ids: tuple[FactId, ...]
    target_evidence_ids: tuple[EvidenceId, ...]
    target_statement_ids: tuple[StatementId, ...] = ()
```

the witness-answer node should not need to infer relevance from raw question text alone.

```python
def resolve_witness_relevant_fact_ids(
    generated_question: GeneratedQuestion,
    package: CompiledCasePackage,
) -> set[FactId]:
    result = set(generated_question.target_fact_ids)

    for evidence_id in generated_question.target_evidence_ids:
        evidence = package.evidence_by_id[evidence_id]
        result.update(evidence.content.fact_ids_supported)
        result.update(evidence.content.fact_ids_undermined)

    for statement_id in generated_question.target_statement_ids:
        statement = package.statements_by_id[statement_id]
        result.update(statement.related_fact_ids)

    return result
```

---

# 31. Example Context Builder

```python
async def _build_witness_answer_context(
    self,
    request: ContextRequest,
    state: TrialState,
) -> WitnessAnswerContext:
    package = await self._cases.get(state.case_package_id)

    if request.target_witness_id is None:
        raise ContextValidationError(
            "target_witness_id is required"
        )

    witness = package.witnesses_by_id[
        request.target_witness_id
    ]

    actor = package.actors_by_id[witness.actor_id]

    behavior = self._get_witness_behavior(
        package,
        witness,
    )

    pending_question = self._get_pending_question(state)

    relevant_fact_ids = resolve_witness_relevant_fact_ids(
        pending_question,
        package,
    )

    knowledge = tuple(
        to_witness_knowledge_view(item)
        for item in get_witness_knowledge_for_question(
            package,
            witness_id=witness.witness_id,
            relevant_fact_ids=relevant_fact_ids,
        )
    )

    relevant_statements = tuple(
        package.statements_by_id[statement_id]
        for statement_id in witness.prior_statement_ids
        if set(
            package.statements_by_id[
                statement_id
            ].related_fact_ids
        )
        & relevant_fact_ids
    )

    previous_testimony = await self._events.get_events(
        request.session_id,
        event_ids=(
            state.witness_states[
                witness.witness_id
            ].testimony_event_ids
        ),
        limit=request.recent_event_limit,
    )

    shown_evidence = self._get_evidence_shown_to_witness(
        package=package,
        state=state,
        witness_id=witness.witness_id,
    )

    return WitnessAnswerContext(
        metadata=self._metadata(
            request=request,
            state=state,
            included_object_ids=(
                witness.witness_id,
                *relevant_fact_ids,
            ),
            excluded_categories=(
                "synthetic_truth",
                "party_strategies",
                "contradiction_labels",
                "coaching_reference",
                "expected_answer",
            ),
        ),
        role_contract=self._role_contract(actor),
        task_instruction=(
            "Answer the pending question as this witness. "
            "Use only the supplied knowledge and remembered "
            "prior testimony. Do not assist either party."
        ),
        procedure=self._procedure_view(state),
        witness=witness,
        behavior=behavior,
        pending_question=pending_question.spoken_text,
        judge_instruction=self._current_judge_instruction(state),
        relevant_knowledge=knowledge,
        relevant_prior_statements=relevant_statements,
        relevant_previous_testimony=previous_testimony,
        shown_evidence=shown_evidence,
    )
```

---

# 32. Context Audit Record

Every context projection should produce an audit record.

```python
class ContextAuditRecord(DomainModel):
    context_id: UUID = Field(default_factory=uuid4)

    session_id: UUID
    node_purpose: NodePurpose
    actor_id: ActorId | None

    projection_version: str
    policy_version: str

    included_object_ids: tuple[str, ...]
    excluded_object_ids: tuple[str, ...]

    included_visibility_scopes: tuple[VisibilityScope, ...]
    token_estimate: int | None = None

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )
```

Store this alongside the LLM trace.

It enables you to diagnose:

* Whether hidden information leaked.
* Whether a required piece of evidence was absent.
* Why a model made an unsupported decision.
* Whether context grew excessively.
* Which projection version produced the output.

---

# 33. Boundary Validation

Before sending context to a model, run hard validations.

```python
class ContextViolation(DomainModel):
    code: str
    description: str
    object_id: str | None = None
    severity: Literal["warning", "error"]
```

```python
class ContextValidator:
    def validate(
        self,
        context: BaseNodeContext,
        policy: ContextPolicy,
    ) -> tuple[ContextViolation, ...]:
        violations: list[ContextViolation] = []

        if (
            not policy.allow_synthetic_truth
            and self._contains_synthetic_truth(context)
        ):
            violations.append(
                ContextViolation(
                    code="SYNTHETIC_TRUTH_LEAK",
                    description=(
                        "Context contains evaluator-only "
                        "synthetic truth."
                    ),
                    severity="error",
                )
            )

        if (
            policy.include_only_admitted_evidence
            and self._contains_unadmitted_evidence(context)
        ):
            violations.append(
                ContextViolation(
                    code="UNADMITTED_EVIDENCE_LEAK",
                    description=(
                        "Context contains evidence not admitted "
                        "for this actor."
                    ),
                    severity="error",
                )
            )

        return tuple(violations)
```

Context generation should fail closed:

```python
violations = validator.validate(context, policy)

errors = [
    violation
    for violation in violations
    if violation.severity == "error"
]

if errors:
    raise ContextBoundaryViolation(errors)
```

Do not send a partially unsafe context and merely log the problem.

---

# 34. Tool Boundaries

The same access rules must apply to tools.

A restricted actor must not be able to bypass context projection by calling:

```text
get_all_case_facts()
get_synthetic_truth()
get_opponent_strategy()
```

Use actor-bound tool facades:

```python
class ActorCaseTools:
    def __init__(
        self,
        actor_id: ActorId,
        session_id: UUID,
        boundary_service: ContextBoundaryService,
    ) -> None:
        self._actor_id = actor_id
        self._session_id = session_id
        self._boundaries = boundary_service

    async def get_evidence(
        self,
        evidence_id: EvidenceId,
    ) -> EvidenceItemView:
        return await self._boundaries.get_evidence_for_actor(
            session_id=self._session_id,
            actor_id=self._actor_id,
            evidence_id=evidence_id,
        )
```

The tool should not accept an arbitrary `actor_id` supplied by the model.

The actor identity must be bound by the runtime.

---

# 35. What Goes Directly into Context vs Tools

## Pass directly

Information required for the node’s immediate responsibility:

* Role contract.
* Exact task.
* Current procedural phase.
* Active objective.
* Pending question or objection.
* Relevant fact and evidence slice.
* Recent related events.
* Required legal excerpts.
* Output schema.

## Expose through tools

Optional or conditional information:

* Full approved exhibit content.
* Earlier testimony beyond the recent window.
* A specific prior statement.
* Additional authority from the frozen snapshot.
* A related witness result.
* Opening commitments.
* Earlier ruling details.

## Never expose as a tool to courtroom actors

* Synthetic truth.
* Evaluator notes.
* Opponent private strategy.
* Expected answer.
* Ideal strategy reference.
* Coaching seeds.
* Other witness private knowledge.
* Jury deliberation.

---

# 36. Context Size Policy

Use relevance-first context rather than unrestricted long context.

```python
class ContextBudget(DomainModel):
    maximum_tokens: int

    reserved_instruction_tokens: int
    reserved_output_tokens: int

    recent_event_limit: int
    authority_limit: int
    evidence_limit: int
    fact_limit: int
```

Recommended starting budgets:

| Node               | Approximate input policy                       |
| ------------------ | ---------------------------------------------- |
| Global strategy    | Broad party case view                          |
| Witness selection  | Strategy summary and unresolved dependencies   |
| Tactical planner   | One objective and related case slice           |
| Question generator | Execution brief and recent exchange            |
| Witness answer     | Question and relevant knowledge atoms          |
| Objection decision | Question, current foundation, and narrow rules |
| Judge ruling       | Objection record and exact legal excerpts      |
| Closing planner    | Structured admitted record                     |
| Jury               | Admitted record and instructions               |
| Evaluator          | Broad but specialist-specific context          |

Do not summarize away identifiers.

A summary can say:

```text
The maintenance evidence was disputed.
```

But evaluators and planners need:

```text
EVD-MAINT-LOG supports FAC-ALARM-FAILED.
WIT-MECHANIC can satisfy FND-MAINT-AUTHOR.
STM-MECHANIC-01 potentially conflicts with live testimony T-42.
```

---

# 37. Revised Warehouse Case Shape

The current case becomes conceptually:

```text
Case:
Stone v. North Pier Logistics

Claim:
Negligence

Elements:
- Duty
- Breach
- Causation
- Damages

Plaintiff theory:
North Pier knew the alarm had failed, kept the forklift operating,
and the missing alarm contributed to Stone's injury.

Defense theories:
- Alarm failure was not established.
- The operator was properly trained.
- Stone failed to exercise reasonable care.
- The alleged alarm failure did not cause the collision.

Facts:
- Alarm failed inspection.
- Maintenance log was created.
- Defendant received the report.
- Forklift remained in service.
- Stone was in the forklift's route.
- Stone suffered injury.
- Operator completed training.
- No support exists for intoxication or intentional conduct.

Evidence:
- Maintenance log.
- Training roster.
- Incident report.
- Warehouse layout.
- Medical record.
- Potential surveillance recording.

Witnesses:
- Mechanic.
- Forklift operator.
- Safety supervisor.
- Plaintiff.
- Treating medical witness.

Private truth:
- Alarm failed.
- Mechanic entered the record.
- Supervisor received the report.
- Operator did not know the alarm had failed.
- No intoxication occurred.

Coaching targets:
- Authenticate the maintenance log.
- Establish notice.
- Separate training from safe equipment condition.
- Establish causation rather than stopping at breach.
- Detect the operator's unsupported inspection claim.
```

This is sufficiently rich to drive a meaningful training simulation.

---

# 38. Recommended V2 Authoring Requirement

For each case, require authors to provide:

## Required

* Trial profile.
* Parties and actors.
* Claims and defenses.
* Legal elements and burdens.
* Material facts.
* Evidence.
* Witness knowledge.
* Prior statements.
* Synthetic truth.
* Legal snapshot.
* At least one strategy for each side.
* Learning objectives.
* Verdict form.
* Jury instructions.

## Strongly recommended

* Timeline.
* Evidence foundation dependencies.
* Contradiction seeds.
* Multiple acceptable strategies.
* Known weak strategies.
* Witness behaviour profiles.
* Objection opportunities.
* Broken-foundation scenarios.
* Unexpected-answer branches.
* Coaching moment seeds.

## Optional initially

* Damages calculation.
* Expert witnesses.
* Multi-party claims.
* Cross-claims.
* Bifurcated trials.
* Privilege issues.
* Character evidence.
* Complex hearsay chains.
* Rebuttal witnesses.

---

# 39. Recommended Implementation Order

## Step 1

Implement the domain types:

```text
Case metadata
Parties
Claims
Elements
Facts
Evidence
Witnesses
Knowledge atoms
Prior statements
Synthetic truth
```

## Step 2

Implement `CaseCompiler`.

Its output should be a validated `CompiledCasePackage`.

## Step 3

Implement role-level policies:

```text
Plaintiff lawyer
Defense lawyer
Witness
Trial judge
Jury
Evaluator
Coach
```

## Step 4

Implement node contexts in this order:

```text
GlobalStrategyContext
WitnessSelectionContext
TacticalActionContext
QuestionGenerationContext
WitnessAnswerContext
ObjectionDecisionContext
JudgeRulingContext
ClosingPlanningContext
JuryDeliberationContext
EvaluationContext
```

## Step 5

Implement `ContextBoundaryService`.

Make direct case-package access unavailable inside LLM nodes.

## Step 6

Add boundary tests before integrating the redesigned planner.

---

# 40. Essential Boundary Tests

```python
def test_witness_cannot_see_synthetic_truth():
    ...

def test_witness_cannot_see_lawyer_strategy():
    ...

def test_plaintiff_cannot_see_defense_private_strategy():
    ...

def test_judge_fact_finding_view_excludes_unadmitted_evidence():
    ...

def test_jury_sees_only_admitted_record():
    ...

def test_evaluator_can_reconstruct_historical_actor_context():
    ...

def test_tool_cannot_bypass_actor_access_policy():
    ...

def test_question_generator_receives_execution_brief_only():
    ...

def test_witness_answer_context_contains_relevant_knowledge():
    ...

def test_witness_answer_context_omits_expected_answer():
    ...

def test_context_fails_closed_on_unknown_visibility():
    ...
```

The most important evaluator capability is historical reconstruction:

```text
At turn T-42, what facts, evidence, testimony, law, and strategic
objectives were actually available to the lawyer?
```

Without that, the coach may unfairly criticize a lawyer for missing information they could not have known.

---

# 41. Final Recommended Architecture

```text
AuthoredCaseTemplate
        ↓
CaseCompiler
        ↓
CompiledCasePackage
        ├── Public case data
        ├── Plaintiff-private data
        ├── Defense-private data
        ├── Witness-private data
        ├── Legal snapshot
        ├── Synthetic truth
        └── Coaching reference
                ↓
         Runtime Trial State
                ↓
       ContextBoundaryService
                ↓
    Role policy + Node purpose
                ↓
       Typed context projection
                ↓
        Validation and audit
                ↓
              LLM
```

The key rule is:

> **No graph node should manually construct a prompt from `TrialState` or `CaseFile`.**

Every model-backed node should follow:

```python
context = await context_boundary_service.build(
    ContextRequest(
        session_id=state.session_id,
        node_purpose=NodePurpose.TACTICAL_ACTION_PLANNING,
        requesting_actor_id=state.active_actor_id,
        target_witness_id=state.current_witness_id,
        active_objective_id=state.active_objective_id,
    ),
    state,
)

decision = await model_gateway.generate_structured(
    task="plan_tactical_action",
    context=context,
    output_type=PlannedAction,
)
```

This creates one enforceable location for:

* Information security.
* Context relevance.
* Prompt-size control.
* Role isolation.
* Legal-source selection.
* Tool access.
* Projection versioning.
* Traceability.
* Future human-vs-AI reuse.

That boundary is as important to the Courtroom Intelligence Engine as the planning graph itself.
