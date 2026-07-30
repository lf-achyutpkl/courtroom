from __future__ import annotations

from courtroom_engine.context.projections import NodePurpose
from courtroom_engine.domain.case import Actor, ActorRole
from courtroom_engine.domain.procedure import ActionType, ProcedureState, TrialPhase
from courtroom_engine.domain.skills import (
    SkillCategory,
    SkillDefinition,
    SkillLoadDecision,
    SkillLoadRequest,
    SkillPolicyPack,
    SkillRegistry,
)

SKILL_POLICY_VERSION = "v2-alpha-skills-1"
DEFAULT_JURISDICTION_ID = "US-CA"

LAWYER_ROLES = (
    ActorRole.PLAINTIFF_LAWYER,
    ActorRole.PROSECUTION_LAWYER,
    ActorRole.DEFENSE_LAWYER,
)


def build_default_skill_registry() -> SkillRegistry:
    skills = (
        *_global_skills(),
        *_california_jurisdiction_skills(),
        *_role_skills(),
        *_phase_skills(),
        *_tactical_skills(),
    )
    packs = (
        SkillPolicyPack(
            pack_id="PACK-GLOBAL-FOUNDATION",
            name="Global courtroom reasoning skills",
            version=SKILL_POLICY_VERSION,
            category=SkillCategory.GLOBAL,
            skill_ids=tuple(
                skill.skill_id
                for skill in skills
                if skill.category == SkillCategory.GLOBAL
            ),
        ),
        SkillPolicyPack(
            pack_id="PACK-US-CA-CIVIL",
            name="California civil courtroom policy pack",
            version=SKILL_POLICY_VERSION,
            category=SkillCategory.JURISDICTION,
            jurisdiction_id=DEFAULT_JURISDICTION_ID,
            skill_ids=tuple(
                skill.skill_id
                for skill in skills
                if skill.category == SkillCategory.JURISDICTION
            ),
        ),
        SkillPolicyPack(
            pack_id="PACK-ROLE-COURTROOM-ACTORS",
            name="Courtroom actor role skills",
            version=SKILL_POLICY_VERSION,
            category=SkillCategory.ROLE,
            skill_ids=tuple(
                skill.skill_id
                for skill in skills
                if skill.category == SkillCategory.ROLE
            ),
        ),
        SkillPolicyPack(
            pack_id="PACK-PHASE-TRIAL",
            name="Trial phase skills",
            version=SKILL_POLICY_VERSION,
            category=SkillCategory.PHASE,
            skill_ids=tuple(
                skill.skill_id
                for skill in skills
                if skill.category == SkillCategory.PHASE
            ),
        ),
        SkillPolicyPack(
            pack_id="PACK-TACTICAL-FOUNDATION",
            name="Foundational trial tactics",
            version=SKILL_POLICY_VERSION,
            category=SkillCategory.TACTICAL,
            skill_ids=tuple(
                skill.skill_id
                for skill in skills
                if skill.category == SkillCategory.TACTICAL
            ),
        ),
    )
    return SkillRegistry(skills=skills, packs=packs)


def build_skill_load_request(
    *,
    jurisdiction_id: str,
    actor: Actor | None,
    node_purpose: NodePurpose,
    procedure: ProcedureState | None,
    action_type: ActionType | None = None,
    requested_skill_ids: tuple[str, ...] = (),
) -> SkillLoadRequest:
    resolved_action_type = action_type or _default_action_for_node_purpose(node_purpose)
    return SkillLoadRequest(
        jurisdiction_id=jurisdiction_id,
        role=actor.role if actor is not None else None,
        phase=procedure.phase if procedure is not None else None,
        node_purpose=node_purpose.value,
        action_type=resolved_action_type,
        requested_skill_ids=requested_skill_ids,
    )


