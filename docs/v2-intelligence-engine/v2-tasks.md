# V2 Intelligence Engine Tasks

This tracks remaining V2 AI-vs-AI work after the initial foundation pass. Source references:

- `v2-ai-ai-implementation-plan.md`
- `v2-graph-design.md`
- `v2-intelligence-engine-blueprint.md`
- `v2-structure.md`
- `v2-skills.md`

## Current Baseline

- [x] Created additive `packages/courtroom-engine` package.
- [x] Added V2 authored/compiled case models, private truth, derived intelligence, and runtime state foundation.
- [x] Added deterministic `CaseCompiler` with initial ID, reference, visibility, party, evidence, and witness-knowledge checks.
- [x] Added typed context requests, context envelope, role-aware context boundary service, and fail-closed leakage tests.
- [x] Registered separate LangStudio graph key `trial-v2-ai-ai` without replacing V1 `trial`.
- [x] Added minimal V2 graph smoke path proving case compilation and context-boundary verification.

## Next Engineering Task

- [x] Expand the case model and context boundary foundation into the planned package structure from `v2-structure.md`.
- [x] Split current flat `courtroom_engine.models` into domain modules for case, evidence, witnesses, legal, strategy, simulation truth, trial state, and events.
- [x] Add explicit public DTOs for every actor-facing context so restricted contexts never rely on copying canonical models and removing fields.
- [x] Add context audit records with included IDs, excluded categories, policy version, projection version, estimated context size, and violation status.
- [x] Add tests for unknown visibility, evaluator-only truth leakage, opposing private strategy leakage, non-target witness knowledge leakage, and direct canonical package access in model-backed nodes.

## Case Intelligence Foundation

Goal: teach the system to read a compact case the way an elite trial lawyer starts reading it: identify what must be proved, which facts matter, which evidence can prove or attack those facts, which witness can establish each point, where the story conflicts, and which gaps should drive strategy. This slice is still AI-vs-AI only and must not touch frontend code or the existing V1 graph.

### Scope Boundary

- [x] Work only in `packages/courtroom-engine`, its tests, and V2 docs unless an OpenSpec artifact explicitly expands scope.
- [x] Keep `trial-v2-ai-ai` additive and do not modify the existing V1 `trial` or `examine-witness` graphs.
- [x] Keep case intelligence deterministic first; use LLM-shaped seams only as typed ports or future adapters, not as required runtime behavior for this slice.
- [x] Treat derived intelligence as separate from authored case facts, private simulation truth, and runtime trial state.
- [x] Ensure no actor-facing context receives canonical case packages, evaluator-only truth, hidden contradiction labels, or another witness's private knowledge.

### Target Modules

- [x] Add `courtroom_engine/domain/case_intelligence/` for derived intelligence models.
- [x] Add `courtroom_engine/application/case_analysis/` for the deterministic analyzer pipeline.
- [x] Keep graph orchestration glue out of the domain layer; any future LangGraph subgraph belongs under `courtroom_engine/orchestration/`.
- [x] Export only stable public types through `courtroom_engine.models` and package `__init__.py` after the internal modules are in place.

### Derived Intelligence Models

- [x] Implement `CaseIntelligenceReport` as the top-level analyzer output attached to `CompiledCasePackage.intelligence`.
- [x] Implement `CaseGraph` with typed nodes and edges for matters, claims or charges, defenses, legal elements, parties, facts, evidence, witnesses, authorities, remedies, and possible verdict outcomes.
- [x] Implement `EvidenceGraph` with evidence-to-fact, evidence-to-element, evidence-to-witness, foundation, authenticity, admissibility, impeachment, and contradiction relationships.
- [x] Implement `TimelineGraph` with event ordering, approximate dates, sequence constraints, source references, temporal gaps, and temporal conflicts.
- [x] Implement `ContradictionGraph` with contradiction records that distinguish witness-vs-witness, witness-vs-document, witness-vs-prior-statement, fact-vs-timeline, claim-vs-evidence, internal-testimony, and theory inconsistency.
- [x] Implement `MaterialFactMap` that maps every legally material fact to its matter, legal element, supporting side, opposing side, dispute status, supporting evidence, contradicting evidence, knowledgeable witnesses, and current proof status.
- [x] Implement `CaseGap` records for missing burden proof, missing foundation, unsupported material facts, unresolved legal issues, one-witness dependencies, weak corroboration, temporal gaps, and contradiction opportunities.
- [x] Add shared provenance and confidence fields to every derived intelligence object that was inferred or classified, including source IDs, derivation method, analyzer version, confidence score, and review status.

