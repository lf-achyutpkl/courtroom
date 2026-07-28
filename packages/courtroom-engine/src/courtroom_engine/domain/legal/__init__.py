from __future__ import annotations

from typing import Literal

from pydantic import model_validator

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.case import CaseKind, PartySide
from courtroom_engine.domain.ids import ElementId, MatterId


class LegalElement(DomainModel):
    element_id: ElementId
    label: str
    description: str
    burden: Literal["preponderance", "clear_and_convincing", "beyond_reasonable_doubt"]
    proving_side: PartySide


class ClaimOrCharge(DomainModel):
    matter_id: MatterId
    case_kind: CaseKind
    title: str
    elements: tuple[LegalElement, ...]

    @model_validator(mode="after")
    def validate_prefix(self) -> "ClaimOrCharge":
        if self.case_kind == CaseKind.CIVIL and not self.matter_id.startswith("CLM-"):
            raise ValueError("civil matters must use CLM-* ids")
        if self.case_kind == CaseKind.CRIMINAL and not self.matter_id.startswith(
            "CHG-"
        ):
            raise ValueError("criminal matters must use CHG-* ids")
        return self
