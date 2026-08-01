"""V2 runtime environment loading and provider configuration validation."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


class RuntimeConfigurationError(RuntimeError):
    """Raised when required V2 provider configuration is absent."""


def _workspace_env_file() -> Path:
    return Path(__file__).resolve().parents[3] / ".env"


def _is_enabled(value: str | None) -> bool:
    return value is not None and value.strip().lower() in {"1", "true", "yes", "on"}


def configure_runtime_environment(*, environment_file: Path | None = None) -> None:
    """Load V2's local dotenv file and validate provider configuration.

    Explicit process variables take precedence so deployments can use their
    normal secret-management mechanism instead of a local dotenv file.
    """

    load_dotenv(dotenv_path=environment_file or _workspace_env_file(), override=False)

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeConfigurationError(
            "OPENAI_API_KEY is required for agent-service-v2. Copy .env.example "
            "to .env and set the key, or provide it through the process environment."
        )

    if _is_enabled(os.getenv("LANGSMITH_TRACING")):
        missing = [
            name
            for name in ("LANGSMITH_API_KEY", "LANGSMITH_PROJECT")
            if not os.getenv(name)
        ]
        if missing:
            raise RuntimeConfigurationError(
                "LangSmith tracing is enabled but missing {}. Set it in .env or "
                "the process environment.".format(", ".join(missing))
            )
