from __future__ import annotations

from uuid import uuid4

from courtroom_domain import CaseFile


def build_dummy_case_file() -> CaseFile:
    case_id = str(uuid4())
    return CaseFile.model_validate(
        {
            "case_id": case_id,
            "case_type": "criminal",
            "charge_or_claim": "Grand theft auto",
            "parties": {
                "plaintiff_or_prosecution": "People of the State of California",
                "defendant": "Jordan Vale",
            },
            "ground_truth": (
                "Jordan Vale borrowed a vehicle from a repair lot without permission, "
                "but returned it after being contacted by police."
            ),
            "disputed_facts": [
                (
                    "Whether Jordan Vale intended to permanently deprive the owner "
                    "of the vehicle."
                ),
                "Whether the repair lot gave implied permission to move the vehicle.",
            ],
            "evidence": [
                {
                    "evidence_id": "E1",
                    "description": (
                        "Repair lot security footage showing the vehicle leaving "
                        "at 8:42 PM."
                    ),
                    "submitted_by": "prosecution",
                },
                {
                    "evidence_id": "E2",
                    "description": (
                        "Text messages asking when the vehicle should be returned."
                    ),
                    "submitted_by": "defense",
                },
            ],
            "witnesses": [
                {
                    "witness_id": "W1",
                    "name": "Maya Chen",
                    "persona": "Repair lot manager",
                    "called_by": "prosecution",
                    "knowledge_scope": (
                        "Observed lot procedures and reported the missing vehicle."
                    ),
                },
                {
                    "witness_id": "W2",
                    "name": "Jordan Vale",
                    "persona": "Defendant",
                    "called_by": "defense",
                    "knowledge_scope": (
                        "Explains why the vehicle was taken and returned."
                    ),
                },
            ],
        }
    )
