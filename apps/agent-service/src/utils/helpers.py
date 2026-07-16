from __future__ import annotations

import logging
from typing import Iterable, Literal

from .config import TRIAL_CONFIG
from .types import CaseFile, TranscriptTurn, WitnessProfile

logger = logging.getLogger(__name__)

AttorneySide = Literal["prosecution", "defense"]


def render_case_context(case_file: CaseFile) -> str:
    evidence_lines = "\n".join(
        f"- {evidence.evidence_id}: {evidence.description}"
        for evidence in case_file.evidence
    )
    facts_lines = "\n".join(f"- {fact}" for fact in case_file.disputed_facts)
    jurisdiction = case_file.jurisdiction
    jurisdiction_line = (
        f"{jurisdiction.country}, {jurisdiction.state}, "
        f"{jurisdiction.court}, {jurisdiction.trial_type} trial"
    )
    return f"""CASE FILE
Case ID: {case_file.case_id}
Case type: {case_file.case_type}
Jurisdiction: {jurisdiction_line}
Charge/Claim: {case_file.charge_or_claim}
Parties: {case_file.parties}

Disputed facts:
{facts_lines}

Evidence on record:
{evidence_lines}"""


def spoken_style_rules(max_sentences: int, role_hint: str) -> str:
    return (
        "This output will be used directly in the frontend/TTS transcript. "
        f"Write it as spoken dialogue for {role_hint}. "
        f"Keep it to at most {max_sentences} short sentences. "
        "Every sentence must include at least one inline delivery tag in square "
        "brackets, "
        "such as [steady], [firm], [measured], [tense], [frustrated], [quiet], "
        "or [somber]. "
        "Use realistic emotional delivery, not exaggerated stage directions. "
        "Do not describe actions outside the dialogue."
    )


def render_witness_public(witness: WitnessProfile) -> str:
    return (
        f"- {witness.witness_id} ({witness.name}, called by {witness.called_by}): "
        f"{witness.persona}"
    )


def render_witness_private(witness: WitnessProfile) -> str:
    return (
        f"{render_witness_public(witness)}\n"
        f"  Known facts (only you/your side sees this): {witness.knowledge_scope}"
    )


def preview_text(text: str | None, limit: int = 220) -> str:
    if not text:
        return "-"
    collapsed = " ".join(text.split())
    return collapsed if len(collapsed) <= limit else collapsed[: limit - 3] + "..."


def format_recent_transcript(
    turns: list[TranscriptTurn],
    max_turns: int = TRIAL_CONFIG.context_window_turns,
    scenes: set[str] | None = None,
    include_scene: bool = False,
) -> str:
    relevant_turns = (
        [turn for turn in turns if turn.scene in scenes]
        if scenes is not None
        else turns
    )
    recent_turns = relevant_turns[-max_turns:]
    return "\n".join(
        (
            f"[{turn.scene}] {turn.speaker_id}: {preview_text(turn.text)}"
            if include_scene
            else f"{turn.speaker_id}: {preview_text(turn.text)}"
        )
        for turn in recent_turns
    )


def get_witness_by_id(case_file: CaseFile, witness_id: str) -> WitnessProfile:
    for witness in case_file.witnesses:
        if witness.witness_id == witness_id:
            return witness
    raise ValueError(f"Unknown witness_id: {witness_id}")


def get_witnesses_by_side(
    case_file: CaseFile, side: AttorneySide
) -> list[WitnessProfile]:
    return [witness for witness in case_file.witnesses if witness.called_by == side]


def build_witness_queue(
    prosecution_witness_ids: Iterable[str], defense_witness_ids: Iterable[str]
) -> list[str]:
    return [*prosecution_witness_ids, *defense_witness_ids]


def log_graph_event(message: str, **context: object) -> None:
    if not logger.isEnabledFor(logging.DEBUG):
        return

    details = " | ".join(f"{key}={value}" for key, value in context.items())
    logger.debug("%s%s", message, f" | {details}" if details else "")
