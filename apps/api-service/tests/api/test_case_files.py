from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import UUID, uuid4

from courtroom_domain import CaseEditOperation, CaseFile, apply_case_edit_result
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api_service.api.deps import get_case_file_repository
from api_service.main import create_app
from api_service.repositories.case_files import (
    CaseFileNotFoundError,
    CaseFileRevisionConflictError,
    StoredCaseFile,
)


class InMemoryCaseFileRepository:
    def __init__(self) -> None:
        self.records: dict[UUID, StoredCaseFile] = {}

    def create(self, case_file: CaseFile, *, status: str = "draft") -> StoredCaseFile:
        timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
        record = StoredCaseFile(
            id=uuid4(),
            case_file=case_file,
            status=status,
            revision=1,
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.records[record.id] = record
        return record

    def get(self, case_file_id: UUID) -> StoredCaseFile | None:
        return self.records.get(case_file_id)

    def apply_operation(
        self,
        case_file_id: UUID,
        operation: CaseEditOperation,
        *,
        expected_revision: int,
    ) -> StoredCaseFile:
        record = self.records.get(case_file_id)
        if record is None:
            raise CaseFileNotFoundError
        if record.revision != expected_revision:
            raise CaseFileRevisionConflictError(
                f"Expected revision {expected_revision}, found {record.revision}"
            )
        updated_at = record.updated_at + timedelta(seconds=1)
        updated = StoredCaseFile(
            id=record.id,
            case_file=apply_case_edit_result(record.case_file, operation),
            status=record.status,
            revision=record.revision + 1,
            created_at=record.created_at,
            updated_at=updated_at,
        )
        self.records[record.id] = updated
        return updated

    def replace_case_file(
        self,
        case_file_id: UUID,
        case_file: CaseFile,
        *,
        expected_revision: int,
        status: str | None = None,
    ) -> StoredCaseFile:
        record = self.records.get(case_file_id)
        if record is None:
            raise CaseFileNotFoundError
        if record.revision != expected_revision:
            raise CaseFileRevisionConflictError(
                f"Expected revision {expected_revision}, found {record.revision}"
            )
        updated = StoredCaseFile(
            id=record.id,
            case_file=case_file,
            status=status or record.status,
            revision=record.revision + 1,
            created_at=record.created_at,
            updated_at=record.updated_at + timedelta(seconds=1),
        )
        self.records[record.id] = updated
        return updated


def build_client(repository: InMemoryCaseFileRepository) -> TestClient:
    app: FastAPI = create_app()
    app.dependency_overrides[get_case_file_repository] = lambda: repository
    return TestClient(app)


def build_case_file(**overrides: object) -> CaseFile:
    payload = {
        "case_id": "case-123",
        "case_title": "People v. Vale",
        "case_type": "criminal",
        "charge_or_claim": "Grand theft auto",
        "parties": {
            "plaintiff_or_prosecution": "People of the State of California",
            "defendant": "Jordan Vale",
        },
        "ground_truth": "Ground truth",
        "disputed_facts": [{"fact_id": "F1", "text": "Fact one"}],
        "evidence": [],
        "witnesses": [],
    }
    payload.update(overrides)
    return CaseFile.model_validate(payload)


class CaseFileApiTest(unittest.TestCase):
    def test_create_case_file_stores_initial_draft_with_uuid_id(self) -> None:
        repository = InMemoryCaseFileRepository()
        client = build_client(repository)

        response = client.post("/case-files")

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        record_id = UUID(payload["id"])
        case_file = payload["case_file"]
        UUID(case_file["case_id"])
        self.assertEqual(case_file["case_type"], "criminal")
        self.assertEqual(case_file["case_title"], "Untitled matter")
        self.assertEqual(
            case_file["charge_or_claim"],
            "Describe the dispute to generate the case file.",
        )
        self.assertEqual(case_file["parties"]["plaintiff_or_prosecution"], "TBD")
        self.assertEqual(case_file["parties"]["defendant"], "TBD")
        self.assertEqual(case_file["ground_truth"], "Pending generation from the author's prompt.")
        self.assertEqual(case_file["witnesses"], [])
        self.assertEqual(case_file["evidence"], [])
        self.assertEqual(case_file["disputed_facts"], [])
        self.assertEqual(payload["revision"], 1)
        self.assertIn(record_id, repository.records)

    def test_create_case_file_uses_new_uuid_each_time(self) -> None:
        repository = InMemoryCaseFileRepository()
        client = build_client(repository)

        first = client.post("/case-files").json()["id"]
        second = client.post("/case-files").json()["id"]

        self.assertNotEqual(first, second)

    def test_get_case_file_returns_stored_case_file(self) -> None:
        repository = InMemoryCaseFileRepository()
        client = build_client(repository)
        created = client.post("/case-files").json()

        response = client.get(f"/case-files/{created['id']}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), created)

    def test_get_case_file_returns_404_for_unknown_id(self) -> None:
        repository = InMemoryCaseFileRepository()
        client = build_client(repository)

        response = client.get("/case-files/00000000-0000-0000-0000-000000000000")

        self.assertEqual(response.status_code, 404)

    def test_mutation_endpoint_edits_case_metadata_and_bumps_revision(self) -> None:
        repository = InMemoryCaseFileRepository()
        record = repository.create(build_case_file())
        client = build_client(repository)

        response = client.post(
            f"/case-files/{record.id}/mutations",
            json={
                "action": "edit_card",
                "card_type": "case_metadata",
                "card_id": None,
                "content": {"case_title": "State v. Caldwell"},
                "expected_revision": 1,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["revision"], 2)
        stored = repository.get(record.id)
        assert stored is not None
        self.assertEqual(stored.case_file.case_title, "State v. Caldwell")

    def test_mutation_endpoint_adds_witness_with_stable_generated_id(self) -> None:
        repository = InMemoryCaseFileRepository()
        record = repository.create(build_case_file())
        client = build_client(repository)

        response = client.post(
            f"/case-files/{record.id}/mutations",
            json={
                "action": "add_card",
                "card_type": "witness",
                "card_id": None,
                "content": {
                    "name": "Laura Bennett",
                    "persona": "Forensic accountant",
                    "called_by": "prosecution",
                    "knowledge_scope": "Reviewed selected ledger entries.",
                },
                "expected_revision": 1,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["operation"]["updated_content"]["witness_id"], "W1")
        stored = repository.get(record.id)
        assert stored is not None
        self.assertEqual(stored.case_file.witnesses[0].witness_id, "W1")

    def test_mutation_endpoint_deletes_witness_and_cleans_contradiction_links(self) -> None:
        repository = InMemoryCaseFileRepository()
        record = repository.create(
            build_case_file(
                witnesses=[
                    {
                        "witness_id": "W1",
                        "name": "Witness One",
                        "persona": "Analyst",
                        "called_by": "prosecution",
                        "knowledge_scope": "Observed records",
                    },
                    {
                        "witness_id": "W2",
                        "name": "Witness Two",
                        "persona": "Investigator",
                        "called_by": "defense",
                        "knowledge_scope": "Interviewed staff",
                        "contradicts": "W1",
                    },
                ]
            )
        )
        client = build_client(repository)

        response = client.post(
            f"/case-files/{record.id}/mutations",
            json={
                "action": "delete_card",
                "card_type": "witness",
                "card_id": "W1",
                "content": None,
                "expected_revision": 1,
            },
        )

        self.assertEqual(response.status_code, 200)
        stored = repository.get(record.id)
        assert stored is not None
        self.assertEqual([w.witness_id for w in stored.case_file.witnesses], ["W2"])
        self.assertIsNone(stored.case_file.witnesses[0].contradicts)

    def test_mutation_endpoint_returns_409_for_revision_mismatch(self) -> None:
        repository = InMemoryCaseFileRepository()
        record = repository.create(build_case_file())
        client = build_client(repository)

        response = client.post(
            f"/case-files/{record.id}/mutations",
            json={
                "action": "edit_card",
                "card_type": "case_metadata",
                "card_id": None,
                "content": {"case_title": "Late edit"},
                "expected_revision": 7,
            },
        )

        self.assertEqual(response.status_code, 409)

    def test_message_endpoint_streams_sse_protocol(self) -> None:
        repository = InMemoryCaseFileRepository()
        record = repository.create(build_case_file())
        client = build_client(repository)

        with (
            patch(
                "api_service.api.routers.case_files.get_database_url",
                return_value="postgresql://example",
            ),
            patch(
                "api_service.api.routers.case_files.stream_case_editor_response",
                return_value=iter(
                    [
                        b'data: {"type":"start","messageId":"m1"}\n\n',
                        b'data: {"type":"data-case-file-update","id":"case_metadata","data":{"action":"edit_card"}}\n\n',
                        b"data: [DONE]\n\n",
                    ]
                ),
            ),
        ):
            response = client.post(
                f"/case-files/{record.id}/messages",
                json={
                    "message": "make the title sharper",
                    "selected_card": {
                        "card_type": "case_metadata",
                        "card_id": None,
                    },
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["x-vercel-ai-ui-message-stream"],
            "v1",
        )
        self.assertIn('"type":"data-case-file-update"', response.text)


if __name__ == "__main__":
    unittest.main()
