from __future__ import annotations

from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel, Field, model_validator

from .models import CaseFile, CaseJurisdiction, DisputedFact, Evidence, Parties, WitnessProfile


class CardType(str, Enum):
    case_metadata = "case_metadata"
    witness = "witness"
    evidence = "evidence"
    disputed_fact = "disputed_fact"


class EditAction(str, Enum):
    full_regenerate = "full_regenerate"
    edit_card = "edit_card"
    add_card = "add_card"
    delete_card = "delete_card"


class CaseMetadata(BaseModel):
    case_title: str
    charge_or_claim: str
    parties: Parties
    jurisdiction: CaseJurisdiction


class SelectedCard(BaseModel):
    card_type: CardType
    card_id: str | None = None

    @model_validator(mode="after")
    def validate_card_id(self) -> "SelectedCard":
        if self.card_type == CardType.case_metadata and self.card_id is not None:
            raise ValueError("case_metadata does not accept a card_id")
        if self.card_type != CardType.case_metadata and not self.card_id:
            raise ValueError("Selected non-metadata cards require a card_id")
        return self


CardContent = CaseFile | CaseMetadata | WitnessProfile | Evidence | DisputedFact
ModelT = TypeVar("ModelT", bound=BaseModel)


class CaseEditOperation(BaseModel):
    action: EditAction
    card_type: CardType | None = None
    card_id: str | None = None
    updated_content: CardContent | None = None

    @model_validator(mode="after")
    def validate_operation(self) -> "CaseEditOperation":
        if self.action == EditAction.full_regenerate:
            if self.card_type is not None or self.card_id is not None:
                raise ValueError("full_regenerate cannot target a card")
            if not isinstance(self.updated_content, CaseFile):
                raise ValueError("full_regenerate requires updated_content as CaseFile")
            return self

        if self.card_type is None:
            raise ValueError("Scoped operations require card_type")
        if self.action == EditAction.delete_card:
            if self.card_type == CardType.case_metadata:
                raise ValueError("case_metadata cannot be deleted")
            if not self.card_id:
                raise ValueError("delete_card requires card_id")
            if self.updated_content is not None:
                raise ValueError("delete_card must not include updated_content")
            return self

        if self.card_type == CardType.case_metadata:
            if self.card_id is not None:
                raise ValueError("case_metadata does not accept card_id")
            if not isinstance(self.updated_content, CaseMetadata):
                raise ValueError("case_metadata updates require CaseMetadata content")
        elif self.card_type == CardType.witness:
            if not isinstance(self.updated_content, WitnessProfile):
                raise ValueError("witness updates require WitnessProfile content")
        elif self.card_type == CardType.evidence:
            if not isinstance(self.updated_content, Evidence):
                raise ValueError("evidence updates require Evidence content")
        elif self.card_type == CardType.disputed_fact:
            if not isinstance(self.updated_content, DisputedFact):
                raise ValueError("disputed_fact updates require DisputedFact content")

        if self.action == EditAction.edit_card and self.card_type != CardType.case_metadata:
            if not self.card_id:
                raise ValueError("edit_card requires card_id")
        return self


class CaseEditResult(CaseEditOperation):
    narration_hint: str = Field(
        description="1-2 sentence internal note on what changed, feeds the narrate node"
    )


def case_metadata_from_case_file(case_file: CaseFile) -> CaseMetadata:
    return CaseMetadata(
        case_title=case_file.case_title,
        charge_or_claim=case_file.charge_or_claim,
        parties=case_file.parties,
        jurisdiction=case_file.jurisdiction,
    )


def apply_case_edit_result(case_file: CaseFile, result: CaseEditOperation) -> CaseFile:
    if result.action == EditAction.full_regenerate:
        assert isinstance(result.updated_content, CaseFile)
        return result.updated_content

    if result.action == EditAction.delete_card:
        return _delete_card(
            case_file=case_file,
            card_type=result.card_type,
            card_id=result.card_id,
        )

    if result.action == EditAction.edit_card:
        return _edit_card(
            case_file=case_file,
            card_type=result.card_type,
            card_id=result.card_id,
            content=result.updated_content,
        )

    return _add_card(
        case_file=case_file,
        card_type=result.card_type,
        content=result.updated_content,
    )


