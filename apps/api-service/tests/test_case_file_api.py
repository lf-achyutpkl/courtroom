from __future__ import annotations

import unittest
from datetime import datetime, timezone
from uuid import UUID, uuid4

from courtroom_domain import CaseFile
from fastapi.testclient import TestClient

from api_service.main import create_app
from api_service.repository import StoredCaseFile


class InMemoryCaseFileRepository:
    def __init__(self) -> None:
        self.records: dict[UUID, StoredCaseFile] = {}

    def create(self, case_file: CaseFile) -> StoredCaseFile:
        record = StoredCaseFile(
            id=uuid4(),
            case_file=case_file,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        self.records[record.id] = record
        return record

    def get(self, case_file_id: UUID) -> StoredCaseFile | None:
        return self.records.get(case_file_id)


class CaseFileApiTest(unittest.TestCase):
    def test_create_case_file_stores_dummy_case_file_with_uuid_id(self) -> None:
        repository = InMemoryCaseFileRepository()
        client = TestClient(create_app(repository=repository))

        response = client.post("/case-files")

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        record_id = UUID(payload["id"])
        case_file = payload["case_file"]
        UUID(case_file["case_id"])
        self.assertEqual(case_file["case_type"], "criminal")
        self.assertEqual(case_file["charge_or_claim"], "Grand theft auto")
        self.assertIn(record_id, repository.records)

    def test_create_case_file_uses_new_uuid_each_time(self) -> None:
        repository = InMemoryCaseFileRepository()
        client = TestClient(create_app(repository=repository))

        first = client.post("/case-files").json()["id"]
        second = client.post("/case-files").json()["id"]

        self.assertNotEqual(first, second)

    def test_get_case_file_returns_stored_case_file(self) -> None:
        repository = InMemoryCaseFileRepository()
        client = TestClient(create_app(repository=repository))
        created = client.post("/case-files").json()

        response = client.get(f"/case-files/{created['id']}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), created)

    def test_get_case_file_returns_404_for_unknown_id(self) -> None:
        repository = InMemoryCaseFileRepository()
        client = TestClient(create_app(repository=repository))

        response = client.get("/case-files/00000000-0000-0000-0000-000000000000")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