### Analyzer Pipeline

- [x] Add deterministic `analyze_case(template_or_package)` application service that returns a validated `CaseIntelligenceReport`.
- [x] Compose the analyzer as ordered, independently testable steps: `normalize_case`, `identify_legal_issues`, `map_legal_elements`, `classify_material_facts`, `build_evidence_graph`, `build_timeline_graph`, `build_witness_knowledge_graph`, `detect_contradictions`, `analyze_case_gaps`, and `validate_case_intelligence`.
- [x] Keep each step pure where practical: input typed case data, output typed intelligence fragments or validation errors.
- [x] Record analyzer diagnostics instead of silently rewriting ambiguous case material.
- [x] Make validation fail closed when references are dangling, confidence is missing for inferred relationships, or derived intelligence claims more than the authored case supports.
- [x] Preserve the existing compiler entry point while moving its current minimal derivation behind the new analyzer service.

### First Vertical Slice

- [x] Use one compact civil scenario as the first runnable case-intelligence fixture.
- [x] Add one compact criminal scenario after the civil path passes, specifically to exercise `CHG-*` matter IDs, prosecution burden, defense theory, and criminal verdict options.
- [x] Keep fixture cases small enough that a human can manually inspect every claim, element, fact, witness, evidence item, contradiction, and gap.
- [x] Include expert-reference expectations in fixtures only as private simulation truth or test fixtures, not as actor-visible case context.

### Tests And Acceptance

- [x] Add unit tests for case graph construction from civil `CLM-*` matters and criminal `CHG-*` matters.
- [x] Add compiler or analyzer validation tests for missing burden elements, dangling evidence references, dangling witness knowledge references, duplicate IDs, mismatched case kind, malformed matter prefixes, and unknown visibility.
- [x] Add tests proving every material fact has provenance, every inferred edge has confidence, and every contradiction points to valid source objects.
- [x] Add tests proving evaluator-only truth, hidden contradiction labels, private strategy, and non-target witness knowledge stay out of actor-facing derived intelligence contexts.
- [x] Add golden-case tests for the first civil fixture covering expected material fact map, evidence graph edges, witness knowledge graph edges, contradiction candidates, and case gaps.
- [x] Gate completion on a reviewer being able to answer from structured outputs: what must be proved, what proves it, who can establish it, what attacks it, what is missing, and why the next strategy planner has enough input to reason like a trial lawyer.

## Procedure And Role Isolation

- [x] Define procedure state, allowed action registry, phase transitions, evidence admission state, objection state, and ruling records.
- [x] Move allowed actions out of ad hoc context code into policy modules.
- [x] Add role policies for plaintiff lawyer, prosecution lawyer, defense lawyer, witness, trial judge, jury, evaluator, and coach.
- [x] Ensure trial judge context sees only admitted record plus disputed material needed for the current ruling.
- [x] Ensure jury context sees only admitted evidence, testimony, stipulations, instructions, permitted arguments, and verdict form.
- [x] Add event stream and replay-friendly courtroom event models before expanding graph execution.

## Strategy Planner

- [x] Add structured strategy models: `PartyStrategy`, `CaseTheory`, `StrategicObjective`, `WitnessPlan`, `EvidencePlan`, opponent-risk records, and objective runtime state.
- [x] Build reusable strategy planning per side instead of separate hardcoded plaintiff/prosecution/defense flows.
- [x] Validate strategy against role context, legal elements, available facts, disclosed evidence, and procedure.
- [x] Add global strategy, witness selection, examination objective, tactical action, and question generation contexts in that order.
- [x] Add tests proving strategy nodes receive strategy context but question generation receives only an execution brief.

