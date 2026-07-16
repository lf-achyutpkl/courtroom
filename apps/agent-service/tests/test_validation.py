import unittest
from typing import Literal, cast
from unittest.mock import patch

from courtroom_domain import CaseFile, NodeTelemetry, TranscriptTurn, TrialState

from src.service import run_trial
from src.utils.types import RunMetadata, RunTrialRequest
from src.utils.validation import DeterministicValidationError, validate_trial_run


def build_case_file() -> CaseFile:
    return CaseFile.model_validate(
        {
            "case_id": "case-1",
            "case_type": "criminal",
            "charge_or_claim": "Test charge",
            "jurisdiction": {
                "country": "US",
                "state": "California",
                "court": "Superior Court",
                "trial_type": "jury",
            },
            "parties": {
                "plaintiff_or_prosecution": "State",
                "defendant": "Defendant",
            },
            "ground_truth": "Ground truth",
            "disputed_facts": ["fact-1"],
            "evidence": [],
            "witnesses": [
                {
                    "witness_id": "W1",
                    "name": "Witness One",
                    "persona": "Finance expert",
                    "called_by": "prosecution",
                    "knowledge_scope": "Saw the ledger",
                },
                {
                    "witness_id": "W2",
                    "name": "Witness Two",
                    "persona": "Operations manager",
                    "called_by": "defense",
                    "knowledge_scope": "Reviewed the records",
                },
            ],
        }
    )


def build_trial_telemetry() -> list[NodeTelemetry]:
    base_times = [
        ("2026-01-01T00:00:00+00:00", "2026-01-01T00:00:01+00:00"),
        ("2026-01-01T00:00:01+00:00", "2026-01-01T00:00:02+00:00"),
        ("2026-01-01T00:00:02+00:00", "2026-01-01T00:00:03+00:00"),
        ("2026-01-01T00:00:03+00:00", "2026-01-01T00:00:04+00:00"),
        ("2026-01-01T00:00:04+00:00", "2026-01-01T00:00:05+00:00"),
        ("2026-01-01T00:00:05+00:00", "2026-01-01T00:00:06+00:00"),
        ("2026-01-01T00:00:06+00:00", "2026-01-01T00:00:07+00:00"),
        ("2026-01-01T00:00:07+00:00", "2026-01-01T00:00:08+00:00"),
    ]
    node_names = [
        "plan_prosecution_strategy",
        "plan_defense_strategy",
        "opening_prosecution",
        "opening_defense",
        "summarize_trial_transcript",
        "closing_prosecution",
        "closing_defense",
        "verdict",
    ]
    return [
        NodeTelemetry(
            node_name=node_name,
            stage="trial",
            phase="planning" if "plan_" in node_name else None,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=1000,
            parse_success=True,
            model_name="gpt-4o-mini",
        )
        for node_name, (started_at, completed_at) in zip(node_names, base_times)
    ]


def make_transcript(
    *items: tuple[str, str] | tuple[str, str, str],
) -> list[TranscriptTurn]:
    turns: list[TranscriptTurn] = []
    for item in items:
        scene, speaker_id = item[:2]
        ruling = item[2] if len(item) == 3 else None
        turns.append(
            TranscriptTurn(
                scene=cast(
                    Literal[
                        "opening",
                        "direct",
                        "cross",
                        "objection",
                        "closing",
                        "ruling",
                        "verdict",
                    ],
                    scene,
                ),
                speaker_id=speaker_id,
                text="Transcript turn.",
                ruling=cast(Literal["sustained", "overruled"] | None, ruling),
            )
        )
    return turns


def build_valid_state() -> TrialState:
    return TrialState(
        case_file=build_case_file(),
        run_id="run-123",
        run_started_at="2026-01-01T00:00:00+00:00",
        full_trial_transcript=make_transcript(
            ("opening", "prosecution"),
            ("opening", "defense"),
            ("closing", "prosecution"),
            ("closing", "defense"),
            ("verdict", "judge"),
        ),
        node_telemetry=build_trial_telemetry(),
    )