def manual_operation_from_payload(
    *,
    case_file: CaseFile,
    action: EditAction,
    card_type: CardType,
    card_id: str | None,
    content: dict[str, Any] | None,
) -> CaseEditOperation:
    if action == EditAction.full_regenerate:
        raise ValueError("Manual mutations do not support full_regenerate")

    if action == EditAction.delete_card:
        return CaseEditOperation(action=action, card_type=card_type, card_id=card_id)

    updated_content = _validate_manual_content(
        case_file=case_file,
        action=action,
        card_type=card_type,
        card_id=card_id,
        content=content,
    )
    return CaseEditOperation(
        action=action,
        card_type=card_type,
        card_id=_card_id_for_content(card_type, updated_content),
        updated_content=updated_content,
    )


def _validate_manual_content(
    *,
    case_file: CaseFile,
    action: EditAction,
    card_type: CardType,
    card_id: str | None,
    content: dict[str, Any] | None,
) -> CardContent:
    if content is None:
        raise ValueError("content is required for add_card and edit_card")

    if card_type == CardType.case_metadata:
        if action == EditAction.add_card:
            raise ValueError("case_metadata cannot be added")
        merged = {
            **case_metadata_from_case_file(case_file).model_dump(mode="python"),
            **content,
        }
        return CaseMetadata.model_validate(merged)

    model_type, existing = _model_and_existing(
        case_file=case_file,
        card_type=card_type,
        card_id=card_id,
        action=action,
    )
    merged = dict(content)
    if existing is not None:
        merged = {**existing.model_dump(mode="python"), **merged}
    if action == EditAction.add_card:
        id_field = _id_field_name(card_type)
        merged.setdefault(id_field, _next_card_id(case_file, card_type))
    return model_type.model_validate(merged)


def _model_and_existing(
    *,
    case_file: CaseFile,
    card_type: CardType,
    card_id: str | None,
    action: EditAction,
) -> tuple[type[WitnessProfile] | type[Evidence] | type[DisputedFact], BaseModel | None]:
    if card_type == CardType.witness:
        return WitnessProfile, (
            _find_by_id(case_file.witnesses, "witness_id", card_id)
            if action == EditAction.edit_card
            else None
        )
    if card_type == CardType.evidence:
        return Evidence, (
            _find_by_id(case_file.evidence, "evidence_id", card_id)
            if action == EditAction.edit_card
            else None
        )
    return DisputedFact, (
        _find_by_id(case_file.disputed_facts, "fact_id", card_id)
        if action == EditAction.edit_card
        else None
    )


def _edit_card(
    *,
    case_file: CaseFile,
    card_type: CardType | None,
    card_id: str | None,
    content: CardContent | None,
) -> CaseFile:
    if card_type == CardType.case_metadata:
        assert isinstance(content, CaseMetadata)
        return case_file.model_copy(
            update={
                "case_title": content.case_title,
                "charge_or_claim": content.charge_or_claim,
                "parties": content.parties,
                "jurisdiction": content.jurisdiction,
            }
        )

    if card_type == CardType.witness:
        assert isinstance(content, WitnessProfile)
        return case_file.model_copy(
            update={
                "witnesses": _replace_by_id(
                    case_file.witnesses, "witness_id", card_id, content
                )
            }
        )
    if card_type == CardType.evidence:
        assert isinstance(content, Evidence)
        return case_file.model_copy(
            update={
                "evidence": _replace_by_id(
                    case_file.evidence, "evidence_id", card_id, content
                )
            }
        )

    assert isinstance(content, DisputedFact)
    return case_file.model_copy(
        update={
            "disputed_facts": _replace_by_id(
                case_file.disputed_facts, "fact_id", card_id, content
            )
        }
    )


