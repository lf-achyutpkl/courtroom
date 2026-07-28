from __future__ import annotations

from enum import StrEnum


class VisibilityScope(StrEnum):
    PUBLIC_CASE = "public_case"
    PLAINTIFF_PRIVATE = "plaintiff_private"
    PROSECUTION_PRIVATE = "prosecution_private"
    DEFENSE_PRIVATE = "defense_private"
    WITNESS_PRIVATE = "witness_private"
    JUDGE_ONLY = "judge_only"
    EVALUATOR_ONLY = "evaluator_only"
    COACH_ONLY = "coach_only"