def resolve_allowed_skill_load(
    request: SkillLoadRequest,
    registry: SkillRegistry | None = None,
) -> SkillLoadDecision:
    registry = registry or DEFAULT_SKILL_REGISTRY
    allowed_skill_ids: list[str] = []
    loaded_pack_ids: list[str] = []

    for skill in registry.skills():
        if _skill_allowed(skill, request):
            allowed_skill_ids.append(skill.skill_id)
            if skill.pack_id not in loaded_pack_ids:
                loaded_pack_ids.append(skill.pack_id)

    denied_ids: list[str] = []
    denial_reasons: list[str] = []
    allowed_set = set(allowed_skill_ids)
    known_set = set(registry.skill_ids())
    for skill_id in request.requested_skill_ids:
        if skill_id not in known_set:
            denied_ids.append(skill_id)
            denial_reasons.append(f"{skill_id} is not registered")
        elif skill_id not in allowed_set:
            denied_ids.append(skill_id)
            denial_reasons.append(
                f"{skill_id} is outside role, phase, jurisdiction, or action scope"
            )

    return SkillLoadDecision(
        allowed_skill_ids=tuple(allowed_skill_ids),
        loaded_pack_ids=tuple(loaded_pack_ids),
        denied_skill_ids=tuple(dict.fromkeys(denied_ids)),
        denial_reasons=tuple(denial_reasons),
    )


def validate_requested_skill_load(
    request: SkillLoadRequest,
    registry: SkillRegistry | None = None,
) -> SkillLoadDecision:
    decision = resolve_allowed_skill_load(request, registry)
    if not decision.allowed:
        raise ValueError("; ".join(decision.denial_reasons))
    return decision


def allowed_skill_ids_for_context(
    *,
    jurisdiction_id: str,
    actor: Actor | None,
    node_purpose: NodePurpose,
    procedure: ProcedureState | None,
    action_type: ActionType | None = None,
    registry: SkillRegistry | None = None,
) -> tuple[str, ...]:
    request = build_skill_load_request(
        jurisdiction_id=jurisdiction_id,
        actor=actor,
        node_purpose=node_purpose,
        procedure=procedure,
        action_type=action_type,
    )
    return resolve_allowed_skill_load(request, registry).allowed_skill_ids


def _skill_allowed(skill: SkillDefinition, request: SkillLoadRequest) -> bool:
    if skill.category == SkillCategory.GLOBAL:
        return True
    if skill.category == SkillCategory.JURISDICTION:
        return request.jurisdiction_id in skill.jurisdiction_ids
    if skill.allowed_roles and request.role not in skill.allowed_roles:
        return False
    if skill.allowed_phases and request.phase not in skill.allowed_phases:
        return False
    if (
        skill.allowed_node_purposes
        and request.node_purpose not in skill.allowed_node_purposes
    ):
        return False
    if skill.allowed_action_types:
        return request.action_type in skill.allowed_action_types
    return True


def _default_action_for_node_purpose(node_purpose: NodePurpose) -> ActionType | None:
    defaults = {
        NodePurpose.GLOBAL_STRATEGY: ActionType.PLAN_STRATEGY,
        NodePurpose.WITNESS_SELECTION: ActionType.SELECT_WITNESS,
        NodePurpose.EXAMINATION_OBJECTIVE: ActionType.PLAN_EXAMINATION_OBJECTIVE,
        NodePurpose.TACTICAL_ACTION_PLANNING: ActionType.PLAN_TACTICAL_ACTION,
        NodePurpose.QUESTION_GENERATION: ActionType.ASK_QUESTION,
        NodePurpose.OBJECTION_DECISION: ActionType.OBJECT,
        NodePurpose.OBJECTION_RULING: ActionType.RULE_ON_OBJECTION,
        NodePurpose.WITNESS_ANSWER: ActionType.ANSWER_PENDING_QUESTION,
        NodePurpose.ACTOR_EVALUATION: ActionType.EVALUATE,
        NodePurpose.COACHING: ActionType.COACH,
    }
    return defaults.get(node_purpose)


