from __future__ import annotations

from uuid import uuid4

from courtroom_domain import CaseFile


def build_initial_case_file() -> CaseFile:
    case_id = str(uuid4())
    return CaseFile.model_validate(
        {
            "case_id": case_id,
            "case_title": "People v. Vale",
            "case_type": "criminal",
            "charge_or_claim": "Grand theft auto",
            "parties": {
                "plaintiff_or_prosecution": "People of the State of California",
                "defendant": "Jordan Vale",
            },
            "ground_truth": "Jordan Vale took a vehicle from a repair lot without permission.",
            "disputed_facts": [
                {
                    "fact_id": "F1",
                    "text": "Whether Jordan Vale had permission to move the vehicle.",
                }
            ],
            "evidence": [
                {
                    "evidence_id": "E1",
                    "description": "Repair lot intake log showing the vehicle was left for service.",
                    "submitted_by": "prosecution",
                }
            ],
            "witnesses": [
                {
                    "witness_id": "W1",
                    "name": "Avery Brooks",
                    "persona": "Repair lot manager who checked in the vehicle.",
                    "called_by": "prosecution",
                    "knowledge_scope": "Can explain who had authority to release the vehicle.",
                }
            ],
        }
    )
