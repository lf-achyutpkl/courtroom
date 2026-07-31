from __future__ import annotations

import json
from pathlib import Path

from agent_service_v2.flows.ai_ai import (
    V2AiAiState,
    build_ai_ai_trial_graph,
)
from agent_service_v2.flows.ai_ai.witness_graph import build_witness_examination_graph


def test_ai_ai_trial_graph_reaches_coaching_complete() -> None:
    result = build_ai_ai_trial_graph().invoke(V2AiAiState())

    assert result["status"] == "learning_trace_persisted"
    assert result["runtime"].phase == "complete"
    assert "evaluation" in result["phase_outputs"]
    assert "coaching" in result["phase_outputs"]
    assert "persist_learning_trace" in result["phase_outputs"]
    assert result["witness_examinations"]
    assert result["closing_record"] is not None
    assert result["learning_trace"] is not None
    assert result["trace"]


def test_ai_ai_trial_graph_exposes_documented_phase_nodes() -> None:
    graph = build_ai_ai_trial_graph().get_graph()

    assert {
        "initialize_session",
        "analyze_case",
        "plan_prosecution_case",
        "plan_defense_case",
        "finalize_trial_plan",
        "run_opening_phase",
        "select_next_witness",
        "run_witness_examination",
        "update_trial_position",
        "prepare_closings",
        "run_closing_phase",
        "run_deliberation",
        "run_evaluation",
        "generate_coaching",
        "persist_learning_trace",
    }.issubset(graph.nodes)
    conditional_edges = {
        (edge.source, edge.target, edge.data)
        for edge in graph.edges
        if edge.conditional
    }
    assert (
        "select_next_witness",
        "run_witness_examination",
        "examine",
    ) in conditional_edges
    assert ("select_next_witness", "prepare_closings", "complete") in conditional_edges


def test_witness_examination_graph_exposes_traceable_action_pipeline() -> None:
    graph = build_witness_examination_graph().get_graph()

    assert {
        "initialize_examination",
        "select_objective",
        "plan_action",
        "validate_action",
        "generate_question",
        "objection_decision",
        "judge_ruling",
        "witness_answer",
        "validate_witness_answer",
        "update_evidence_state",
        "detect_new_contradictions",
        "assess_objective_progress",
        "transition_examination",
        "finalize_witness",
    }.issubset(graph.nodes)
    conditional_edges = {
        (edge.source, edge.target, edge.data)
        for edge in graph.edges
        if edge.conditional
    }
    assert ("validate_action", "generate_question", "valid") in conditional_edges
    assert ("objection_decision", "judge_ruling", "object") in conditional_edges
    assert (
        "validate_witness_answer",
        "update_evidence_state",
        "flag",
    ) in conditional_edges


def test_langgraph_config_registers_v2_graphs() -> None:
    config_path = Path(__file__).resolve().parents[1] / "langgraph.json"
    config = json.loads(config_path.read_text())

    assert config["graphs"] == {
        "ai-ai-trial": "./src/agent_service_v2/studio.py:ai_ai_trial",
        "ai-ai-evaluation": "./src/agent_service_v2/studio.py:ai_ai_evaluation",
    }
