from __future__ import annotations

from agent_service_v2.evaluation import build_evaluation_graph
from agent_service_v2.flows.ai_ai import (
    build_ai_ai_trial_graph,
    build_ai_ai_witness_loop_graph,
)

ai_ai_trial = build_ai_ai_trial_graph()
ai_ai_witness_loop = build_ai_ai_witness_loop_graph()
ai_ai_evaluation = build_evaluation_graph()

__all__ = ["ai_ai_evaluation", "ai_ai_trial", "ai_ai_witness_loop"]
