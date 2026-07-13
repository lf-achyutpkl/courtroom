from dataclasses import dataclass


@dataclass(frozen=True)
class TrialRuntimeConfig:
    max_questions_per_phase: int = 4
    context_window_turns: int = 4
    skip_direct_objections: bool = True


TRIAL_CONFIG = TrialRuntimeConfig()
