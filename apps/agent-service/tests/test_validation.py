import unittest
from unittest.mock import patch

from src.service import run_trial
from src.utils.state import TrialState
from src.utils.types import CaseFile, NodeTelemetry, RunTrialRequest, TranscriptTurn
from src.utils.validation import DeterministicValidationError, validate_trial_run


def build_case_file() -> CaseFile:
    return CaseFile.model_validate(
        {
            "case_id": "case-1",
            "case_type": "criminal",
            "charge_or_claim": "Test charge",
            "jurisdiction": "US",
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
                }
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


def build_valid_state() -> TrialState:
    return TrialState(
        case_file=build_case_file(),
        run_id="run-123",
        run_started_at="2026-01-01T00:00:00+00:00",
        full_trial_transcript=[
            TranscriptTurn(
                scene="opening",
                speaker_id="prosecution",
                text="Opening for the prosecution.",
            ),
            TranscriptTurn(
                scene="opening",
                speaker_id="defense",
                text="Opening for the defense.",
            ),
            TranscriptTurn(
                scene="closing",
                speaker_id="prosecution",
                text="Closing for the prosecution.",
            ),
            TranscriptTurn(
                scene="closing",
                speaker_id="defense",
                text="Closing for the defense.",
            ),
            TranscriptTurn(
                scene="verdict",
                speaker_id="judge",
                text="The court finds the defendant guilty.",
            ),
        ],
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
                "full_trial_transcript": [
                    TranscriptTurn(
                        scene="opening",
                        speaker_id="prosecution",
                        text="Opening for the prosecution.",
                    ),
                    TranscriptTurn(
                        scene="direct",
                        speaker_id="W1",
                        text="I saw the ledger.",
                    ),
                    TranscriptTurn(
                        scene="closing",
                        speaker_id="defense",
                        text="Closing for the defense.",
                    ),
                    TranscriptTurn(
                        scene="verdict",
                        speaker_id="judge",
                        text="The court enters a verdict.",
                    ),
                ]
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

    def test_run_trial_rejects_invalid_verdict_contract(self) -> None:
        invalid_state = build_valid_state().model_copy(
            update={
                "full_trial_transcript": [
                    TranscriptTurn(
                        scene="opening",
                        speaker_id="prosecution",
                        text="Opening for the prosecution.",
                    ),
                    TranscriptTurn(
                        scene="opening",
                        speaker_id="defense",
                        text="Opening for the defense.",
                    ),
                    TranscriptTurn(
                        scene="closing",
                        speaker_id="prosecution",
                        text="Closing for the prosecution.",
                    ),
                    TranscriptTurn(
                        scene="closing",
                        speaker_id="defense",
                        text="Closing for the defense.",
                    ),
                    TranscriptTurn(
                        scene="verdict",
                        speaker_id="defense",
                        text="The defense announces the verdict.",
                    ),
                ]
            }
        )
        request = RunTrialRequest(case_file=invalid_state.case_file)

        with patch("src.service._trial_graph.invoke", return_value=invalid_state):
            with self.assertRaises(DeterministicValidationError) as context:
                run_trial(request)

        self.assertIn(
            "verdict scene must be spoken by the judge", str(context.exception)
        )


def run_trial_metadata(state: TrialState):
    from src.utils.types import RunMetadata

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
