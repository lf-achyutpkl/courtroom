from __future__ import annotations

import unittest
from datetime import datetime, timezone
from uuid import uuid4

from api_service.presenters.interactive_trials import build_interactive_trial_response
from api_service.repositories.interactive_trial_runs import (
    StoredInteractiveTrialRun,
    StoredParticipantTurn,
)


class InteractiveTrialPresenterTests(unittest.TestCase):
    def test_live_transcript_uses_incrementally_published_witness_turn_once(
        self,
    ) -> None:
        run_id = uuid4()
        now = datetime.now(timezone.utc)
        question = {
            "scene": "direct",
            "speaker_id": "prosecution",
            "text": "What happened?",
        }
        pending_turn_id = uuid4()
        run = StoredInteractiveTrialRun(
        id=run_id,
        case_file_id=uuid4(),
        human_attorney_side="defense",
        human_witness_plan=["W1"],
        langgraph_thread_id="thread-1",
        status="awaiting_human",
        state_snapshot={
            "full_trial_transcript": [question],
            "current_witness_transcript": [question],
            "current_witness_id": "W1",
            "examination_phase": "direct",
            "case_file": {
                "witnesses": [
                    {
                        "witness_id": "W1",
                        "name": "Ms. Chen",
                        "persona": "Repair lot manager",
                        "called_by": "prosecution",
                    }
                ]
            },
        },
        transcript_snapshot=[question],
        result_snapshot=None,
        pending_turn_id=pending_turn_id,
        error_message=None,
        created_at=now,
        started_at=now,
        completed_at=None,
        )
        turn = StoredParticipantTurn(
        id=pending_turn_id,
        run_id=run_id,
        turn_number=1,
        scene="objection",
        attorney_side="defense",
        status="pending_upload",
        object_requested=None,
        is_final=None,
        object_bucket=None,
        object_key=None,
        content_type=None,
        size_bytes=None,
        checksum=None,
        submitted_at=None,
        resumed_at=None,
        )

        response = build_interactive_trial_response(run, turn)

        self.assertEqual(response.transcript, [question])
        self.assertEqual(response.live_transcript, [question])
        self.assertIsNotNone(response.pending_human_turn)
        assert response.pending_human_turn is not None
        self.assertEqual(response.pending_human_turn.context.action, "objection")
        self.assertIsNotNone(response.pending_human_turn.context.witness)
        assert response.pending_human_turn.context.witness is not None
        self.assertEqual(response.pending_human_turn.context.witness.name, "Ms. Chen")
