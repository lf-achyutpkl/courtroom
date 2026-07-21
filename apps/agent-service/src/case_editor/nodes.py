from __future__ import annotations

from typing import Literal, cast
from uuid import UUID

from courtroom_domain import (
    CardType,
    CaseEditResult,
    CaseFile,
    CaseJurisdiction,
    DisputedFact,
    EditAction,
    Evidence,
    Parties,
    SelectedCard,
    WitnessProfile,
)
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..utils.llm import fast_llm, invoke_structured
from .prompts import (
    build_narration_system_prompt,
    build_narration_user_prompt,
    build_process_edit_system_prompt,
    build_process_edit_user_prompt,
)
from .state import CaseEditorState, CaseFileStore


class _StrictPatchModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LlmCaseMetadataContent(_StrictPatchModel):
    case_title: str | None = None
    charge_or_claim: str | None = None
    parties: Parties | None = None
    jurisdiction: CaseJurisdiction | None = None

    @model_validator(mode="after")
    def validate_non_empty(self) -> "LlmCaseMetadataContent":
        if not any(value is not None for value in self.model_dump().values()):
            raise ValueError("case metadata edits must update at least one field")
        return self


class LlmWitnessContent(_StrictPatchModel):
    witness_id: str | None = None
    name: str | None = None
    persona: str | None = None
    called_by: Literal["prosecution", "defense"] | None = None
    knowledge_scope: str | None = None
    contradicts: str | None = None

    @model_validator(mode="after")
    def validate_non_empty(self) -> "LlmWitnessContent":
        if not any(value is not None for value in self.model_dump().values()):
            raise ValueError("witness edits must update at least one field")
        return self


class LlmEvidenceContent(_StrictPatchModel):
    evidence_id: str | None = None
    description: str | None = None
    submitted_by: Literal["prosecution", "defense"] | None = None

    @model_validator(mode="after")
    def validate_non_empty(self) -> "LlmEvidenceContent":
        if not any(value is not None for value in self.model_dump().values()):
            raise ValueError("evidence edits must update at least one field")
        return self


class LlmDisputedFactContent(_StrictPatchModel):
    fact_id: str | None = None
    text: str | None = None

    @model_validator(mode="after")
    def validate_non_empty(self) -> "LlmDisputedFactContent":
        if not any(value is not None for value in self.model_dump().values()):
            raise ValueError("disputed fact edits must update at least one field")
        return self


class LlmCaseEditResult(BaseModel):
    action: EditAction
    card_type: CardType | None = None
    card_id: str | None = None
    updated_content: (
        CaseFile
        | LlmCaseMetadataContent
        | LlmWitnessContent
        | LlmEvidenceContent
        | LlmDisputedFactContent
        | None
    ) = None
    narration_hint: str = Field(
        description="1-2 sentence internal note on what changed, feeds the narrate node"
    )

    @model_validator(mode="after")
    def validate_content_matches_scope(self) -> "LlmCaseEditResult":
        if self.action == EditAction.full_regenerate:
            if not isinstance(self.updated_content, CaseFile):
                raise ValueError(
                    "full_regenerate requires updated_content aligned to CaseFile"
                )
            return self

        if self.card_type is None:
            raise ValueError("scoped edits require card_type")

        if self.action == EditAction.delete_card:
            if self.updated_content is not None:
                raise ValueError("delete_card must not include updated_content")
            return self

        expected_type = {
            CardType.case_metadata: LlmCaseMetadataContent,
            CardType.witness: LlmWitnessContent,
            CardType.evidence: LlmEvidenceContent,
            CardType.disputed_fact: LlmDisputedFactContent,
        }[self.card_type]
        if not isinstance(self.updated_content, expected_type):
            raise ValueError(
                f"{self.card_type.value} edits require updated_content aligned to "
                f"{expected_type.__name__}"
            )

        if self.action == EditAction.add_card:
            _validate_required_add_fields(
                self.card_type,
                cast(
                    LlmCaseMetadataContent
                    | LlmWitnessContent
                    | LlmEvidenceContent
                    | LlmDisputedFactContent,
                    self.updated_content,
                ),
            )

        return self


def make_process_edit_node(case_files: CaseFileStore):
    def process_edit_node(state: CaseEditorState) -> dict[str, object]:
        stored = case_files.get(UUID(state.case_file_id))
        if stored is None:
            raise ValueError(f"Case file {state.case_file_id} was not found")
        case_file = CaseFile.model_validate(stored.case_file)
        selected_card = _selected_card_from_state(state)
        llm_result = _invoke_process_edit(
            case_file=case_file,
            selected_card=selected_card,
            user_message=state.user_message,
        )
        edit_result = _coerce_case_edit_result(
            llm_result=llm_result,
            case_file=case_file,
        )
        if edit_result.action == EditAction.full_regenerate:
            case_files.replace_case_file(
                UUID(state.case_file_id),
                edit_result.updated_content,
                expected_revision=stored.revision,
            )
        else:
            case_files.apply_operation(
                UUID(state.case_file_id),
                edit_result,
                expected_revision=stored.revision,
            )
        return {"edit_result": edit_result}

    return process_edit_node


def _selected_card_from_state(state: CaseEditorState) -> SelectedCard | None:
    if state.selected_card_type is None:
        return None
    return SelectedCard(
        card_type=CardType(state.selected_card_type),
        card_id=state.selected_card_id,
    )


