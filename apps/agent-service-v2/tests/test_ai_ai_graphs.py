from __future__ import annotations

import json
from pathlib import Path

from agent_service_v2.flows.ai_ai import (
    V2AiAiState,
    build_ai_ai_trial_graph,
    build_ai_ai_witness_loop_graph,
)


def test_ai_ai_trial_graph_reaches_coaching_complete() -> None:
    result = build_ai_ai_trial_graph().invoke(V2AiAiState())

    assert result["status"] == "coaching_complete"
    assert result["runtime"].phase == "complete"
    assert "evaluation" in result["phase_outputs"]
    assert "coaching" in result["phase_outputs"]
    assert result["witness_examinations"]


def test_ai_ai_witness_loop_graph_stops_after_witness_loop() -> None:
    result = build_ai_ai_witness_loop_graph().invoke(V2AiAiState())

    assert result["status"] == "witness_loop_complete"
    assert result["runtime"].phase == "closing_record"
    assert sorted(result["phase_outputs"]) == [
        "analyze_case",
        "initialize_session",
        "opening",
        "plan_sides",
        "witness_loop",
    ]


def test_langgraph_config_registers_v2_graphs() -> None:
    config_path = Path(__file__).resolve().parents[1] / "langgraph.json"
    config = json.loads(config_path.read_text())

    assert config["graphs"] == {
        "ai-ai-trial": "./src/agent_service_v2/studio.py:ai_ai_trial",
        "ai-ai-witness-loop": "./src/agent_service_v2/studio.py:ai_ai_witness_loop",
        "ai-ai-evaluation": "./src/agent_service_v2/studio.py:ai_ai_evaluation",
    }