def _global_skills() -> tuple[SkillDefinition, ...]:
    return (
        SkillDefinition(
            skill_id="SKILL-GLOBAL-CITATION-GROUNDING",
            name="Citation grounding",
            category=SkillCategory.GLOBAL,
            description="Cite only supplied record, case, evidence, or rule sources.",
            pack_id="PACK-GLOBAL-FOUNDATION",
        ),
        SkillDefinition(
            skill_id="SKILL-GLOBAL-SOURCE-HIERARCHY",
            name="Source hierarchy",
            category=SkillCategory.GLOBAL,
            description="Prefer controlling legal authority and admitted record over weaker sources.",
            pack_id="PACK-GLOBAL-FOUNDATION",
        ),
        SkillDefinition(
            skill_id="SKILL-GLOBAL-UNCERTAINTY-HANDLING",
            name="Uncertainty handling",
            category=SkillCategory.GLOBAL,
            description="State uncertainty when the visible record does not support a firm conclusion.",
            pack_id="PACK-GLOBAL-FOUNDATION",
        ),
        SkillDefinition(
            skill_id="SKILL-GLOBAL-ROLE-BOUNDARY-COMPLIANCE",
            name="Role-boundary compliance",
            category=SkillCategory.GLOBAL,
            description="Act only from the current role's visible context and authority.",
            pack_id="PACK-GLOBAL-FOUNDATION",
        ),
        SkillDefinition(
            skill_id="SKILL-GLOBAL-PROFESSIONAL-CONDUCT",
            name="Professional conduct",
            category=SkillCategory.GLOBAL,
            description="Maintain courtroom-appropriate conduct and avoid improper argument.",
            pack_id="PACK-GLOBAL-FOUNDATION",
        ),
        SkillDefinition(
            skill_id="SKILL-GLOBAL-EVIDENCE-PROVENANCE",
            name="Evidence provenance",
            category=SkillCategory.GLOBAL,
            description="Track which exhibit, testimony, or fact source supports every claim.",
            pack_id="PACK-GLOBAL-FOUNDATION",
        ),
    )


def _california_jurisdiction_skills() -> tuple[SkillDefinition, ...]:
    return (
        SkillDefinition(
            skill_id="SKILL-US-CA-CIVIL-PROCEDURE",
            name="California civil procedure",
            category=SkillCategory.JURISDICTION,
            description="Apply California-oriented civil procedure constraints for the trial simulation.",
            pack_id="PACK-US-CA-CIVIL",
            jurisdiction_ids=(DEFAULT_JURISDICTION_ID,),
        ),
        SkillDefinition(
            skill_id="SKILL-US-CA-EVIDENCE",
            name="California evidence",
            category=SkillCategory.JURISDICTION,
            description="Apply California-oriented evidence concepts including foundation and admissibility.",
            pack_id="PACK-US-CA-CIVIL",
            jurisdiction_ids=(DEFAULT_JURISDICTION_ID,),
        ),
        SkillDefinition(
            skill_id="SKILL-US-CA-CACI",
            name="CACI instructions",
            category=SkillCategory.JURISDICTION,
            description="Map civil claims and defenses to CACI-oriented element language.",
            pack_id="PACK-US-CA-CIVIL",
            jurisdiction_ids=(DEFAULT_JURISDICTION_ID,),
        ),
        SkillDefinition(
            skill_id="SKILL-US-CA-LOCAL-COURT-RULES",
            name="Local court rules",
            category=SkillCategory.JURISDICTION,
            description="Reserve local-rule constraints as a jurisdiction-scoped policy surface.",
            pack_id="PACK-US-CA-CIVIL",
            jurisdiction_ids=(DEFAULT_JURISDICTION_ID,),
        ),
    )


def _role_skills() -> tuple[SkillDefinition, ...]:
    return (
        SkillDefinition(
            skill_id="SKILL-ROLE-PLAINTIFF-PROSECUTION-LAWYER",
            name="Plaintiff/prosecution lawyer",
            category=SkillCategory.ROLE,
            description="Advance the initiating party's burden with grounded trial strategy.",
            pack_id="PACK-ROLE-COURTROOM-ACTORS",
            allowed_roles=(ActorRole.PLAINTIFF_LAWYER, ActorRole.PROSECUTION_LAWYER),
        ),
        SkillDefinition(
            skill_id="SKILL-ROLE-DEFENSE-LAWYER",
            name="Defense lawyer",
            category=SkillCategory.ROLE,
            description="Attack proof gaps, credibility, causation, and admissibility from defense posture.",
            pack_id="PACK-ROLE-COURTROOM-ACTORS",
            allowed_roles=(ActorRole.DEFENSE_LAWYER,),
        ),
        SkillDefinition(
            skill_id="SKILL-ROLE-TRIAL-JUDGE",
            name="Trial judge",
            category=SkillCategory.ROLE,
            description="Control procedure, rule on objections, and apply law to the record.",
            pack_id="PACK-ROLE-COURTROOM-ACTORS",
            allowed_roles=(ActorRole.TRIAL_JUDGE,),
        ),
        SkillDefinition(
            skill_id="SKILL-ROLE-JUROR",
            name="Juror",
            category=SkillCategory.ROLE,
            description="Reason only from admitted evidence and court instructions.",
            pack_id="PACK-ROLE-COURTROOM-ACTORS",
            allowed_roles=(ActorRole.JURY,),
        ),
        SkillDefinition(
            skill_id="SKILL-ROLE-WITNESS",
            name="Witness",
            category=SkillCategory.ROLE,
            description="Answer from personal knowledge without adopting lawyer strategy.",
            pack_id="PACK-ROLE-COURTROOM-ACTORS",
            allowed_roles=(ActorRole.WITNESS,),
        ),
    )


