import unittest

from src.evaluation.promptfoo_suite import (
    REQUIRED_ADVERSARIAL_CATEGORIES,
    promptfoo_categories,
    validate_promptfoo_categories,
)


class PromptfooSuiteTest(unittest.TestCase):
    def test_suite_contains_required_adversarial_categories(self) -> None:
        validate_promptfoo_categories()

        self.assertEqual(promptfoo_categories(), REQUIRED_ADVERSARIAL_CATEGORIES)


if __name__ == "__main__":
    unittest.main()
