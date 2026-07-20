from __future__ import annotations

from uuid import uuid4

from courtroom_domain import CaseFile


def build_initial_case_file() -> CaseFile:
    case_id = str(uuid4())
    return CaseFile.model_validate(
        {
            "case_id": case_id,
            "case_title": "Untitled matter",
            "case_type": "criminal",
            "charge_or_claim": "Describe the dispute to generate the case file.",
            "parties": {
                "plaintiff_or_prosecution": "TBD",
                "defendant": "TBD",
            },
            "ground_truth": "Pending generation from the author's prompt.",
            "disputed_facts": [],
            "evidence": [],
            "witnesses": [],
        }
    )