def _phase_skills() -> tuple[SkillDefinition, ...]:
    return (
        _phase_skill("SKILL-PHASE-OPENING", "Opening statement", TrialPhase.OPENING),
        _phase_skill(
            "SKILL-PHASE-DIRECT",
            "Direct examination",
            TrialPhase.WITNESS_EXAMINATION,
            node_purposes=(
                NodePurpose.EXAMINATION_OBJECTIVE.value,
                NodePurpose.TACTICAL_ACTION_PLANNING.value,
                NodePurpose.QUESTION_GENERATION.value,
            ),
        ),
        _phase_skill(
            "SKILL-PHASE-CROSS",
            "Cross-examination",
            TrialPhase.WITNESS_EXAMINATION,
            node_purposes=(
                NodePurpose.EXAMINATION_OBJECTIVE.value,
                NodePurpose.TACTICAL_ACTION_PLANNING.value,
                NodePurpose.QUESTION_GENERATION.value,
            ),
        ),
        _phase_skill(
            "SKILL-PHASE-REDIRECT",
            "Redirect",
            TrialPhase.WITNESS_EXAMINATION,
            node_purposes=(
                NodePurpose.EXAMINATION_OBJECTIVE.value,
                NodePurpose.TACTICAL_ACTION_PLANNING.value,
                NodePurpose.QUESTION_GENERATION.value,
            ),
        ),
        _phase_skill(
            "SKILL-PHASE-OBJECTIONS",
            "Objections",
            TrialPhase.WITNESS_EXAMINATION,
            node_purposes=(
                NodePurpose.OBJECTION_DECISION.value,
                NodePurpose.OBJECTION_RULING.value,
            ),
        ),
        _phase_skill("SKILL-PHASE-CLOSING", "Closing argument", TrialPhase.CLOSING),
        _phase_skill(
            "SKILL-PHASE-DELIBERATION",
            "Deliberation",
            TrialPhase.DELIBERATION,
            roles=(ActorRole.TRIAL_JUDGE, ActorRole.JURY),
        ),
    )


def _phase_skill(
    skill_id: str,
    name: str,
    phase: TrialPhase,
    *,
    roles: tuple[ActorRole, ...] = LAWYER_ROLES,
    node_purposes: tuple[str, ...] = (),
) -> SkillDefinition:
    return SkillDefinition(
        skill_id=skill_id,
        name=name,
        category=SkillCategory.PHASE,
        description=f"Apply phase-specific reasoning for {name.lower()}.",
        pack_id="PACK-PHASE-TRIAL",
        allowed_roles=roles,
        allowed_phases=(phase,),
        allowed_node_purposes=node_purposes,
    )


