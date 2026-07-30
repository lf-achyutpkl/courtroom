from __future__ import annotations

import unittest

from courtroom_engine import (
    ActionType,
    ActorRole,
    CaseCompiler,
    ContextBoundaryService,
    ContextRequest,
    NodePurpose,
    ProcedureState,
    TrialPhase,
    TrialRuntimeState,
)
from courtroom_engine.fixtures import build_reference_case
from courtroom_engine.policies.skills import (
    DEFAULT_SKILL_REGISTRY,
    build_skill_load_request,
    resolve_allowed_skill_load,
    validate_requested_skill_load,
)


class SkillRegistryTests(unittest.TestCase):
    def test_default_registry_covers_required_skill_packs(self) -> None:
        skill_ids = set(DEFAULT_SKILL_REGISTRY.skill_ids())

        self.assertTrue(
            {
                "SKILL-GLOBAL-CITATION-GROUNDING",
                "SKILL-GLOBAL-SOURCE-HIERARCHY",
                "SKILL-GLOBAL-UNCERTAINTY-HANDLING",
                "SKILL-GLOBAL-ROLE-BOUNDARY-COMPLIANCE",
                "SKILL-GLOBAL-PROFESSIONAL-CONDUCT",
                "SKILL-GLOBAL-EVIDENCE-PROVENANCE",
                "SKILL-US-CA-CIVIL-PROCEDURE",
                "SKILL-US-CA-EVIDENCE",
                "SKILL-US-CA-CACI",
                "SKILL-US-CA-LOCAL-COURT-RULES",
                "SKILL-ROLE-PLAINTIFF-PROSECUTION-LAWYER",
                "SKILL-ROLE-DEFENSE-LAWYER",
                "SKILL-ROLE-TRIAL-JUDGE",
                "SKILL-ROLE-JUROR",
                "SKILL-ROLE-WITNESS",
                "SKILL-PHASE-OPENING",
                "SKILL-PHASE-DIRECT",
                "SKILL-PHASE-CROSS",
                "SKILL-PHASE-REDIRECT",
                "SKILL-PHASE-OBJECTIONS",
                "SKILL-PHASE-CLOSING",
                "SKILL-PHASE-DELIBERATION",
                "SKILL-TACTIC-AUTHENTICATION",
                "SKILL-TACTIC-PERSONAL-KNOWLEDGE",
                "SKILL-TACTIC-IMPEACH-PRIOR-STATEMENT",
                "SKILL-TACTIC-PERCEPTION-CHALLENGE",
                "SKILL-TACTIC-BIAS-EXPOSURE",
                "SKILL-TACTIC-CAUSATION",
            }.issubset(skill_ids)
        )
        self.assertIn("PACK-US-CA-CIVIL", DEFAULT_SKILL_REGISTRY.pack_ids())

    def test_plaintiff_question_generation_gets_scoped_trial_skills(self) -> None:
        package = CaseCompiler().compile(build_reference_case())
        plaintiff = next(
            actor
            for actor in package.actors
            if actor.role == ActorRole.PLAINTIFF_LAWYER
        )
        request = build_skill_load_request(
            jurisdiction_id=package.metadata.jurisdiction,
            actor=plaintiff,
            node_purpose=NodePurpose.QUESTION_GENERATION,
            procedure=ProcedureState(phase=TrialPhase.WITNESS_EXAMINATION),
            action_type=ActionType.ASK_QUESTION,
        )

        decision = resolve_allowed_skill_load(request)

        self.assertIn("SKILL-GLOBAL-CITATION-GROUNDING", decision.allowed_skill_ids)
        self.assertIn(
            "SKILL-ROLE-PLAINTIFF-PROSECUTION-LAWYER", decision.allowed_skill_ids
        )
        self.assertIn("SKILL-PHASE-DIRECT", decision.allowed_skill_ids)
        self.assertIn("SKILL-TACTIC-PERSONAL-KNOWLEDGE", decision.allowed_skill_ids)
        self.assertNotIn("SKILL-ROLE-DEFENSE-LAWYER", decision.allowed_skill_ids)
        self.assertNotIn("SKILL-PHASE-DELIBERATION", decision.allowed_skill_ids)

    def test_witness_cannot_request_lawyer_tactical_skill(self) -> None:
        package = CaseCompiler().compile(build_reference_case())
        witness = next(
            actor for actor in package.actors if actor.role == ActorRole.WITNESS
        )
        request = build_skill_load_request(
            jurisdiction_id=package.metadata.jurisdiction,
            actor=witness,
            node_purpose=NodePurpose.WITNESS_ANSWER,
            procedure=ProcedureState(phase=TrialPhase.WITNESS_EXAMINATION),
            action_type=ActionType.ANSWER_PENDING_QUESTION,
            requested_skill_ids=("SKILL-TACTIC-IMPEACH-PRIOR-STATEMENT",),
        )

        decision = resolve_allowed_skill_load(request)

        self.assertFalse(decision.allowed)
        self.assertEqual(
            decision.denied_skill_ids, ("SKILL-TACTIC-IMPEACH-PRIOR-STATEMENT",)
        )
        with self.assertRaisesRegex(ValueError, "outside role, phase"):
            validate_requested_skill_load(request)

    def test_unknown_skill_is_rejected_fail_closed(self) -> None:
        request = build_skill_load_request(
            jurisdiction_id="US-CA",
            actor=None,
            node_purpose=NodePurpose.INITIAL_CASE_ANALYSIS,
            procedure=ProcedureState(phase=TrialPhase.CASE_INTELLIGENCE),
            requested_skill_ids=("SKILL-UNREGISTERED",),
        )

        decision = resolve_allowed_skill_load(request)

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.denied_skill_ids, ("SKILL-UNREGISTERED",))
        self.assertIn("SKILL-UNREGISTERED is not registered", decision.denial_reasons)

    def test_context_metadata_exposes_allowed_skill_ids(self) -> None:
        package = CaseCompiler().compile(build_reference_case())
        plaintiff = next(
            actor
            for actor in package.actors
            if actor.role == ActorRole.PLAINTIFF_LAWYER
        )
        runtime = TrialRuntimeState(
            case_id=package.metadata.case_id,
            phase=TrialPhase.STRATEGY.value,
            procedure=ProcedureState(phase=TrialPhase.STRATEGY),
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

        self.assertIn(
            "SKILL-GLOBAL-EVIDENCE-PROVENANCE", context.metadata.allowed_skill_ids
        )
        self.assertIn(
            "SKILL-ROLE-PLAINTIFF-PROSECUTION-LAWYER",
            context.metadata.allowed_skill_ids,
        )
        self.assertIn("SKILL-TACTIC-CAUSATION", context.metadata.allowed_skill_ids)
        self.assertNotIn(
            "SKILL-ROLE-DEFENSE-LAWYER", context.metadata.allowed_skill_ids
        )
        self.assertIn("PACK-GLOBAL-FOUNDATION", context.metadata.loaded_skill_pack_ids)


if __name__ == "__main__":
    unittest.main()