## Minimum Practical V2 Graph

- [x] Replace the smoke graph with the minimum practical graph from `v2-graph-design.md`: initialize session, analyze case, plan both sides, opening phase, witness loop, closing record, closing phase, structured deliberation, evaluation.
- [x] Keep major phases as root nodes and use subgraphs for case intelligence, strategy, witness examination, deliberation, and evaluation.
- [x] Store root state as references and phase outputs rather than copying the complete case into every checkpoint.
- [x] Keep `trial-v2-ai-ai` additive and leave `trial` and `examine-witness` unchanged.

## Witness Examination Redesign

- [x] Build the structured witness examination subgraph: initialize examination, select objective, plan action, validate action, generate question, objection decision, judge ruling, witness answer, validate answer, update evidence state, detect new contradictions, assess objective progress, transition examination, finalize witness.
- [x] Separate tactical action planning from courtroom question generation.
- [x] Add deterministic updater for facts, evidence, contradictions, objective progress, and witness credibility signals after every accepted answer.
- [x] Ensure witness answer context includes only relevant knowledge atoms, prior testimony, shown exhibits, current question, and witness behavior profile.
- [x] Add validator behavior that distinguishes model hallucination from intentional witness contradiction.

## Verdict, Evaluation, And Coaching

- [ ] Replace single verdict generation with structured judicial deliberation: judge record, legal questions, element evaluation, witness credibility, burden application, candidate findings, challenge findings, final verdict, verdict validation.
- [ ] Add evaluation pipeline: deterministic checks, prosecution/plaintiff evaluation, defense evaluation, witness evaluation, judge evaluation, simulation evaluation, missed opportunity detection, counterfactual comparison, aggregation, confidence calibration.
- [ ] Add grounded evaluation observations that cite facts, evidence, transcript events, strategy records, or ruling records.
- [ ] Add coaching graph only after evaluator quality is acceptable; coaching should transform grounded observations, not rescore the trial.
- [ ] Add skill evidence updates for legal grounding, procedure, role adherence, evidence use, contradiction handling, and professional conduct.

## Skills And Policy Packs

- [ ] Implement a skill registry with explicit loading rules.
- [ ] Add global skills: citation grounding, source hierarchy, uncertainty handling, role-boundary compliance, professional conduct, and evidence provenance.
- [ ] Add California jurisdiction skills for civil procedure, evidence, CACI instructions, and local court rules.
- [ ] Add role skills for plaintiff/prosecution lawyer, defense lawyer, trial judge, juror, and witness.
- [ ] Add phase skills for opening, direct, cross, redirect, objections, closing, and deliberation.
- [ ] Add tactical skills for authentication, personal knowledge, impeachment, perception challenge, bias exposure, and causation.
- [ ] Enforce that LLM calls cannot freely load arbitrary skills outside the current role, phase, jurisdiction, and allowed action.

## Testing And Acceptance Gates

- [ ] Add package-level tests under `packages/courtroom-engine/tests` once the package structure expands.
- [ ] Add scenario tests for one compact AI-vs-AI vertical slice.
- [ ] Add regression tests for context leakage, invalid phase transitions, unsupported evidence references, malformed IDs, and hallucinated facts.
- [ ] Add LangStudio smoke tests for `trial-v2-ai-ai`.
- [ ] Add blind comparison dataset later to compare V2 planner-selected actions against V1 prompt-only actions.
- [ ] Do not add frontend or API integration tests until LangStudio validation is complete.

## Explicitly Out Of Scope For Current V2 Slice

- [ ] Frontend UI changes.
- [ ] FastAPI route changes.
- [ ] RQ worker changes.
- [ ] AI-vs-Human interrupts.
- [ ] Human-vs-Human mode.
- [ ] Fine-tuning.
- [ ] Production learning loops.
- [ ] Multi-jurisdiction support beyond initial California-oriented abstractions.
