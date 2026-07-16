from __future__ import annotations

from courtroom_domain import CaseFile


def build_case_file(**overrides) -> CaseFile:
    payload = {
        "case_id": "case-123",
        "case_type": "criminal",
        "charge_or_claim": "Grand theft auto",
        "parties": {
            "plaintiff_or_prosecution": "People of the State of California",
            "defendant": "Jordan Vale",
        },
        "ground_truth": "Ground truth",
        "disputed_facts": ["Fact one"],
        "evidence": [],
        "witnesses": [],
    }
    payload.update(overrides)
    return CaseFile.model_validate(payload)
