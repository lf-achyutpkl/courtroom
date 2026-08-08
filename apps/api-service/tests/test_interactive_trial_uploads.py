import unittest

from api_service.api.routers.interactive_trials import normalize_audio_content_type
from api_service.schemas.interactive_trials import SubmitParticipantTurnRequest


class NormalizeAudioContentTypeTests(unittest.TestCase):
    def test_removes_browser_codec_parameters(self) -> None:
        self.assertEqual(
            normalize_audio_content_type("audio/webm;codecs=opus"),
            "audio/webm",
        )

    def test_normalizes_case_and_whitespace(self) -> None:
        self.assertEqual(
            normalize_audio_content_type(" Audio/MP4 ; codecs=mp4a.40.2 "),
            "audio/mp4",
        )


class SubmitParticipantTurnRequestTests(unittest.TestCase):
    def test_retains_final_question_control(self) -> None:
        request = SubmitParticipantTurnRequest(object=True, is_final=False)

        self.assertFalse(request.is_final)
