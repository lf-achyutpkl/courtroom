from __future__ import annotations

from courtroom_engine.application.case_analysis import analyze_case

from .models import (
    AuthoredCaseTemplate,
    CompiledCasePackage,
    PartySide,
    VisibilityScope,
)


class CaseCompiler:
    """Validates authored V2 cases and derives minimum graph inputs."""

    def compile(self, template: AuthoredCaseTemplate) -> CompiledCasePackage:
        self._validate(template)
        return CompiledCasePackage(
            metadata=template.metadata,
            parties=template.parties,
            actors=template.actors,
            matters=template.matters,
            facts=template.facts,
            evidence=template.evidence,
            witnesses=template.witnesses,
            witness_knowledge=template.witness_knowledge,
            intelligence=analyze_case(template),
            private_truth=template.private_truth,
        )

    def _validate(self, template: AuthoredCaseTemplate) -> None:
        party_ids = {party.party_id for party in template.parties}
        actor_ids = {actor.actor_id for actor in template.actors}
        matter_ids = {matter.matter_id for matter in template.matters}
        fact_ids = {fact.fact_id for fact in template.facts}
        evidence_ids = {item.evidence_id for item in template.evidence}
        element_ids = {
            element.element_id
            for matter in template.matters
            for element in matter.elements
        }
        witness_ids = {witness.witness_id for witness in template.witnesses}
        knowledge_ids = {atom.knowledge_atom_id for atom in template.witness_knowledge}

        if len(party_ids) != len(template.parties):
            raise ValueError("duplicate party ids are not allowed")
        if len(actor_ids) != len(template.actors):
            raise ValueError("duplicate actor ids are not allowed")
        if len(matter_ids) != len(template.matters):
            raise ValueError("duplicate matter ids are not allowed")
        element_count = sum(len(matter.elements) for matter in template.matters)
        if len(element_ids) != element_count:
            raise ValueError("duplicate element ids are not allowed")
        if len(fact_ids) != len(template.facts):
            raise ValueError("duplicate fact ids are not allowed")
        if len(evidence_ids) != len(template.evidence):
            raise ValueError("duplicate evidence ids are not allowed")
        if len(witness_ids) != len(template.witnesses):
            raise ValueError("duplicate witness ids are not allowed")
        if len(knowledge_ids) != len(template.witness_knowledge):
            raise ValueError("duplicate witness knowledge ids are not allowed")

        self._validate_case_sides(template)

        for actor in template.actors:
            if actor.party_id is not None and actor.party_id not in party_ids:
                raise ValueError(f"unknown actor party id: {actor.party_id}")
            if actor.witness_id is not None and actor.witness_id not in witness_ids:
                raise ValueError(f"unknown actor witness id: {actor.witness_id}")

        for fact in template.facts:
            for element_id in fact.supports_element_ids:
                if element_id not in element_ids:
                    raise ValueError(f"unknown fact element id: {element_id}")

        for evidence in template.evidence:
            for fact_id in evidence.supports_fact_ids:
                if fact_id not in fact_ids:
                    raise ValueError(f"unknown evidence fact id: {fact_id}")

        knowledge_by_id = {
            atom.knowledge_atom_id: atom for atom in template.witness_knowledge
        }
        for atom in template.witness_knowledge:
            if atom.witness_id not in witness_ids:
                raise ValueError(f"unknown knowledge witness id: {atom.witness_id}")
            if atom.visibility != VisibilityScope.WITNESS_PRIVATE:
                raise ValueError("witness knowledge must be witness-private")
            for fact_id in atom.related_fact_ids:
                if fact_id not in fact_ids:
                    raise ValueError(f"unknown knowledge fact id: {fact_id}")

        for witness in template.witnesses:
            for atom_id in witness.knowledge_atom_ids:
                atom = knowledge_by_id.get(atom_id)
                if atom is None:
                    raise ValueError(f"unknown witness knowledge atom id: {atom_id}")
                if atom.witness_id != witness.witness_id:
                    raise ValueError(
                        f"knowledge atom {atom_id} belongs to {atom.witness_id}, "
                        f"not {witness.witness_id}"
                    )

    def _validate_case_sides(self, template: AuthoredCaseTemplate) -> None:
        sides = {party.side for party in template.parties}
        if template.metadata.case_kind == "civil":
            required = {PartySide.PLAINTIFF, PartySide.DEFENSE}
        else:
            required = {PartySide.PROSECUTION, PartySide.DEFENSE}
        if not required.issubset(sides):
            raise ValueError(f"{template.metadata.case_kind} cases require {required}")
        for matter in template.matters:
            if matter.case_kind != template.metadata.case_kind:
                raise ValueError("matter case kind must match case metadata")
            if not matter.elements:
                raise ValueError("matters must define at least one legal element")
