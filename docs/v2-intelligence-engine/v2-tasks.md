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

- [ ] Implement case intelligence state and outputs: case graph, evidence graph, timeline graph, contradiction graph, material fact map, and case-gap records.
- [ ] Add a deterministic `analyze_case` service or subgraph that composes normalization, legal issue identification, element mapping, fact classification, evidence graph generation, witness knowledge graph generation, contradiction detection, and validation.
- [ ] Add provenance and confidence fields to derived intelligence objects.
- [ ] Add civil and criminal fixture cases, while keeping the first runnable vertical slice on one compact scenario.
- [ ] Add compiler tests for criminal `CHG-*` matters, civil `CLM-*` matters, missing burden elements, dangling evidence references, duplicate IDs, and mismatched case kind.

## Procedure And Role Isolation

- [ ] Define procedure state, allowed action registry, phase transitions, evidence admission state, objection state, and ruling records.
- [ ] Move allowed actions out of ad hoc context code into policy modules.
- [ ] Add role policies for plaintiff lawyer, prosecution lawyer, defense lawyer, witness, trial judge, jury, evaluator, and coach.
- [ ] Ensure trial judge context sees only admitted record plus disputed material needed for the current ruling.
- [ ] Ensure jury context sees only admitted evidence, testimony, stipulations, instructions, permitted arguments, and verdict form.
- [ ] Add event stream and replay-friendly courtroom event models before expanding graph execution.

## Strategy Planner

- [ ] Add structured strategy models: `PartyStrategy`, `CaseTheory`, `StrategicObjective`, `WitnessPlan`, `EvidencePlan`, opponent-risk records, and objective runtime state.
- [ ] Build reusable strategy planning per side instead of separate hardcoded plaintiff/prosecution/defense flows.
- [ ] Validate strategy against role context, legal elements, available facts, disclosed evidence, and procedure.
- [ ] Add global strategy, witness selection, examination objective, tactical action, and question generation contexts in that order.
- [ ] Add tests proving strategy nodes receive strategy context but question generation receives only an execution brief.

## Minimum Practical V2 Graph

- [ ] Replace the smoke graph with the minimum practical graph from `v2-graph-design.md`: initialize session, analyze case, plan both sides, opening phase, witness loop, closing record, closing phase, structured deliberation, evaluation.
- [ ] Keep major phases as root nodes and use subgraphs for case intelligence, strategy, witness examination, deliberation, and evaluation.
- [ ] Store root state as references and phase outputs rather than copying the complete case into every checkpoint.
- [ ] Keep `trial-v2-ai-ai` additive and leave `trial` and `examine-witness` unchanged.

## Witness Examination Redesign

- [ ] Build the structured witness examination subgraph: initialize examination, select objective, plan action, validate action, generate question, objection decision, judge ruling, witness answer, validate answer, update evidence state, detect new contradictions, assess objective progress, transition examination, finalize witness.
- [ ] Separate tactical action planning from courtroom question generation.
- [ ] Add deterministic updater for facts, evidence, contradictions, objective progress, and witness credibility signals after every accepted answer.
- [ ] Ensure witness answer context includes only relevant knowledge atoms, prior testimony, shown exhibits, current question, and witness behavior profile.
- [ ] Add validator behavior that distinguishes model hallucination from intentional witness contradiction.

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
