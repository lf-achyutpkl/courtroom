from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from typing import cast
from unittest.mock import patch
from uuid import UUID, uuid4

from courtroom_domain import CaseEditOperation, CaseFile, apply_case_edit_result
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api_service.api.deps import (
    get_case_file_message_repository,
    get_case_file_repository,
)
from api_service.main import create_app
from api_service.repositories.case_file_messages import StoredCaseFileMessage
from api_service.repositories.case_files import (
    CaseFileNotFoundError,
    CaseFileRevisionConflictError,
    StoredCaseFile,
    _normalize_case_file_payload,
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

    def list(self) -> list[StoredCaseFile]:
        return sorted(
            self.records.values(),
            key=lambda record: (record.updated_at, record.created_at),
            reverse=True,
        )

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


class InMemoryCaseFileMessageRepository:
    def __init__(self) -> None:
        self.records: list[StoredCaseFileMessage] = []

    def list_for_case_file(self, case_file_id: UUID) -> list[StoredCaseFileMessage]:
        return [
            record for record in self.records if record.case_file_id == case_file_id
        ]

    def create(
        self,
        *,
        case_file_id: UUID,
        role: str,
        content: str,
    ) -> StoredCaseFileMessage:
        created_at = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(
            seconds=len(self.records)
        )
        record = StoredCaseFileMessage(
            id=uuid4(),
            case_file_id=case_file_id,
            role=role,  # type: ignore[arg-type]
            content=content,
            created_at=created_at,
        )
        self.records.append(record)
        return record


def build_client(
    repository: InMemoryCaseFileRepository,
    message_repository: InMemoryCaseFileMessageRepository | None = None,
) -> TestClient:
    app: FastAPI = create_app()
    app.dependency_overrides[get_case_file_repository] = lambda: repository
    app.dependency_overrides[get_case_file_message_repository] = lambda: (
        message_repository or InMemoryCaseFileMessageRepository()
    )
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
    def test_normalize_case_file_payload_repairs_legacy_draft_shape(self) -> None:
        case_json = {
            "case_id": "540f88e7-7138-4f9d-8e9b-2a0c4a7150d2",
            "case_type": "criminal",
            "charge_or_claim": "Grand theft auto",
            "parties": {
                "plaintiff_or_prosecution": "People of the State of California",
                "defendant": "Jordan Vale",
            },
            "ground_truth": "Ground truth",
            "disputed_facts": [
                "Whether Jordan Vale intended to deprive the owner of the vehicle.",
                (
                    "Whether the repair lot gave Jordan Vale permission to move "
                    "the vehicle."
                ),
            ],
            "evidence": [],
            "witnesses": [],
        }
        record = type(
            "Record",
            (),
            {
                "case_id": "540f88e7-7138-4f9d-8e9b-2a0c4a7150d2",
                "case_title": "People v. Vale",
                "case_type": "criminal",
                "charge_or_claim": "Grand theft auto",
                "plaintiff_or_prosecution": "People of the State of California",
                "defendant": "Jordan Vale",
                "case_json": case_json,
            },
        )()

        normalized = _normalize_case_file_payload(cast(object, record))

        self.assertEqual(normalized["case_title"], "People v. Vale")
        self.assertEqual(normalized["disputed_facts"][0]["fact_id"], "F1")
        self.assertEqual(
            normalized["disputed_facts"][0]["text"],
            "Whether Jordan Vale intended to deprive the owner of the vehicle.",
        )

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
        self.assertEqual(case_file["case_title"], "People v. Vale")
        self.assertEqual(case_file["charge_or_claim"], "Grand theft auto")
        self.assertEqual(
            case_file["parties"]["plaintiff_or_prosecution"],
            "People of the State of California",
        )
        self.assertEqual(case_file["parties"]["defendant"], "Jordan Vale")
        self.assertEqual(
            case_file["ground_truth"],
            "Jordan Vale took a vehicle from a repair lot without permission.",
        )
        self.assertEqual(len(case_file["witnesses"]), 1)
        self.assertEqual(case_file["witnesses"][0]["witness_id"], "W1")
        self.assertEqual(len(case_file["evidence"]), 1)
        self.assertEqual(case_file["evidence"][0]["evidence_id"], "E1")
        self.assertEqual(case_file["disputed_facts"][0]["fact_id"], "F1")
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

    def test_list_case_files_returns_dashboard_records(self) -> None:
        repository = InMemoryCaseFileRepository()
        first = repository.create(build_case_file(case_title="Matter One"))
        second = repository.create(build_case_file(case_title="Matter Two"))
        client = build_client(repository)

        response = client.get("/case-files")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            [item["id"] for item in payload],
            [str(first.id), str(second.id)],
        )

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

    def test_mutation_endpoint_rejects_locked_case_file(self) -> None:
        repository = InMemoryCaseFileRepository()
        record = repository.create(build_case_file(), status="simulation_started")
        client = build_client(repository)

        response = client.post(
            f"/case-files/{record.id}/mutations",
            json={
                "action": "edit_card",
                "card_type": "case_metadata",
                "card_id": None,
                "content": {"case_title": "Locked"},
                "expected_revision": 1,
            },
        )

        self.assertEqual(response.status_code, 409)

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

    def test_mutation_endpoint_deletes_witness_and_cleans_contradiction_links(
        self,
    ) -> None:
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

    def test_get_messages_returns_persisted_transcript(self) -> None:
        repository = InMemoryCaseFileRepository()
        message_repository = InMemoryCaseFileMessageRepository()
        record = repository.create(build_case_file())
        message_repository.create(
            case_file_id=record.id,
            role="human",
            content="Draft the witness list.",
        )
        message_repository.create(
            case_file_id=record.id,
            role="ai",
            content="I added a first-pass witness list.",
        )
        client = build_client(repository, message_repository)

        response = client.get(f"/case-files/{record.id}/messages")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()[0]["content"],
            "Draft the witness list.",
        )
        self.assertEqual(response.json()[1]["role"], "ai")

    def test_message_endpoint_rejects_locked_case_file(self) -> None:
        repository = InMemoryCaseFileRepository()
        record = repository.create(build_case_file(), status="simulation_started")
        client = build_client(repository)

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

        self.assertEqual(response.status_code, 409)

    def test_message_endpoint_streams_sse_protocol(self) -> None:
        repository = InMemoryCaseFileRepository()
        message_repository = InMemoryCaseFileMessageRepository()
        record = repository.create(build_case_file())
        client = build_client(repository, message_repository)

        with (
            patch(
                "api_service.api.routers.case_files.get_database_url",
                return_value="postgresql://example",
            ),
            patch(
                "api_service.api.routers.case_files.iter_case_editor_stream_chunks",
                return_value=iter(
                    [
                        type(
                            "Chunk",
                            (),
                            {
                                "kind": "start",
                                "data": {"type": "start", "messageId": "m1"},
                            },
                        )(),
                        type(
                            "Chunk",
                            (),
                            {
                                "kind": "text-delta",
                                "data": {
                                    "type": "text-delta",
                                    "id": "t1",
                                    "delta": "Sharper ",
                                },
                            },
                        )(),
                        type(
                            "Chunk",
                            (),
                            {
                                "kind": "text-delta",
                                "data": {
                                    "type": "text-delta",
                                    "id": "t1",
                                    "delta": "title",
                                },
                            },
                        )(),
                        type(
                            "Chunk",
                            (),
                            {
                                "kind": "data-case-file-update",
                                "data": {
                                    "type": "data-case-file-update",
                                    "id": "case_metadata",
                                    "data": {"action": "edit_card"},
                                },
                            },
                        )(),
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
        self.assertIn('"type": "data-case-file-update"', response.text)
        self.assertEqual(len(message_repository.records), 2)
        self.assertEqual(message_repository.records[0].role, "human")
        self.assertEqual(
            message_repository.records[0].content,
            "make the title sharper",
        )
        self.assertEqual(message_repository.records[1].role, "ai")
        self.assertEqual(message_repository.records[1].content, "Sharper title")


if __name__ == "__main__":
    unittest.main()
