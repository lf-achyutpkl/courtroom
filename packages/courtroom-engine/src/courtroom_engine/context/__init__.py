from __future__ import annotations

from .assembler import ContextBoundaryService
from .projections import (
    ActorCaseViewDTO,
    ActorContextDTO,
    BaseNodeContext,
    CaseGapContextDTO,
    ContextAuditRecord,
    ContextMetadata,
    ContextRequest,
    EvidenceContextDTO,
    EvidenceRelationshipContextDTO,
    FactContextDTO,
    MaterialFactContextDTO,
    ModelNodeContextDTO,
    NodePurpose,
    ProceduralContext,
    PublicCaseIntelligenceContextDTO,
    QuestionExecutionBriefDTO,
    TacticalActionPlanDTO,
    WitnessFactContextDTO,
    WitnessKnowledgeContextDTO,
)

ActorCaseView = ActorCaseViewDTO
ModelNodeContext = ModelNodeContextDTO

__all__ = [
    "ActorCaseView",
    "ActorCaseViewDTO",
    "ActorContextDTO",
    "BaseNodeContext",
    "CaseGapContextDTO",
    "ContextAuditRecord",
    "ContextBoundaryService",
    "ContextMetadata",
    "ContextRequest",
    "EvidenceContextDTO",
    "EvidenceRelationshipContextDTO",
    "FactContextDTO",
    "MaterialFactContextDTO",
    "ModelNodeContext",
    "ModelNodeContextDTO",
    "NodePurpose",
    "ProceduralContext",
    "PublicCaseIntelligenceContextDTO",
    "QuestionExecutionBriefDTO",
    "TacticalActionPlanDTO",
    "WitnessFactContextDTO",
    "WitnessKnowledgeContextDTO",
]