def _tactical_skills() -> tuple[SkillDefinition, ...]:
    tactical_node_purposes = (
        NodePurpose.TACTICAL_ACTION_PLANNING.value,
        NodePurpose.QUESTION_GENERATION.value,
        NodePurpose.OBJECTION_DECISION.value,
        NodePurpose.OBJECTION_RULING.value,
    )
    return (
        SkillDefinition(
            skill_id="SKILL-TACTIC-AUTHENTICATION",
            name="Authentication",
            category=SkillCategory.TACTICAL,
            description="Establish that an exhibit is what the proponent claims it is.",
            pack_id="PACK-TACTICAL-FOUNDATION",
            allowed_roles=(*LAWYER_ROLES, ActorRole.TRIAL_JUDGE),
            allowed_phases=(TrialPhase.WITNESS_EXAMINATION,),
            allowed_node_purposes=tactical_node_purposes,
            allowed_action_types=(
                ActionType.PLAN_TACTICAL_ACTION,
                ActionType.ASK_QUESTION,
                ActionType.OFFER_EVIDENCE,
                ActionType.ADMIT_EVIDENCE,
            ),
        ),
        SkillDefinition(
            skill_id="SKILL-TACTIC-PERSONAL-KNOWLEDGE",
            name="Personal knowledge",
            category=SkillCategory.TACTICAL,
            description="Establish or challenge a witness's basis to testify.",
            pack_id="PACK-TACTICAL-FOUNDATION",
            allowed_roles=(*LAWYER_ROLES, ActorRole.TRIAL_JUDGE),
            allowed_phases=(TrialPhase.WITNESS_EXAMINATION,),
            allowed_node_purposes=tactical_node_purposes,
            allowed_action_types=(
                ActionType.PLAN_TACTICAL_ACTION,
                ActionType.ASK_QUESTION,
                ActionType.OBJECT,
                ActionType.RULE_ON_OBJECTION,
            ),
        ),
        SkillDefinition(
            skill_id="SKILL-TACTIC-IMPEACH-PRIOR-STATEMENT",
            name="Impeachment with prior statement",
            category=SkillCategory.TACTICAL,
            description="Use an inconsistent prior statement to attack credibility.",
            pack_id="PACK-TACTICAL-FOUNDATION",
            allowed_roles=LAWYER_ROLES,
            allowed_phases=(TrialPhase.WITNESS_EXAMINATION,),
            allowed_node_purposes=tactical_node_purposes,
            allowed_action_types=(
                ActionType.PLAN_TACTICAL_ACTION,
                ActionType.ASK_QUESTION,
            ),
        ),
        SkillDefinition(
            skill_id="SKILL-TACTIC-PERCEPTION-CHALLENGE",
            name="Perception challenge",
            category=SkillCategory.TACTICAL,
            description="Test what a witness could see, hear, perceive, or recall.",
            pack_id="PACK-TACTICAL-FOUNDATION",
            allowed_roles=LAWYER_ROLES,
            allowed_phases=(TrialPhase.WITNESS_EXAMINATION,),
            allowed_node_purposes=tactical_node_purposes,
            allowed_action_types=(
                ActionType.PLAN_TACTICAL_ACTION,
                ActionType.ASK_QUESTION,
            ),
        ),
        SkillDefinition(
            skill_id="SKILL-TACTIC-BIAS-EXPOSURE",
            name="Bias exposure",
            category=SkillCategory.TACTICAL,
            description="Reveal motives, relationships, or incentives affecting credibility.",
            pack_id="PACK-TACTICAL-FOUNDATION",
            allowed_roles=LAWYER_ROLES,
            allowed_phases=(TrialPhase.WITNESS_EXAMINATION,),
            allowed_node_purposes=tactical_node_purposes,
            allowed_action_types=(
                ActionType.PLAN_TACTICAL_ACTION,
                ActionType.ASK_QUESTION,
            ),
        ),
        SkillDefinition(
            skill_id="SKILL-TACTIC-CAUSATION",
            name="Causation",
            category=SkillCategory.TACTICAL,
            description="Connect or contest the chain between conduct, harm, and damages.",
            pack_id="PACK-TACTICAL-FOUNDATION",
            allowed_roles=LAWYER_ROLES,
            allowed_phases=(
                TrialPhase.STRATEGY,
                TrialPhase.WITNESS_EXAMINATION,
                TrialPhase.CLOSING,
            ),
            allowed_node_purposes=(
                NodePurpose.GLOBAL_STRATEGY.value,
                NodePurpose.TACTICAL_ACTION_PLANNING.value,
                NodePurpose.QUESTION_GENERATION.value,
            ),
            allowed_action_types=(
                ActionType.PLAN_STRATEGY,
                ActionType.PLAN_TACTICAL_ACTION,
                ActionType.ASK_QUESTION,
                ActionType.ARGUE,
            ),
        ),
    )


DEFAULT_SKILL_REGISTRY = build_default_skill_registry()
