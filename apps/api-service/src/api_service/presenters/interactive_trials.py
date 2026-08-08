"""Public read-model projection for durable interactive trial runs."""

from __future__ import annotations

from ..repositories.interactive_trial_runs import (
    StoredInteractiveTrialRun,
    StoredParticipantTurn,
)
from ..schemas.interactive_trials import (
    InteractiveTrialRunResponse,
    PendingHumanTurnContextResponse,
    PendingHumanTurnResponse,
    PendingWitnessResponse,
)


def build_interactive_trial_response(
    run: StoredInteractiveTrialRun, turn: StoredParticipantTurn | None
) -> InteractiveTrialRunResponse:
    return InteractiveTrialRunResponse(
        interactive_trial_run_id=run.id,
        case_file_id=run.case_file_id,
        human_attorney_side=run.human_attorney_side,
        human_witness_plan=run.human_witness_plan,
        status=run.status,
        transcript=run.transcript_snapshot or [],
        live_transcript=_live_transcript(run),
        result=run.result_snapshot,
        pending_human_turn=(
            PendingHumanTurnResponse(
                turn_id=turn.id,
                scene=turn.scene,
                attorney_side=turn.attorney_side,
                context=_pending_turn_context(run, turn),
            )
            if turn and run.status == "awaiting_human"
            else None
        ),
        error_message=run.error_message,
        created_at=run.created_at,
        completed_at=run.completed_at,
    )


def _live_transcript(run: StoredInteractiveTrialRun) -> list[dict[str, object]]:
    finalized = list(run.transcript_snapshot or [])
    current = (run.state_snapshot or {}).get("current_witness_transcript")
    if not isinstance(current, list):
        return finalized
    seen = {_turn_key(turn) for turn in finalized}
    return finalized + [
        turn
        for turn in current
        if isinstance(turn, dict) and _turn_key(turn) not in seen
    ]


def _turn_key(turn: dict[str, object]) -> tuple[object, object, object, object, object]:
    return tuple(
        turn.get(key)
        for key in ("scene", "speaker_id", "text", "objection_type", "ruling")
    )


def _pending_turn_context(
    run: StoredInteractiveTrialRun, turn: StoredParticipantTurn
) -> PendingHumanTurnContextResponse:
    action = (
        turn.scene
        if turn.scene in {"opening", "closing", "question", "objection"}
        else "question"
    )
    snapshot = run.state_snapshot or {}
    phase = snapshot.get("examination_phase")
    witness = _snapshot_witness(snapshot)
    if action == "question" and witness:
        instruction = (
            f"Ask {witness.name} the next {phase or 'direct'} examination question."
        )
    elif action == "objection":
        instruction = (
            "Decide whether to record an objection to the preceding question, "
            "or continue without one."
        )
    else:
        instruction = f"Record your {action} statement for the court."
    return PendingHumanTurnContextResponse(
        action=action,
        attorney_side=turn.attorney_side,  # type: ignore[arg-type]
        instruction=instruction,
        examination_phase=phase if phase in {"direct", "cross"} else None,
        witness=witness if action in {"question", "objection"} else None,
    )


def _snapshot_witness(snapshot: dict[str, object]) -> PendingWitnessResponse | None:
    witness_id, case_file = (
        snapshot.get("current_witness_id"),
        snapshot.get("case_file"),
    )
    if not isinstance(witness_id, str) or not isinstance(case_file, dict):
        return None
    witnesses = case_file.get("witnesses")
    if not isinstance(witnesses, list):
        return None
    for witness in witnesses:
        if isinstance(witness, dict) and witness.get("witness_id") == witness_id:
            name, persona, called_by = (
                witness.get(key) for key in ("name", "persona", "called_by")
            )
            if all(isinstance(value, str) for value in (name, persona, called_by)):
                return PendingWitnessResponse(
                    witness_id=witness_id,
                    name=name,
                    persona=persona,
                    called_by=called_by,
                )
    return None
