import unittest

from src.evaluation.dataset import load_dataset
from src.evaluation.evaluators import evaluate_rule_reference
from src.utils.types import RunMetadata, RunTrialResponse, TranscriptTurn


def response_for(turns, deterministic_valid=True):
    return RunTrialResponse(
        full_trial_transcript=turns,
        run=RunMetadata(
            run_id="run-1",
            case_id="case-ledger-theft",
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


class RuleReferenceEvaluatorTest(unittest.TestCase):
    def setUp(self) -> None:
        dataset = load_dataset()
        self.normal_case = dataset.active_cases[0]
        self.contradiction_case = dataset.active_cases[1]

    def test_passing_transcript(self) -> None:
        response = response_for(
            [
                TranscriptTurn(scene="opening", speaker_id="prosecution", text="Opening."),
                TranscriptTurn(
                    scene="direct",
                    speaker_id="W-auditor",
                    text="The ledger shows after-hours payments.",
                    cited_chunk_ids=["E-ledger-01"],
                ),
                TranscriptTurn(
                    scene="cross",
                    speaker_id="defense",
                    text="The badge access timing is disputed.",
                    cited_chunk_ids=["E-badge-02"],
                ),
                TranscriptTurn(scene="closing", speaker_id="defense", text="Closing."),
                TranscriptTurn(
                    scene="verdict",
                    speaker_id="judge",
                    text="The verdict relies on after-hours payments and badge access.",
                    cited_chunk_ids=["E-ledger-01", "E-badge-02"],
                ),
            ]
        )

        results = evaluate_rule_reference(response=response, case=self.normal_case)

        self.assertTrue(all(result.passed for result in results))

    def test_unknown_evidence_reference_fails(self) -> None:
        response = response_for(
            [
                TranscriptTurn(
                    scene="verdict",
                    speaker_id="judge",
                    text="Verdict.",
                    cited_chunk_ids=["E-missing"],
                )
            ]
        )

        results = evaluate_rule_reference(response=response, case=self.normal_case)
        evidence_result = next(
            result for result in results if result.evaluator_name == "evidence_reference"
        )

        self.assertFalse(evidence_result.passed)
        self.assertIn("E-missing", evidence_result.related_evidence_ids)

    def test_verdict_missing_required_support_fails(self) -> None:
        response = response_for(
            [
                TranscriptTurn(scene="opening", speaker_id="prosecution", text="Opening."),
                TranscriptTurn(scene="closing", speaker_id="defense", text="Closing."),
                TranscriptTurn(
                    scene="verdict",
                    speaker_id="judge",
                    text="The verdict does not discuss the reference facts.",
                ),
            ]
        )

        results = evaluate_rule_reference(response=response, case=self.normal_case)
        verdict_result = next(
            result for result in results if result.evaluator_name == "verdict_support"
        )

        self.assertFalse(verdict_result.passed)
        self.assertTrue(verdict_result.related_evidence_ids)

    def test_unresolved_contradiction_probe_fails(self) -> None:
        response = response_for(
            [
                TranscriptTurn(
                    scene="direct",
                    speaker_id="W-operator",
                    text="The alarm passed inspection.",
                ),
                TranscriptTurn(
                    scene="verdict",
                    speaker_id="judge",
                    text="Verdict relies on the testimony.",
                ),
            ]
        )

        results = evaluate_rule_reference(
            response=response, case=self.contradiction_case
        )
        contradiction_result = next(
            result
            for result in results
            if result.evaluator_name == "contradiction_probe"
        )

        self.assertFalse(contradiction_result.passed)

    def test_unsupported_claim_fails(self) -> None:
        response = response_for(
            [
                TranscriptTurn(
                    scene="verdict",
                    speaker_id="judge",
                    text="The operator was intoxicated.",
                )
            ]
        )

        results = evaluate_rule_reference(
            response=response, case=self.contradiction_case
        )
        claim_result = next(
            result for result in results if result.evaluator_name == "unsupported_claim"
        )

        self.assertFalse(claim_result.passed)

    def test_missing_phase_fails(self) -> None:
        response = response_for(
            [TranscriptTurn(scene="verdict", speaker_id="judge", text="Verdict.")]
        )

        results = evaluate_rule_reference(response=response, case=self.normal_case)
        phase_result = next(
            result for result in results if result.evaluator_name == "phase_coverage"
        )

        self.assertFalse(phase_result.passed)

    def test_evaluators_skip_deterministic_invalid_runs(self) -> None:
        response = response_for(
            [TranscriptTurn(scene="verdict", speaker_id="judge", text="Verdict.")],
            deterministic_valid=False,
        )

        self.assertEqual(
            evaluate_rule_reference(response=response, case=self.normal_case), []
        )


if __name__ == "__main__":
    unittest.main()
