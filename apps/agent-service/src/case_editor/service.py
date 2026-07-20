from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from courtroom_domain import CaseEditResult, SelectedCard
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver

from .graph import build_case_editor_graph
from .state import CaseEditorState, CaseFileStore


@dataclass(frozen=True)
class CaseEditorStreamEvent:
    event_type: str
    payload: dict[str, Any]


@contextmanager
def build_postgres_checkpointer(database_url: str) -> Iterator[PostgresSaver]:
    with PostgresSaver.from_conn_string(database_url) as checkpointer:
        checkpointer.setup()
        yield checkpointer


def stream_case_edit(
    *,
    case_file_id: UUID,
    user_message: str,
    selected_card: SelectedCard | None,
    case_files: CaseFileStore,
    checkpointer: PostgresSaver,
) -> Iterator[CaseEditorStreamEvent]:
    graph = build_case_editor_graph(case_files=case_files, checkpointer=checkpointer)
    state = CaseEditorState(
        case_file_id=str(case_file_id),
        user_message=user_message,
        selected_card_type=selected_card.card_type.value if selected_card else None,
        selected_card_id=selected_card.card_id if selected_card else None,
        messages=[HumanMessage(content=user_message)],
    )
    config = {
        "configurable": {
            "thread_id": str(case_file_id),
            "checkpoint_ns": "case_editor",
        }
    }
    for update in graph.stream(state, config=config, stream_mode="updates"):
        for node_name, node_payload in update.items():
            if node_name == "process_edit":
                edit_result = _extract_edit_result(node_payload)
                yield CaseEditorStreamEvent(
                    event_type="edit_result",
                    payload={
                        "id": _event_id_for_edit_result(edit_result),
                        "edit_result": edit_result.model_dump(mode="json"),
                    },
                )
            elif node_name == "narrate":
                narration_text = node_payload.get("narration_text", "")
                if narration_text:
                    yield CaseEditorStreamEvent(
                        event_type="narration",
                        payload={"text": str(narration_text)},
                    )


def _extract_edit_result(payload: dict[str, Any]) -> CaseEditResult:
    raw = payload.get("edit_result")
    if isinstance(raw, CaseEditResult):
        return raw
    return CaseEditResult.model_validate(raw)


def _event_id_for_edit_result(edit_result: CaseEditResult) -> str:
    if edit_result.action.value == "full_regenerate":
        return "full_case"
    if edit_result.card_type is None:
        return "case_edit"
    if edit_result.card_type.value == "case_metadata":
        return "case_metadata"
    return edit_result.card_id or edit_result.card_type.value
