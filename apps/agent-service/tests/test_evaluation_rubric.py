import unittest

from courtroom_domain import TranscriptTurn

from src.evaluation.dataset import load_dataset
from src.evaluation.evaluators import EvaluatorResult
from src.evaluation.rubric import (
    DEFAULT_JUDGE_MODEL,
    RUBRIC_PROMPT_VERSION,
    RubricDimension,
    RubricEvaluatorConfig,
    RubricScore,
    TokenUsage,
    evaluate_rubric,
)
from src.utils.types import RunMetadata, RunTrialResponse


def response_for(deterministic_valid=True):
    return RunTrialResponse(
        full_trial_transcript=[
            TranscriptTurn(scene="opening", speaker_id="prosecution", text="Opening."),
            TranscriptTurn(
                scene="verdict",
                speaker_id="judge",
                text="Verdict cites the audit log.",
                cited_chunk_ids=["E-audit-01"],
            ),
        ],
        run=RunMetadata(
            run_id="run-1",
            case_id="case-1",
            graph_version="v1",
            prompt_version="v1",
            model_name="gpt-4o-mini",
            judge_model_name="gpt-4o-mini",
            environment="test",
            deterministic_validation_passed=deterministic_valid,
            started_at="2026-01-01T00:00:00+00:00",
            completed_at="2026-01-01T00:00:01+00:00",
            duration_ms=1000,
        ),
    )


def score(dimension: RubricDimension, value: float) -> RubricScore:
    return RubricScore(
        dimension=dimension,
        score=value,
        threshold=0.0,
        passed=True,
        rationale=f"{dimension} rationale",
        cited_turn_ids=[1],
    )


def passing_judge(rubric_input):
    return {
        "scores": [
            score("legal_grounding", 0.95),
            score("procedural_realism", 0.91),
            score("role_adherence", 0.92),
            score("contradiction_handling", 0.93),
            score("verdict_support", 0.94),
            score("unsafe_content_handling", 0.99),
        ],
        "rationale": f"Used {rubric_input.judge_model}",
        "token_usage": TokenUsage(
            prompt_tokens=100, completion_tokens=20, total_tokens=120
        ),
    }


class RubricEvaluatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.reference = load_dataset().active_cases[0].reference

    def test_valid_score_parsing_and_default_model(self) -> None:
        results = evaluate_rubric(
            response=response_for(), reference=self.reference, judge=passing_judge
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].evaluator_model, DEFAULT_JUDGE_MODEL)
        self.assertEqual(results[0].evaluator_prompt_version, RUBRIC_PROMPT_VERSION)
        self.assertTrue(results[0].passed)
        token_usage = results[0].token_usage
        if token_usage is None:
            raise AssertionError("expected rubric token usage to be present")
        self.assertEqual(token_usage.total_tokens, 120)

    def test_threshold_failure(self) -> None:
        def failing_judge(_rubric_input):
            payload = passing_judge(_rubric_input)
            payload["scores"][0] = score("legal_grounding", 0.1)
            return payload

        results = evaluate_rubric(
            response=response_for(), reference=self.reference, judge=failing_judge
        )

        self.assertFalse(results[0].passed)
        self.assertFalse(results[0].scores[0].passed)

    def test_rejects_partial_score_dimensions(self) -> None:
        def partial_judge(_rubric_input):
            payload = passing_judge(_rubric_input)
            payload["scores"] = payload["scores"][:-1]
            return payload

        with self.assertRaisesRegex(ValueError, "missing: unsafe_content_handling"):
            evaluate_rubric(
                response=response_for(), reference=self.reference, judge=partial_judge
            )

    def test_metadata_capture_and_dependency_injection(self) -> None:
        seen_inputs = []

        def injected_judge(rubric_input):
            seen_inputs.append(rubric_input)
            return passing_judge(rubric_input)

        config = RubricEvaluatorConfig(judge_model="custom-judge")
        results = evaluate_rubric(
            response=response_for(),
            reference=self.reference,
            judge=injected_judge,
            config=config,
        )

        self.assertEqual(seen_inputs[0].judge_model, "custom-judge")
        self.assertEqual(results[0].evaluator_model, "custom-judge")
        self.assertGreaterEqual(results[0].latency_ms, 0)
        self.assertEqual(results[0].cited_turn_ids, [1])

    def test_prerequisite_gating(self) -> None:
        blocked = EvaluatorResult(
            evaluator_name="evidence_reference",
            passed=False,
            severity="high",
            summary="Blocked",
        )

        self.assertEqual(
            evaluate_rubric(
                response=response_for(),
                reference=self.reference,
                judge=passing_judge,
                prerequisite_results=[blocked],
            ),
            [],
        )

    def test_deterministic_invalid_gating(self) -> None:
        self.assertEqual(
            evaluate_rubric(
                response=response_for(deterministic_valid=False),
                reference=self.reference,
                judge=passing_judge,
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
