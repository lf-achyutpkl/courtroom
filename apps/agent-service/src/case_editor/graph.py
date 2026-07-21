from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from .nodes import make_process_edit_node, narrate_node
from .state import CaseEditorState, CaseFileStore


def build_case_editor_graph(*, case_files: CaseFileStore, checkpointer: Any):
    builder = StateGraph(CaseEditorState)
    builder.add_node("process_edit", make_process_edit_node(case_files))
    builder.add_node("narrate", narrate_node)
    builder.add_edge(START, "process_edit")
    builder.add_edge("process_edit", "narrate")
    builder.add_edge("narrate", END)
    return builder.compile(checkpointer=checkpointer)
