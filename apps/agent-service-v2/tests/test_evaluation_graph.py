from __future__ import annotations

from agent_service_v2.evaluation import EvaluationState, build_evaluation_graph
from agent_service_v2.flows.ai_ai import V2AiAiState, build_ai_ai_trial_graph


def test_evaluation_graph_runs_from_trial_outputs() -> None:
    trial_result = build_ai_ai_trial_graph().invoke(V2AiAiState())

    result = build_evaluation_graph().invoke(
        EvaluationState(
            case_package=trial_result["case_package"],
            runtime=trial_result["runtime"],
            strategies=tuple(trial_result["strategies"].values()),
            witness_examinations=tuple(trial_result["witness_examinations"]),
            deliberation=trial_result["deliberation"],
        )
    )

    assert result["status"] == "evaluation_complete"
    assert result["report"] is not None
    assert result["report"].observations
