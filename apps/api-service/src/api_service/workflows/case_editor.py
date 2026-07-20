from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable, Iterator, Protocol
from uuid import UUID

from courtroom_domain import SelectedCard

from ..repositories.case_files import CaseFileRepository


@dataclass(frozen=True)
class EditorStreamChunk:
    kind: str
    data: dict[str, object]


class SupportsEditorEvent(Protocol):
    event_type: str
    payload: dict[str, object]


def stream_case_editor_response(
    *,
    case_file_id: UUID,
    message: str,
    selected_card: SelectedCard | None,
    case_files: CaseFileRepository,
    database_url: str,
) -> Iterator[bytes]:
    message_id = f"case-file-{case_file_id}"
    text_id = f"text-{case_file_id}"

    for chunk in iter_case_editor_stream_chunks(
        case_file_id=case_file_id,
        message=message,
        selected_card=selected_card,
        case_files=case_files,
        database_url=database_url,
        message_id=message_id,
        text_id=text_id,
    ):
        yield _encode_sse(chunk.data)
    yield b"data: [DONE]\n\n"


def iter_case_editor_stream_chunks(
    *,
    case_file_id: UUID,
    message: str,
    selected_card: SelectedCard | None,
    case_files: CaseFileRepository,
    database_url: str,
    message_id: str | None = None,
    text_id: str | None = None,
) -> Iterator[EditorStreamChunk]:
    stream_case_edit, build_postgres_checkpointer = _load_agent_editor_contract()
    resolved_message_id = message_id or f"case-file-{case_file_id}"
    resolved_text_id = text_id or f"text-{case_file_id}"

    yield EditorStreamChunk(
        kind="start",
        data={"type": "start", "messageId": resolved_message_id},
    )
    yield EditorStreamChunk(
        kind="text-start",
        data={"type": "text-start", "id": resolved_text_id},
    )

    with build_postgres_checkpointer(database_url) as checkpointer:
        for event in stream_case_edit(
            case_file_id=case_file_id,
            user_message=message,
            selected_card=selected_card,
            case_files=case_files,
            checkpointer=checkpointer,
        ):
            if event.event_type == "edit_result":
                yield EditorStreamChunk(
                    kind="data-case-file-update",
                    data={
                        "type": "data-case-file-update",
                        "id": event.payload["id"],
                        "data": event.payload["edit_result"],
                    },
                )
            elif event.event_type == "narration":
                for delta in _split_text(str(event.payload["text"])):
                    yield EditorStreamChunk(
                        kind="text-delta",
                        data={
                            "type": "text-delta",
                            "id": resolved_text_id,
                            "delta": delta,
                        },
                    )

    yield EditorStreamChunk(
        kind="text-end",
        data={"type": "text-end", "id": resolved_text_id},
    )
    yield EditorStreamChunk(kind="finish", data={"type": "finish"})


def _split_text(text: str) -> list[str]:
    if not text:
        return []
    words = text.split(" ")
    deltas: list[str] = []
    for index, word in enumerate(words):
        suffix = "" if index == len(words) - 1 else " "
        deltas.append(f"{word}{suffix}")
    return deltas


def _encode_sse(payload: dict[str, object]) -> bytes:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")


@lru_cache(maxsize=1)
def _load_agent_editor_contract() -> tuple[Callable[..., Iterator[SupportsEditorEvent]], Callable[[str], object]]:
    try:
        service_module = importlib.import_module("src.case_editor.service")
    except ModuleNotFoundError as exc:
        agent_service_root = Path(__file__).resolve().parents[4] / "agent-service"
        if not agent_service_root.exists():
            raise RuntimeError(
                f"Agent service workspace not found at {agent_service_root}."
            ) from exc

        package_name = "_agent_service_runtime"
        package_root = agent_service_root / "src"
        package_init = package_root / "__init__.py"
        package = sys.modules.get(package_name)
        if package is None:
            spec = importlib.util.spec_from_file_location(
                package_name,
                package_init,
                submodule_search_locations=[str(package_root)],
            )
            if spec is None or spec.loader is None:
                raise RuntimeError(
                    f"Unable to load agent service package from {package_root}."
                ) from exc

            package = importlib.util.module_from_spec(spec)
            sys.modules[package_name] = package
            spec.loader.exec_module(package)

        service_module = importlib.import_module(f"{package_name}.case_editor.service")

    return service_module.stream_case_edit, service_module.build_postgres_checkpointer
