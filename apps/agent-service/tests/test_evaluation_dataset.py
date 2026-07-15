import unittest

from src.evaluation.dataset import (
    DEFAULT_DATASET_VERSION,
    CoverageTag,
    EvaluationCase,
    load_dataset,
)


class EvaluationDatasetTest(unittest.TestCase):
    def test_seeded_cases_validate_against_schema(self) -> None:
        dataset = load_dataset()

        self.assertEqual(dataset.dataset_version, DEFAULT_DATASET_VERSION)
        for case in dataset.active_cases:
            self.assertIsInstance(case, EvaluationCase)
            self.assertTrue(case.eval_case_id)
            self.assertTrue(case.case_file.case_id)
            self.assertTrue(case.reference.expected_phases)
            self.assertIsNotNone(case.expected_signals)

    def test_default_dataset_has_three_active_cases(self) -> None:
        dataset = load_dataset()

        self.assertEqual(len(dataset.active_cases), 3)

    def test_seeded_cases_cover_required_categories(self) -> None:
        dataset = load_dataset()
        required_tags = set(CoverageTag.__args__)
        actual_tags = {
            tag
            for case in dataset.active_cases
            for tag in case.tags
            if tag in required_tags
        }

        self.assertEqual(actual_tags, required_tags)


if __name__ == "__main__":
    unittest.main()
