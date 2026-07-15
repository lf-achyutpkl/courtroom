import os
from dataclasses import dataclass

from .env import load_service_env


load_service_env()


@dataclass(frozen=True)
class TrialRuntimeConfig:
    max_questions_per_phase: int = 4
    context_window_turns: int = 4
    skip_direct_objections: bool = True
    graph_version: str = "v1"
    prompt_version: str = "v1"
    environment: str = os.getenv("COURTROOM_RUNTIME_ENV", "local")


TRIAL_CONFIG = TrialRuntimeConfig()
