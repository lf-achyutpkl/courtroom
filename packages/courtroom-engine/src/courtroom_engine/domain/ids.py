from __future__ import annotations

from typing import Annotated

from pydantic import Field

CaseId = Annotated[str, Field(pattern=r"^CASE-[A-Z0-9-]+$")]
PartyId = Annotated[str, Field(pattern=r"^PTY-[A-Z0-9-]+$")]
ActorId = Annotated[str, Field(pattern=r"^ACT-[A-Z0-9-]+$")]
MatterId = Annotated[str, Field(pattern=r"^(CLM|CHG)-[A-Z0-9-]+$")]
ElementId = Annotated[str, Field(pattern=r"^ELM-[A-Z0-9-]+$")]
FactId = Annotated[str, Field(pattern=r"^FAC-[A-Z0-9-]+$")]
EvidenceId = Annotated[str, Field(pattern=r"^EVD-[A-Z0-9-]+$")]
WitnessId = Annotated[str, Field(pattern=r"^WIT-[A-Z0-9-]+$")]
KnowledgeAtomId = Annotated[str, Field(pattern=r"^KNO-[A-Z0-9-]+$")]
ContradictionId = Annotated[str, Field(pattern=r"^CON-[A-Z0-9-]+$")]
ObjectiveId = Annotated[str, Field(pattern=r"^OBJ-[A-Z0-9-]+$")]
