from __future__ import annotations

import json

from courtroom_domain import (
    CaseEditResult,
    CaseFile,
    SelectedCard,
    case_metadata_from_case_file,
)


def build_process_edit_system_prompt() -> str:
    return (
        "You are editing a structured courtroom case file.\n"
        "Return exactly one scoped edit result.\n"
        "Follow these rules strictly:\n"
        "- Use edit_card when a selected card or a clearly identified existing card is the target.\n"
        "- Use add_card when the request is asking for a new witness, evidence item, or disputed fact.\n"
        "- Use delete_card only when the user explicitly asks to remove a card.\n"
        "- Use full_regenerate only for broad whole-case requests.\n"
        "- Never change ground_truth during edit_card, add_card, or delete_card.\n"
        "- Align updated_content to the matching CaseFile sub-schema for the selected card type.\n"
        "- For scoped edits, updated_content must only contain the changed card payload, not the full case.\n"
        "- Preserve exact field types from the CaseFile schema even when returning only part of a card.\n"
        '- Do not put descriptive prose into enum fields. Use only literal enum values such as "prosecution" or "defense".\n'
        '- Evidence.submitted_by must be exactly "prosecution" or "defense".\n'
        '- Witness.called_by must be exactly "prosecution" or "defense".\n'
        "- For edit_card, omit unchanged fields instead of rewriting them with explanatory text.\n"
        "- Preserve witness information asymmetry. knowledge_scope must remain a plausible fragment.\n"
        "- Only add contradictions when the request clearly implies one.\n"
        "- Keep narration_hint to one or two plain sentences summarizing the change."
    )


def build_process_edit_user_prompt(
    *,
    case_file: CaseFile,
    selected_card: SelectedCard | None,
    user_message: str,
) -> str:
    selected_card_payload = (
        selected_card.model_dump(mode="json") if selected_card is not None else None
    )
    metadata = case_metadata_from_case_file(case_file).model_dump(mode="json")
    return (
        "Current case file JSON:\n"
        f"{json.dumps(case_file.model_dump(mode='json'), indent=2)}\n\n"
        "Current case metadata card JSON:\n"
        f"{json.dumps(metadata, indent=2)}\n\n"
        "Selected card:\n"
        f"{json.dumps(selected_card_payload, indent=2)}\n\n"
        "User request:\n"
        f"{user_message}\n\n"
        "Return a CaseEditResult-compatible edit decision.\n"
        "Important: updated_content must match the target card schema and enum fields must use exact literal values."
    )


def build_narration_system_prompt() -> str:
    return (
        "You are a concise collaborative case editor.\n"
        "Explain the committed case-file change in one to three sentences.\n"
        "Stay grounded in the actual edit result and prior chat tone.\n"
        "Do not mention internal validation, schemas, or IDs unless the user asked for them."
    )


def build_narration_user_prompt(
    *,
    edit_result: CaseEditResult,
    user_message: str,
) -> str:
    return (
        "Latest user request:\n"
        f"{user_message}\n\n"
        "Grounding edit result:\n"
        f"{json.dumps(edit_result.model_dump(mode='json'), indent=2)}\n\n"
        "Respond with a short natural-language explanation of what changed."
    )
