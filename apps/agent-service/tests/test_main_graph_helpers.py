import unittest

from src.utils.config import TRIAL_CONFIG
from src.utils.helpers import build_witness_queue, get_witness_by_id, get_witnesses_by_side
from src.utils.nodes import route_after_witness_selection, select_next_witness_node
from src.utils.state import TrialState
from src.utils.types import CaseFile


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
                },
                {
                    "witness_id": "W2",
                    "name": "Witness Two",
                    "persona": "Security expert",
                    "called_by": "defense",
                    "knowledge_scope": "Reviewed access logs",
                },
            ],
        }
    )


def build_state() -> TrialState:
    return TrialState.model_validate(
        {
            "case_file": build_case_file(),
            "prosecution_witness_plan": [],
            "defense_witness_plan": [],
            "examining_attorney": "prosecution",
            "attorney_is_done": False,
        }
    )


class MainGraphHelpersTest(unittest.TestCase):
    def test_runtime_config_defaults(self) -> None:
        self.assertEqual(TRIAL_CONFIG.max_questions_per_phase, 4)
        self.assertEqual(TRIAL_CONFIG.context_window_turns, 4)
        self.assertTrue(TRIAL_CONFIG.skip_direct_objections)

    def test_build_witness_queue_preserves_plan_order(self) -> None:
        self.assertEqual(build_witness_queue(["W1", "W3"], ["W2"]), ["W1", "W3", "W2"])

    def test_get_witness_helpers_filter_and_lookup(self) -> None:
        case_file = build_case_file()
        self.assertEqual(get_witness_by_id(case_file, "W2").name, "Witness Two")
        self.assertEqual(
            [witness.witness_id for witness in get_witnesses_by_side(case_file, "prosecution")],
            ["W1"],
        )

    def test_select_next_witness_resets_state_for_direct_exam(self) -> None:
        state = build_state().model_copy(
            update={
                "witness_queue": ["W2"],
                "current_witness_transcript": [],
                "turn_count": 3,
                "objection_pending": True,
                "last_objection_type": "hearsay",
                "active_question_text": "old question",
                "attorney_is_done": True,
            }
        )

        update = select_next_witness_node(state)

        self.assertEqual(update["current_witness_id"], "W2")
        self.assertEqual(update["witness_queue"], [])
        self.assertEqual(update["examination_phase"], "direct")
        self.assertEqual(update["examining_attorney"], "defense")
        self.assertFalse(update["objection_pending"])
        self.assertIsNone(update["active_question_text"])
        self.assertFalse(update["attorney_is_done"])

    def test_route_after_witness_selection(self) -> None:
        state = build_state()
        self.assertEqual(route_after_witness_selection(state), "summarize_trial_transcript")

        active_state = state.model_copy(update={"current_witness_id": "W1"})
        self.assertEqual(route_after_witness_selection(active_state), "examine_witness")


if __name__ == "__main__":
    unittest.main()