def _add_card(
    *,
    case_file: CaseFile,
    card_type: CardType | None,
    content: CardContent | None,
) -> CaseFile:
    if card_type == CardType.case_metadata:
        raise ValueError("case_metadata cannot be added")
    if card_type == CardType.witness:
        assert isinstance(content, WitnessProfile)
        if not content.witness_id:
            content = content.model_copy(
                update={"witness_id": _next_card_id(case_file, card_type)}
            )
        return case_file.model_copy(update={"witnesses": [*case_file.witnesses, content]})
    if card_type == CardType.evidence:
        assert isinstance(content, Evidence)
        if not content.evidence_id:
            content = content.model_copy(
                update={"evidence_id": _next_card_id(case_file, card_type)}
            )
        return case_file.model_copy(update={"evidence": [*case_file.evidence, content]})

    assert isinstance(content, DisputedFact)
    if not content.fact_id:
        content = content.model_copy(update={"fact_id": _next_card_id(case_file, card_type)})
    return case_file.model_copy(
        update={"disputed_facts": [*case_file.disputed_facts, content]}
    )


def _delete_card(
    *,
    case_file: CaseFile,
    card_type: CardType | None,
    card_id: str | None,
) -> CaseFile:
    if card_type == CardType.case_metadata:
        raise ValueError("case_metadata cannot be deleted")
    if card_type == CardType.witness:
        filtered = [
            witness for witness in case_file.witnesses if witness.witness_id != card_id
        ]
        _assert_deleted(len(filtered), len(case_file.witnesses), card_id)
        return case_file.model_copy(
            update={
                "witnesses": [
                    witness.model_copy(
                        update={
                            "contradicts": None
                            if witness.contradicts == card_id
                            else witness.contradicts
                        }
                    )
                    for witness in filtered
                ]
            }
        )
    if card_type == CardType.evidence:
        filtered = [
            evidence for evidence in case_file.evidence if evidence.evidence_id != card_id
        ]
        _assert_deleted(len(filtered), len(case_file.evidence), card_id)
        return case_file.model_copy(update={"evidence": filtered})

    filtered = [fact for fact in case_file.disputed_facts if fact.fact_id != card_id]
    _assert_deleted(len(filtered), len(case_file.disputed_facts), card_id)
    return case_file.model_copy(update={"disputed_facts": filtered})


def _replace_by_id(
    items: list[ModelT], field_name: str, expected_id: str | None, replacement: ModelT
) -> list[ModelT]:
    for index, item in enumerate(items):
        if getattr(item, field_name) == expected_id:
            updated = list(items)
            updated[index] = replacement
            return updated
    raise ValueError(f"Card with id {expected_id!r} was not found")


def _find_by_id(
    items: list[ModelT], field_name: str, card_id: str | None
) -> ModelT:
    for item in items:
        if getattr(item, field_name) == card_id:
            return item
    raise ValueError(f"Card with id {card_id!r} was not found")


def _assert_deleted(new_count: int, previous_count: int, card_id: str | None) -> None:
    if new_count == previous_count:
        raise ValueError(f"Card with id {card_id!r} was not found")


def _next_card_id(case_file: CaseFile, card_type: CardType) -> str:
    prefix, items, field_name = {
        CardType.witness: ("W", case_file.witnesses, "witness_id"),
        CardType.evidence: ("E", case_file.evidence, "evidence_id"),
        CardType.disputed_fact: ("F", case_file.disputed_facts, "fact_id"),
    }[card_type]
    next_index = 1
    for item in items:
        value = getattr(item, field_name)
        if isinstance(value, str) and value.startswith(prefix):
            try:
                next_index = max(next_index, int(value.removeprefix(prefix)) + 1)
            except ValueError:
                continue
    return f"{prefix}{next_index}"


def _id_field_name(card_type: CardType) -> str:
    if card_type == CardType.witness:
        return "witness_id"
    if card_type == CardType.evidence:
        return "evidence_id"
    if card_type == CardType.disputed_fact:
        return "fact_id"
    raise ValueError(f"Unsupported card type {card_type}")


def _card_id_for_content(card_type: CardType, content: CardContent) -> str | None:
    if card_type == CardType.case_metadata:
        return None
    return getattr(content, _id_field_name(card_type))
