from __future__ import annotations

from datetime import datetime

from .state import TrialState
from .types import NodeTelemetry, RunMetadata, RunTrialResponse, TranscriptTurn

TRIAL_NODE_SEQUENCE = [
    "plan_prosecution_strategy",
    "plan_defense_strategy",
    "opening_prosecution",
    "opening_defense",
    "summarize_trial_transcript",
    "closing_prosecution",
    "closing_defense",
    "verdict",
]

WITNESS_NODE_SEQUENCE = [
    "ask_question",
    "objection_check",
    "judge_ruling",
    "witness_answer",
]

ATTORNEY_SPEAKERS = {"prosecution", "defense"}

SCENE_PHASE_RANKS = {
    "opening": 0,
    "direct": 1,
    "cross": 1,
    "objection": 1,
    "ruling": 1,
    "closing": 2,
    "verdict": 3,
}

TRIAL_NODE_ORDER_RANKS = {
    "plan_prosecution_strategy": 0,
    "plan_defense_strategy": 0,
    "opening_prosecution": 1,
    "opening_defense": 2,
    "summarize_trial_transcript": 3,
    "closing_prosecution": 4,
    "closing_defense": 5,
    "verdict": 6,
}


class DeterministicValidationError(ValueError):
    """Raised when a trial run violates deterministic response invariants."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        self.generated_output: RunTrialResponse | None = None
        self.node_telemetry: list[NodeTelemetry] = []
        super().__init__("Deterministic validation failed: " + "; ".join(errors))


def _parse_iso8601(value: str, field_name: str, errors: list[str]) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        errors.append(f"{field_name} must be a valid ISO-8601 timestamp")
        return None


def _validate_transcript_structure(
    state: TrialState,
    errors: list[str],
) -> None:
    transcript = state.full_trial_transcript
    if not transcript:
        errors.append("full_trial_transcript must not be empty")
        return

    witness_ids = {witness.witness_id for witness in state.case_file.witnesses}
    valid_speakers = {"prosecution", "defense", "judge", *witness_ids}
    required_scenes = {"opening", "closing", "verdict"}
    seen_scenes: set[str] = set()
    witness_turn_without_question = False
    question_before_ruling: TranscriptTurn | None = None
    previous_turn: TranscriptTurn | None = None
    last_phase_rank = -1

    for index, turn in enumerate(transcript):
        if turn.speaker_id not in valid_speakers:
            errors.append(
                f"turn {index} uses invalid speaker_id '{turn.speaker_id}'"
            )

        seen_scenes.add(turn.scene)
        current_phase_rank = SCENE_PHASE_RANKS[turn.scene]
        if current_phase_rank < last_phase_rank:
            errors.append(
                f"turn {index} scene '{turn.scene}' regresses from prior trial phase"
            )
        last_phase_rank = max(last_phase_rank, current_phase_rank)

        if turn.ruling is not None and turn.speaker_id != "judge":
            errors.append(f"turn {index} uses ruling on non-judge speaker")

        if turn.objection_type is not None and not (
            turn.speaker_id == "judge"
            or (turn.scene == "objection" and turn.speaker_id in ATTORNEY_SPEAKERS)
        ):
            errors.append(
                f"turn {index} uses objection_type outside an objection or ruling"
            )

        if turn.scene == "verdict" and turn.speaker_id != "judge":
            errors.append("verdict scene must be spoken by the judge")

        if turn.scene == "verdict" and index != len(transcript) - 1:
            errors.append(f"turn {index} verdict scene must be final")

        if turn.scene == "ruling" and turn.speaker_id != "judge":
            errors.append("ruling scene must be spoken by the judge")

        if turn.scene == "objection":
            if turn.speaker_id not in ATTORNEY_SPEAKERS:
                errors.append("objection scene must be spoken by an attorney")
            if (
                previous_turn is None
                or previous_turn.scene not in {"direct", "cross"}
                or previous_turn.speaker_id not in ATTORNEY_SPEAKERS
            ):
                errors.append(
                    f"turn {index} objection must follow an attorney question"
                )
            elif previous_turn.speaker_id == turn.speaker_id:
                errors.append(
                    f"turn {index} objection must be raised by opposing counsel"
                )
            else:
                question_before_ruling = previous_turn

        if turn.scene == "ruling":
            if previous_turn is not None and previous_turn.scene == "ruling":
                errors.append(f"turn {index} ruling cannot follow another ruling")
            if previous_turn is not None and previous_turn.scene == "objection":
                if question_before_ruling is None:
                    errors.append(
                        f"turn {index} ruling must follow an objection to an attorney question"
                    )
            elif (
                previous_turn is None
                or previous_turn.scene not in {"direct", "cross"}
                or previous_turn.speaker_id not in ATTORNEY_SPEAKERS
            ):
                errors.append(f"turn {index} ruling must follow an attorney question")
            else:
                question_before_ruling = previous_turn

        if turn.scene in {"direct", "cross"} and turn.speaker_id in witness_ids:
            prior_turn = transcript[index - 1] if index > 0 else None
            direct_answer = (
                prior_turn is not None
                and prior_turn.scene == turn.scene
                and prior_turn.speaker_id in ATTORNEY_SPEAKERS
            )
            answer_after_ruling = (
                prior_turn is not None
                and prior_turn.scene == "ruling"
                and prior_turn.ruling == "overruled"
                and question_before_ruling is not None
                and question_before_ruling.scene == turn.scene
                and question_before_ruling.speaker_id in ATTORNEY_SPEAKERS
            )
            if not direct_answer and not answer_after_ruling:
                witness_turn_without_question = True

        if turn.scene not in {"objection", "ruling"}:
            question_before_ruling = None

        previous_turn = turn

    missing_scenes = sorted(required_scenes - seen_scenes)
    if missing_scenes:
        errors.append(f"transcript missing required scenes: {', '.join(missing_scenes)}")

    if transcript[-1].scene != "verdict":
        errors.append("final transcript turn must be the verdict")

    if witness_turn_without_question:
        errors.append(
            "witness answers must follow an attorney question in the same examination phase"
        )


def _validate_node_telemetry(telemetry: list[NodeTelemetry], errors: list[str]) -> None:
    trial_positions: list[int] = []

    for index, record in enumerate(telemetry):
        started_at = _parse_iso8601(
            record.started_at, f"node_telemetry[{index}].started_at", errors
        )
        completed_at = _parse_iso8601(
            record.completed_at, f"node_telemetry[{index}].completed_at", errors
        )
        if (
            started_at is not None
            and completed_at is not None
            and completed_at < started_at
        ):
            errors.append(
                f"node_telemetry[{index}] completed before it started for '{record.node_name}'"
            )

        if record.duration_ms < 0:
            errors.append(
                f"node_telemetry[{index}] has negative duration for '{record.node_name}'"
            )

        if record.parse_success is False:
            errors.append(
                f"node_telemetry[{index}] reports parse failure for '{record.node_name}'"
            )

        if record.stage == "trial":
            if record.node_name not in TRIAL_NODE_SEQUENCE:
                errors.append(
                    f"node_telemetry[{index}] uses unknown trial node '{record.node_name}'"
                )
            else:
                trial_positions.append(TRIAL_NODE_ORDER_RANKS[record.node_name])
        elif record.node_name in WITNESS_NODE_SEQUENCE:
            if record.phase not in {"direct", "cross"}:
                errors.append(
                    f"node_telemetry[{index}] witness node '{record.node_name}' is missing a direct/cross phase"
                )
            if not record.witness_id:
                errors.append(
                    f"node_telemetry[{index}] witness node '{record.node_name}' is missing witness_id"
                )

    if trial_positions != sorted(trial_positions):
        errors.append("trial node telemetry is out of order")

    trial_node_names = {record.node_name for record in telemetry if record.stage == "trial"}
    required_trial_nodes = {
        "plan_prosecution_strategy",
        "plan_defense_strategy",
        "opening_prosecution",
        "opening_defense",
        "summarize_trial_transcript",
        "closing_prosecution",
        "closing_defense",
        "verdict",
    }
    missing_trial_nodes = sorted(required_trial_nodes - trial_node_names)
    if missing_trial_nodes:
        errors.append(
            "missing required trial telemetry nodes: " + ", ".join(missing_trial_nodes)
        )


def _validate_response_contract(
    state: TrialState,
    run_metadata: RunMetadata,
    errors: list[str],
) -> None:
    if not run_metadata.run_id:
        errors.append("run.run_id must not be empty")
    if run_metadata.case_id != state.case_file.case_id:
        errors.append("run.case_id must match the request case_id")
    if not run_metadata.graph_version:
        errors.append("run.graph_version must not be empty")
    if not run_metadata.prompt_version:
        errors.append("run.prompt_version must not be empty")
    if not run_metadata.model_name:
        errors.append("run.model_name must not be empty")
    if not run_metadata.judge_model_name:
        errors.append("run.judge_model_name must not be empty")
    if not run_metadata.environment:
        errors.append("run.environment must not be empty")

    started_at = _parse_iso8601(run_metadata.started_at, "run.started_at", errors)
    completed_at = _parse_iso8601(run_metadata.completed_at, "run.completed_at", errors)
    if started_at is not None and completed_at is not None:
        expected_duration_ms = int((completed_at - started_at).total_seconds() * 1000)
        if expected_duration_ms < 0:
            errors.append("run.completed_at must not be earlier than run.started_at")
        elif run_metadata.duration_ms != expected_duration_ms:
            errors.append("run.duration_ms must match the timestamp delta")


def validate_trial_run(state: TrialState, run_metadata: RunMetadata) -> None:
    """Validate transcript, runtime telemetry, and public response invariants."""

    errors: list[str] = []
    _validate_transcript_structure(state, errors)
    _validate_node_telemetry(state.node_telemetry, errors)
    _validate_response_contract(state, run_metadata, errors)

    if errors:
        raise DeterministicValidationError(errors)
