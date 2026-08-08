from __future__ import annotations

from unittest import TestCase
from unittest.mock import patch

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt
from test_main_graph_helpers import build_case_file

from src.interactive.state import InteractiveTrialState
from src.interactive.witness_graph import build_ai_human_witness_graph
from src.utils import types


class InteractiveWitnessGraphTest(TestCase):
    def test_question_then_objection_resume_uses_checkpointed_child_state(self) -> None:
        def ask_question(state: InteractiveTrialState) -> dict[str, object]:
            if state.examining_attorney == state.human_attorney_side:
                payload = interrupt({"kind": "human_question"})
                self.assertTrue(payload["is_final"])
                text = "Human direct question"
            else:
                text = "AI cross question"
            return {
                "current_witness_transcript": [
                    *state.current_witness_transcript,
                    types.TranscriptTurn(
                        scene=state.examination_phase,
                        speaker_id=state.examining_attorney,
                        text=text,
                    ),
                ],
                "attorney_is_done": True,
                "active_question_text": text,
            }

        def objection_check(state: InteractiveTrialState) -> dict[str, object]:
            opposing = (
                "defense"
                if state.examining_attorney == "prosecution"
                else "prosecution"
            )
            if opposing == state.human_attorney_side:
                payload = interrupt({"kind": "human_objection"})
                self.assertIs(payload["object"], False)
            return {"objection_pending": False}

        def witness_answer(state: InteractiveTrialState) -> dict[str, object]:
            return {
                "current_witness_transcript": [
                    *state.current_witness_transcript,
                    types.TranscriptTurn(
                        scene=state.examination_phase,
                        speaker_id=state.current_witness_id,
                        text="Witness answer",
                    ),
                ]
            }

        with (
            patch("src.interactive.witness_graph.ask_question_node", ask_question),
            patch(
                "src.interactive.witness_graph.objection_check_node", objection_check
            ),
            patch("src.interactive.witness_graph.witness_answer_node", witness_answer),
        ):
            graph = build_ai_human_witness_graph(
                checkpointer=InMemorySaver()
            ).with_config({"configurable": {"thread_id": "interactive-witness-test"}})
            initial_state = InteractiveTrialState(
                case_file=build_case_file(),
                trial_mode="ai_vs_human",
                human_attorney_side="prosecution",
                current_witness_id="W1",
            )

            first = graph.invoke(initial_state)
            self.assertEqual(first["__interrupt__"][0].value["kind"], "human_question")

            second = graph.invoke(
                Command(resume={"audio_base64": "test", "is_final": True})
            )
        self.assertEqual(
            second["__interrupt__"][0].value["kind"], "human_objection"
        )
        self.assertEqual(
            [turn.text for turn in second["full_trial_transcript"]],
            ["Human direct question", "Witness answer", "AI cross question"],
        )

        final = graph.invoke(Command(resume={"object": False}))
        self.assertNotIn("__interrupt__", final)
        self.assertEqual(
            [turn.text for turn in final["full_trial_transcript"]],
            [
                "Human direct question",
                "Witness answer",
                "AI cross question",
                "Witness answer",
            ],
        )
