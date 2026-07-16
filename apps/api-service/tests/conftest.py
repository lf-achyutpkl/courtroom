from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from courtroom_domain import CaseFile
from fastapi.testclient import TestClient

from api_service.main import create_app
from api_service.api.deps import (
    get_case_file_repository,
    get_simulation_queue,
    get_simulation_run_repository,
)
from api_service.repositories.case_files import StoredCaseFile
from api_service.repositories.simulation_runs import StoredSimulationRun


@pytest.fixture
def fixed_datetime() -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.fixture
def case_file_factory():
    def _build(case_file: CaseFile, created_at: datetime) -> StoredCaseFile:
        return StoredCaseFile(id=uuid4(), case_file=case_file, created_at=created_at)

    return _build


@pytest.fixture
def simulation_run_factory(fixed_datetime: datetime):
    def _build(case_file_id: UUID) -> StoredSimulationRun:
        return StoredSimulationRun(
            id=uuid4(),
            case_file_id=case_file_id,
            status="pending",
            result=None,
            error_message=None,
            created_at=fixed_datetime,
            started_at=None,
            completed_at=None,
        )

    return _build


@pytest.fixture
def client_factory():
    def _build(**kwargs) -> TestClient:
        client = TestClient(create_app())
        client.app.dependency_overrides[get_case_file_repository] = kwargs.get(
            "case_file_repository", get_case_file_repository
        )
        client.app.dependency_overrides[get_simulation_run_repository] = kwargs.get(
            "simulation_repository", get_simulation_run_repository
        )
        client.app.dependency_overrides[get_simulation_queue] = kwargs.get(
            "simulation_queue", get_simulation_queue
        )
        return client

    return _build