def narrate_node(state: CaseEditorState) -> dict[str, object]:
    if state.edit_result is None:
        raise ValueError("edit_result is required before narrate")
    history = list(state.messages[:-1]) if state.messages else []
    response = fast_llm.invoke(
        [
            *history,
            SystemMessage(content=build_narration_system_prompt()),
            HumanMessage(
                content=build_narration_user_prompt(
                    edit_result=state.edit_result,
                    user_message=state.user_message,
                )
            ),
        ]
    )
    narration_text = getattr(response, "content", "")
    if not isinstance(narration_text, str):
        narration_text = str(narration_text)
    return {
        "narration_text": narration_text,
        "messages": [AIMessage(content=narration_text)],
    }


def _invoke_process_edit(
    *,
    case_file: CaseFile,
    selected_card: SelectedCard | None,
    user_message: str,
) -> LlmCaseEditResult:
    system_prompt = build_process_edit_system_prompt()
    user_prompt = build_process_edit_user_prompt(
        case_file=case_file,
        selected_card=selected_card,
        user_message=user_message,
    )
    errors: list[Exception] = []
    for _ in range(2):
        try:
            return invoke_structured(
                system_prompt,
                user_prompt,
                LlmCaseEditResult,
                node_name="case_editor_process_edit",
            )
        except Exception as exc:  # noqa: PERF203
            errors.append(exc)
    raise errors[-1]


def _coerce_case_edit_result(
    *,
    llm_result: LlmCaseEditResult,
    case_file: CaseFile,
) -> CaseEditResult:
    payload = llm_result.model_dump(mode="python")
    if llm_result.action == EditAction.full_regenerate:
        payload["updated_content"] = CaseFile.model_validate(llm_result.updated_content)
        return CaseEditResult.model_validate(payload)

    if llm_result.action == EditAction.delete_card:
        payload["updated_content"] = None
        return CaseEditResult.model_validate(payload)

    if llm_result.card_type == CardType.case_metadata:
        if not isinstance(llm_result.updated_content, LlmCaseMetadataContent):
            raise ValueError("case metadata edits require typed metadata content")
        merged = {
            "case_title": case_file.case_title,
            "charge_or_claim": case_file.charge_or_claim,
            "parties": case_file.parties.model_dump(mode="python"),
            "jurisdiction": case_file.jurisdiction.model_dump(mode="python"),
            **llm_result.updated_content.model_dump(mode="python", exclude_none=True),
        }
        payload["updated_content"] = merged
        return CaseEditResult.model_validate(payload)

    if llm_result.card_type == CardType.witness:
        if not isinstance(llm_result.updated_content, LlmWitnessContent):
            raise ValueError("witness edits require typed witness content")
        updated_content = llm_result.updated_content.model_dump(
            mode="python",
            exclude_none=True,
        )
        updated_content.setdefault(
            "witness_id",
            llm_result.card_id or _next_witness_id(case_file),
        )
        payload["updated_content"] = WitnessProfile.model_validate(updated_content)
        payload["card_id"] = updated_content["witness_id"]
        return CaseEditResult.model_validate(payload)
    if llm_result.card_type == CardType.evidence:
        if not isinstance(llm_result.updated_content, LlmEvidenceContent):
            raise ValueError("evidence edits require typed evidence content")
        updated_content = llm_result.updated_content.model_dump(
            mode="python",
            exclude_none=True,
        )
        updated_content.setdefault(
            "evidence_id",
            llm_result.card_id or _next_evidence_id(case_file),
        )
        payload["updated_content"] = Evidence.model_validate(updated_content)
        payload["card_id"] = updated_content["evidence_id"]
        return CaseEditResult.model_validate(payload)

    if not isinstance(llm_result.updated_content, LlmDisputedFactContent):
        raise ValueError("disputed fact edits require typed fact content")
    updated_content = llm_result.updated_content.model_dump(
        mode="python",
        exclude_none=True,
    )
    updated_content.setdefault(
        "fact_id", llm_result.card_id or _next_fact_id(case_file)
    )
    payload["updated_content"] = DisputedFact.model_validate(updated_content)
    payload["card_id"] = updated_content["fact_id"]
    return CaseEditResult.model_validate(payload)


def _next_witness_id(case_file: CaseFile) -> str:
    return _next_id([witness.witness_id for witness in case_file.witnesses], "W")


def _next_evidence_id(case_file: CaseFile) -> str:
    return _next_id([evidence.evidence_id for evidence in case_file.evidence], "E")


def _next_fact_id(case_file: CaseFile) -> str:
    return _next_id([fact.fact_id for fact in case_file.disputed_facts], "F")


def _next_id(existing_ids: list[str], prefix: str) -> str:
    next_index = 1
    for value in existing_ids:
        if value.startswith(prefix):
            try:
                next_index = max(next_index, int(value.removeprefix(prefix)) + 1)
            except ValueError:
                continue
    return f"{prefix}{next_index}"


def _validate_required_add_fields(
    card_type: CardType,
    content: LlmCaseMetadataContent
    | LlmWitnessContent
    | LlmEvidenceContent
    | LlmDisputedFactContent,
) -> None:
    required_fields = {
        CardType.witness: ("name", "persona", "called_by", "knowledge_scope"),
        CardType.evidence: ("description", "submitted_by"),
        CardType.disputed_fact: ("text",),
    }.get(card_type)
    if required_fields is None:
        raise ValueError(f"{card_type.value} cannot be added")

    missing_fields = [
        field_name
        for field_name in required_fields
        if getattr(content, field_name, None) in (None, "")
    ]
    if missing_fields:
        joined = ", ".join(missing_fields)
        raise ValueError(f"add_card for {card_type.value} requires fields: {joined}")
