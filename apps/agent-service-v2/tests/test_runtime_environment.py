from __future__ import annotations

import os
from pathlib import Path

import pytest

from agent_service_v2.shared.runtime_environment import (
    RuntimeConfigurationError,
    configure_runtime_environment,
)


def _clear_provider_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "OPENAI_API_KEY",
        "LANGSMITH_TRACING",
        "LANGSMITH_API_KEY",
        "LANGSMITH_PROJECT",
    ):
        monkeypatch.delenv(name, raising=False)


def test_runtime_configuration_loads_dotenv_without_overriding_process_values(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _clear_provider_environment(monkeypatch)
    environment_file = tmp_path / ".env"
    environment_file.write_text(
        "OPENAI_API_KEY=dotenv-key\nLANGSMITH_TRACING=false\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENAI_API_KEY", "process-key")

    configure_runtime_environment(environment_file=environment_file)

    assert os.environ["OPENAI_API_KEY"] == "process-key"


def test_runtime_configuration_rejects_missing_openai_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _clear_provider_environment(monkeypatch)

    with pytest.raises(RuntimeConfigurationError, match="OPENAI_API_KEY"):
        configure_runtime_environment(environment_file=tmp_path / ".env")


def test_runtime_configuration_requires_complete_langsmith_when_enabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _clear_provider_environment(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")

    with pytest.raises(RuntimeConfigurationError, match="LANGSMITH_API_KEY"):
        configure_runtime_environment(environment_file=tmp_path / ".env")
