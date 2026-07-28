from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from .compiler import CaseCompiler
from .context import ContextBoundaryService, ContextRequest, NodePurpose
from .fixtures import build_reference_case
from .models import CompiledCasePackage, TrialRuntimeState


class V2AiAiState(BaseModel):
    case_package: CompiledCasePackage | None = None
    runtime: TrialRuntimeState | None = None
    status: str = "created"
    boundary_context_ids: list[str] = Field(default_factory=list)


def initialize_session_node(state: V2AiAiState) -> V2AiAiState:
    compiler = CaseCompiler()
    case_package = compiler.compile(build_reference_case())
    runtime = TrialRuntimeState(
        case_id=case_package.metadata.case_id,
        phase="case_intelligence",
        public_event_summaries=("V2 AI-vs-AI session initialized.",),
    )
    return state.model_copy(
        update={
            "case_package": case_package,
            "runtime": runtime,
            "status": "initialized",
        }
    )


def verify_context_boundaries_node(state: V2AiAiState) -> V2AiAiState:
    if state.case_package is None or state.runtime is None:
        raise ValueError("V2 session must be initialized before boundary verification")
    plaintiff_actor = next(
        actor
        for actor in state.case_package.actors
        if actor.role.value in {"plaintiff_lawyer", "prosecution_lawyer"}
    )
    witness_actor = next(
        actor for actor in state.case_package.actors if actor.role.value == "witness"
    )
    boundary = ContextBoundaryService()
    plaintiff_context = boundary.build(
        case_package=state.case_package,
        state=state.runtime,
        request=ContextRequest(
            session_id=state.runtime.session_id,
            node_purpose=NodePurpose.GLOBAL_STRATEGY,
            requesting_actor_id=plaintiff_actor.actor_id,
        ),
    )
    witness_context = boundary.build(
        case_package=state.case_package,
        state=state.runtime.model_copy(
            update={
                "phase": "witness_answer",
                "current_witness_id": witness_actor.witness_id,
            }
        ),
        request=ContextRequest(
            session_id=state.runtime.session_id,
            node_purpose=NodePurpose.WITNESS_ANSWER,
            requesting_actor_id=witness_actor.actor_id,
        ),
    )
    return state.model_copy(
        update={
            "status": "context_boundaries_verified",
            "boundary_context_ids": [
                *state.boundary_context_ids,
                *plaintiff_context.metadata.included_object_ids,
                *witness_context.metadata.included_object_ids,
            ],
        }
    )


def build_v2_ai_ai_graph():
    builder = StateGraph(V2AiAiState)
    builder.add_node("initialize_session", initialize_session_node)
    builder.add_node("verify_context_boundaries", verify_context_boundaries_node)
    builder.add_edge(START, "initialize_session")
    builder.add_edge("initialize_session", "verify_context_boundaries")
    builder.add_edge("verify_context_boundaries", END)
    return builder.compile()
