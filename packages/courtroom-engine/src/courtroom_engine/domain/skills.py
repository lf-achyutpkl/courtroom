from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.case import ActorRole
from courtroom_engine.domain.procedure import ActionType, TrialPhase


class SkillCategory(StrEnum):
    GLOBAL = "global"
    JURISDICTION = "jurisdiction"
    ROLE = "role"
    PHASE = "phase"
    TACTICAL = "tactical"


class SkillDefinition(DomainModel):
    skill_id: str
    name: str
    category: SkillCategory
    description: str
    pack_id: str
    jurisdiction_ids: tuple[str, ...] = ()
    allowed_roles: tuple[ActorRole, ...] = ()
    allowed_phases: tuple[TrialPhase, ...] = ()
    allowed_node_purposes: tuple[str, ...] = ()
    allowed_action_types: tuple[ActionType, ...] = ()
    prerequisite_skill_ids: tuple[str, ...] = ()


class SkillPolicyPack(DomainModel):
    pack_id: str
    name: str
    version: str
    category: SkillCategory
    jurisdiction_id: str | None = None
    skill_ids: tuple[str, ...] = ()


class SkillLoadDecision(DomainModel):
    allowed_skill_ids: tuple[str, ...] = ()
    loaded_pack_ids: tuple[str, ...] = ()
    denied_skill_ids: tuple[str, ...] = ()
    denial_reasons: tuple[str, ...] = ()

    @property
    def allowed(self) -> bool:
        return not self.denied_skill_ids and not self.denial_reasons


class SkillRegistry:
    def __init__(
        self,
        *,
        skills: tuple[SkillDefinition, ...],
        packs: tuple[SkillPolicyPack, ...],
    ) -> None:
        self._skills = {skill.skill_id: skill for skill in skills}
        self._packs = {pack.pack_id: pack for pack in packs}
        if len(self._skills) != len(skills):
            raise ValueError("skill registry contains duplicate skill IDs")
        if len(self._packs) != len(packs):
            raise ValueError("skill registry contains duplicate pack IDs")
        self._validate_pack_references()

    def get(self, skill_id: str) -> SkillDefinition:
        try:
            return self._skills[skill_id]
        except KeyError as exc:
            raise KeyError(f"unknown skill ID: {skill_id}") from exc

    def get_pack(self, pack_id: str) -> SkillPolicyPack:
        try:
            return self._packs[pack_id]
        except KeyError as exc:
            raise KeyError(f"unknown skill policy pack ID: {pack_id}") from exc

    def skills(self) -> tuple[SkillDefinition, ...]:
        return tuple(self._skills.values())

    def packs(self) -> tuple[SkillPolicyPack, ...]:
        return tuple(self._packs.values())

    def skill_ids(self) -> tuple[str, ...]:
        return tuple(self._skills)

    def pack_ids(self) -> tuple[str, ...]:
        return tuple(self._packs)

    def _validate_pack_references(self) -> None:
        unknown_ids: list[str] = []
        for pack in self._packs.values():
            unknown_ids.extend(
                skill_id for skill_id in pack.skill_ids if skill_id not in self._skills
            )
        if unknown_ids:
            raise ValueError(
                "skill policy packs reference unknown skills: "
                + ", ".join(sorted(set(unknown_ids)))
            )


class SkillLoadRequest(DomainModel):
    jurisdiction_id: str = "US-CA"
    role: ActorRole | None = None
    phase: TrialPhase | None = None
    node_purpose: str
    action_type: ActionType | None = None
    requested_skill_ids: tuple[str, ...] = Field(default=())
