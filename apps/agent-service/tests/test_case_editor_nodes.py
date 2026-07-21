import unittest
from typing import cast

from courtroom_domain import CaseFile, EditAction, Evidence
from pydantic import ValidationError

from src.case_editor.nodes import LlmCaseEditResult, _coerce_case_edit_result


def build_case_file() -> CaseFile:
    return CaseFile.model_validate(
        {
            "case_id": "case-1",
            "case_title": "State v. Defendant",
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
            "disputed_facts": [],
            "evidence": [],
            "witnesses": [],
        }
    )


class CaseEditorNodesTest(unittest.TestCase):
    def test_llm_case_edit_result_rejects_invalid_evidence_enum(self) -> None:
        with self.assertRaises(ValidationError):
            LlmCaseEditResult.model_validate(
                {
                    "action": EditAction.add_card,
                    "card_type": "evidence",
                    "updated_content": {
                        "description": (
                            "Bodycam still showing the suspect near the alley."
                        ),
                        "submitted_by": (
                            "Officer Maria Lee submitted this to the prosecution"
                        ),
                    },
                    "narration_hint": "Added one new evidence item.",
                }
            )

    def test_coerce_case_edit_result_adds_generated_evidence_id(self) -> None:
        llm_result = LlmCaseEditResult.model_validate(
            {
                "action": EditAction.add_card,
                "card_type": "evidence",
                "updated_content": {
                    "description": "Bodycam still showing the suspect near the alley.",
                    "submitted_by": "prosecution",
                },
                "narration_hint": "Added one new evidence item.",
            }
        )

        result = _coerce_case_edit_result(
            llm_result=llm_result,
            case_file=build_case_file(),
        )

        assert result.updated_content is not None
        assert result.card_type is not None
        updated_content = cast(Evidence, result.updated_content)
        self.assertEqual(result.card_type.value, "evidence")
        self.assertEqual(result.card_id, "E1")
        self.assertEqual(updated_content.evidence_id, "E1")
        self.assertEqual(updated_content.submitted_by, "prosecution")


if __name__ == "__main__":
    unittest.main()