class DeterministicValidationTest(unittest.TestCase):
    def test_run_trial_returns_metadata_for_valid_state(self) -> None:
        state = build_valid_state()
        request = RunTrialRequest(case_file=state.case_file)

        with patch("src.service._trial_graph.invoke", return_value=state):
            response = run_trial(request)

        self.assertEqual(response.run.case_id, state.case_file.case_id)
        self.assertEqual(response.run.graph_version, "v1")
        self.assertEqual(response.run.prompt_version, "v1")
        self.assertTrue(response.run.deterministic_validation_passed)
        self.assertEqual(response.full_trial_transcript[-1].scene, "verdict")

    def test_validate_trial_run_rejects_witness_answer_without_question(self) -> None:
        state = build_valid_state().model_copy(
            update={
                "full_trial_transcript": make_transcript(
                    ("opening", "prosecution"),
                    ("direct", "W1"),
                    ("closing", "defense"),
                    ("verdict", "judge"),
                )
            }
        )

        with self.assertRaises(DeterministicValidationError) as context:
            validate_trial_run(
                state,
                run_metadata=run_trial_metadata(state),
            )

        self.assertIn(
            "witness answers must follow an attorney question",
            str(context.exception),
        )

    def test_validate_trial_run_accepts_direct_cross_for_multiple_witnesses(
        self,
    ) -> None:
        state = build_valid_state().model_copy(
            update={
                "full_trial_transcript": make_transcript(
                    ("opening", "prosecution"),
                    ("opening", "defense"),
                    ("direct", "prosecution"),
                    ("direct", "W1"),
                    ("cross", "defense"),
                    ("cross", "W1"),
                    ("direct", "defense"),
                    ("direct", "W2"),
                    ("cross", "prosecution"),
                    ("cross", "W2"),
                    ("closing", "prosecution"),
                    ("closing", "defense"),
                    ("verdict", "judge"),
                )
            }
        )

        validate_trial_run(state, run_metadata=run_trial_metadata(state))

    def test_validate_trial_run_accepts_answer_after_overruled_ruling(self) -> None:
        state = build_valid_state().model_copy(
            update={
                "full_trial_transcript": make_transcript(
                    ("opening", "prosecution"),
                    ("direct", "prosecution"),
                    ("ruling", "judge", "overruled"),
                    ("direct", "W1"),
                    ("closing", "prosecution"),
                    ("verdict", "judge"),
                )
            }
        )

        validate_trial_run(state, run_metadata=run_trial_metadata(state))

    def test_validate_trial_run_accepts_objection_before_overruled_ruling(
        self,
    ) -> None:
        state = build_valid_state().model_copy(
            update={
                "full_trial_transcript": [
                    *make_transcript(
                        ("opening", "prosecution"),
                        ("direct", "prosecution"),
                    ),
                    TranscriptTurn(
                        scene="objection",
                        speaker_id="defense",
                        text="Objection, relevance.",
                        objection_type="relevance",
                    ),
                    *make_transcript(
                        ("ruling", "judge", "overruled"),
                        ("direct", "W1"),
                        ("closing", "prosecution"),
                        ("verdict", "judge"),
                    ),
                ]
            }
        )

        validate_trial_run(state, run_metadata=run_trial_metadata(state))

    def test_validate_trial_run_rejects_same_side_objection(self) -> None:
        state = build_valid_state().model_copy(
            update={
                "full_trial_transcript": [
                    *make_transcript(
                        ("opening", "prosecution"),
                        ("direct", "prosecution"),
                    ),
                    TranscriptTurn(
                        scene="objection",
                        speaker_id="prosecution",
                        text="Objection, relevance.",
                        objection_type="relevance",
                    ),
                    *make_transcript(
                        ("ruling", "judge", "sustained"),
                        ("closing", "prosecution"),
                        ("verdict", "judge"),
                    ),
                ]
            }
        )

        with self.assertRaises(DeterministicValidationError) as context:
            validate_trial_run(state, run_metadata=run_trial_metadata(state))

        self.assertIn(
            "objection must be raised by opposing counsel", str(context.exception)
        )

    def test_validate_trial_run_rejects_answer_after_sustained_ruling(self) -> None:
        state = build_valid_state().model_copy(
            update={
                "full_trial_transcript": make_transcript(
                    ("opening", "prosecution"),
                    ("direct", "prosecution"),
                    ("ruling", "judge", "sustained"),
                    ("direct", "W1"),
                    ("closing", "prosecution"),
                    ("verdict", "judge"),
                )
            }
        )

        with self.assertRaises(DeterministicValidationError) as context:
            validate_trial_run(state, run_metadata=run_trial_metadata(state))

        self.assertIn(
            "witness answers must follow an attorney question",
            str(context.exception),
        )

    def test_validate_trial_run_rejects_ruling_after_closing(self) -> None:
        state = build_valid_state().model_copy(
            update={
                "full_trial_transcript": make_transcript(
                    ("opening", "prosecution"),
                    ("closing", "prosecution"),
                    ("ruling", "judge", "sustained"),
                    ("verdict", "judge"),
                )
            }
        )

        with self.assertRaises(DeterministicValidationError) as context:
            validate_trial_run(state, run_metadata=run_trial_metadata(state))

        self.assertIn(
            "scene 'ruling' regresses from prior trial phase", str(context.exception)
        )

    def test_validate_trial_run_rejects_consecutive_rulings(self) -> None:
        state = build_valid_state().model_copy(
            update={
                "full_trial_transcript": make_transcript(
                    ("opening", "prosecution"),
                    ("direct", "prosecution"),
                    ("ruling", "judge", "sustained"),
                    ("ruling", "judge", "overruled"),
                    ("closing", "prosecution"),
                    ("verdict", "judge"),
                )
            }
        )

        with self.assertRaises(DeterministicValidationError) as context:
            validate_trial_run(state, run_metadata=run_trial_metadata(state))

        self.assertIn("ruling cannot follow another ruling", str(context.exception))

    def test_validate_trial_run_accepts_parallel_strategy_telemetry_order(self) -> None:
        telemetry = build_trial_telemetry()
        state = build_valid_state().model_copy(
            update={"node_telemetry": [telemetry[1], telemetry[0], *telemetry[2:]]}
        )

        validate_trial_run(state, run_metadata=run_trial_metadata(state))

    def test_run_trial_rejects_invalid_verdict_contract(self) -> None:
        invalid_state = build_valid_state().model_copy(
            update={
                "full_trial_transcript": make_transcript(
                    ("opening", "prosecution"),
                    ("opening", "defense"),
                    ("closing", "prosecution"),
                    ("closing", "defense"),
                    ("verdict", "defense"),
                )
            }
        )
        request = RunTrialRequest(case_file=invalid_state.case_file)

        with patch("src.service._trial_graph.invoke", return_value=invalid_state):
            with self.assertRaises(DeterministicValidationError) as context:
                run_trial(request)

        self.assertIn(
            "verdict scene must be spoken by the judge", str(context.exception)
        )
        generated_output = context.exception.generated_output
        if generated_output is None:
            raise AssertionError("expected generated output on validation failure")
        self.assertEqual(
            generated_output.run.case_id,
            invalid_state.case_file.case_id,
        )
        self.assertFalse(generated_output.run.deterministic_validation_passed)


def run_trial_metadata(state: TrialState) -> RunMetadata:
    return RunMetadata(
        run_id=state.run_id or "run-123",
        case_id=state.case_file.case_id,
        graph_version="v1",
        prompt_version="v1",
        model_name="gpt-4o-mini",
        judge_model_name="gpt-4o-mini",
        environment="test",
        deterministic_validation_passed=False,
        started_at="2026-01-01T00:00:00+00:00",
        completed_at="2026-01-01T00:00:08+00:00",
        duration_ms=8000,
    )


if __name__ == "__main__":
    unittest.main()
