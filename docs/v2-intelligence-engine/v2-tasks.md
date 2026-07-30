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

Goal: teach the system to reach and explain a legally grounded verdict from the admitted record, evaluate every participant from cited courtroom evidence, and turn those evaluations into concrete coaching that helps a human learn to think like an elite trial lawyer. This slice is still AI-vs-AI only and must not touch frontend code or the existing V1 graph.

### Scope Boundary

- [x] Work only in `packages/courtroom-engine`, its tests, V2 docs, and additive `trial-v2-ai-ai` orchestration unless an OpenSpec artifact explicitly expands scope.
- [x] Do not modify `apps/web-app`, `apps/api-service`, or the existing V1 `trial` and `examine-witness` graphs.
- [x] Keep the Trial Judge and Evaluation Judge as separate roles with separate context policies, prompts, model routing, and output contracts.
- [x] Treat verdict, evaluation, coaching, and skill-profile updates as separate stages; coaching must transform evaluation observations and must not rescore the trial.
- [x] Require every verdict finding, evaluator observation, missed opportunity, and coaching moment to cite structured records instead of relying on transcript summary alone.
- [x] Keep deterministic validators as hard gates before LLM-based evaluation or coaching runs.

### Target Modules

- [x] Add `courtroom_engine/domain/deliberation/` for judge record, legal question, element finding, credibility finding, burden application, candidate finding, verdict, and validation models.
- [x] Add or expand `courtroom_engine/domain/evaluation/` for deterministic validation results, grounded observations, actor scores, missed opportunities, counterfactual comparisons, aggregation records, calibration records, and expert-review flags.
- [x] Add `courtroom_engine/domain/coaching/` for coaching moments, better-action sequences, example execution, case improvement plans, and skill evidence updates.
- [x] Add `courtroom_engine/application/deliberation/` for the judicial deliberation pipeline.
- [x] Add `courtroom_engine/application/evaluation/` for deterministic checks, specialist evaluators, missed-opportunity detection, counterfactual comparison, aggregation, and calibration.
- [x] Add `courtroom_engine/application/coaching/` only after evaluation acceptance gates pass.
- [x] Add `courtroom_engine/orchestration/deliberation_graph.py`, `evaluation_graph.py`, and `coaching_graph.py` as additive V2 subgraphs wired only into `trial-v2-ai-ai`.
- [x] Keep graph nodes thin: orchestration routes state, application services make decisions, domain models define contracts, policies enforce boundaries.

### Judicial Deliberation Foundation

- [x] Replace single verdict generation with a structured deliberation subgraph: `build_judge_record`, `identify_legal_questions`, `evaluate_elements`, `assess_credibility`, `apply_burden`, `generate_findings`, `challenge_findings`, `finalize_findings`, `generate_verdict`, and `validate_verdict`.
- [x] Build a judge-only record from admitted evidence, admitted testimony, stipulations, permitted arguments, jury or bench instructions, ruling records, and procedural status.
- [x] Exclude private simulation truth, unrevealed case intelligence, hidden contradiction labels, lawyer private strategy, evaluator-only references, and excluded evidence from the judge record.
- [x] Model `LegalQuestion` records for each claim, charge, defense, remedy, or verdict option that must be resolved.
- [x] Model `ElementEvaluation` records with element ID, burden holder, standard of proof, supporting admitted record citations, contrary admitted record citations, unresolved gaps, and provisional proved/not-proved status.
- [x] Model `WitnessCredibilityFinding` records that cite only testimony, admitted impeachment material, demeanor events if captured, prior admitted statements, and contradiction records made available in court.
- [x] Model `BurdenApplication` records that explicitly connect each element finding to the configured burden and standard.
- [x] Generate candidate findings from structured element and credibility records, then run a challenge pass that searches for unsupported findings, missing contrary evidence, burden mistakes, and record-boundary violations.
- [x] Generate the final verdict only from finalized findings, not directly from the raw transcript.
- [x] Validate verdict support deterministically: every dispositive finding must cite admitted records, every required element must be resolved, the configured burden must be applied, and no excluded or hidden material may influence the verdict.

### Evaluation Pipeline Foundation

- [x] Build `EvaluationState` from trial events, transcript events, admitted evidence state, strategy records, action decision records, ruling records, deliberation findings, verdict records, context audit records, and run metadata.
- [x] Run deterministic checks first for hidden-information leakage, nonexistent evidence citations, excluded evidence use, invalid phase transitions, unresolved objections, out-of-turn actions, unsupported transcript facts, role-boundary violations, and verdict findings unsupported by admitted records.
- [x] Fail closed or route to blocked evaluation status when deterministic checks show the trial record is structurally invalid.
- [x] Add specialist evaluator contracts for prosecution/plaintiff, defense, witnesses, trial judge, and simulation quality instead of a single all-purpose evaluation prompt.
- [x] Evaluate lawyers in separate dimensions: theory coherence, element coverage, objective selection, witness sequencing, evidence use, foundation, contradiction handling, objections, adaptation, opening, closing, procedure, role adherence, and professional conduct.
- [x] Evaluate witnesses primarily as simulation quality: knowledge-boundary compliance, consistency with personal knowledge, prior-statement consistency, appropriate uncertainty, persona stability, responsiveness, and non-disclosure of hidden facts.
- [x] Evaluate the trial judge for record-only rulings, neutral procedure handling, correct legal standard, burden treatment, evidence-to-fact reasoning, element findings, verdict support, and internal consistency.
- [x] Evaluate simulation quality for legal issue coverage, evidence coverage, adversarial balance, procedural realism, narrative coherence, contradiction handling, role separation, educational usefulness, and absence of unsupported facts.
- [x] Store evaluator identity, rubric version, prompt version, model version, input context policy version, confidence, abstention status, and human-review status on every evaluator output.

### Grounded Evaluation Observations

- [x] Define `EvaluationObservation` with evaluated actor, dimension, claim, severity, score impact, confidence, citations, affected objectives, recommended alternative, evaluator version, and review status.
- [x] Require citations to one or more structured records: fact IDs, evidence IDs, transcript event IDs, courtroom event IDs, strategy objective IDs, tactical action IDs, ruling IDs, contradiction IDs, element IDs, finding IDs, or verdict IDs.
- [x] Reject or mark invalid any evaluator observation that cannot cite supporting records.
- [x] Distinguish objective defects from advocacy judgment: structural invalidity, legal-grounding problem, strategic mistake, execution problem, witness-simulation defect, judge-reasoning defect, and coaching opportunity.
- [x] Add source-span or event-span support for observations that depend on a sequence, such as an abandoned cross-examination objective or missed impeachment setup.
- [x] Preserve low-confidence observations without converting them into firm coaching claims; low-confidence, high-severity observations should route to expert review.

### Missed Opportunity And Counterfactual Comparison

- [x] Detect missed opportunities only at high-value decision points: available contradiction, completed foundation, damaging admission, objection opportunity, opened-door moment, unsupported required element, or abandoned strategic objective.
- [x] Reconstruct the legally available state at the decision point before generating alternatives.
- [x] Generate bounded alternative actions from allowed actions, role context, active strategy objectives, admitted or usable evidence, witness knowledge boundaries, and procedural constraints.
- [x] Compare actual action against alternatives on legal relevance, objective advancement, evidence support, risk, recoverability, likely opponent response, and expected verdict sensitivity.
- [x] Store `CounterfactualComparison` records that include actual action, preferred action, rejected alternatives, assumptions, citations, expected value delta, risk analysis, confidence, and evaluator version.
- [x] Avoid exhaustive search across every utterance; reserve counterfactual evaluation for moments likely to change case strength or learning value.

### Coaching Readiness Gate

- [x] Do not build coaching graph behavior until evaluator outputs pass fixture-level citation validity, deterministic-validation gating, and reviewer-readable observation quality.
- [x] Establish a small golden evaluation fixture before coaching: one correct strategic move, one missed impeachment, one foundation failure, one witness boundary violation, and one unsupported verdict finding.
- [x] Gate coaching on a reviewer being able to trace each proposed coaching point back to a valid evaluation observation and the underlying courtroom records.
- [x] Ensure coaching never claims a human lied or gives legal advice beyond the simulated training context; coaching should focus on observable advocacy behavior and scenario-specific alternatives.

### Coaching Graph

- [x] Build coaching as a separate subgraph: `select_learning_moments`, `map_moments_to_skills`, `reconstruct_moment_state`, `explain_cause_and_consequence`, `generate_better_sequence`, `generate_example_execution`, `prioritize_feedback`, and `build_improvement_plan`.
- [x] Transform grounded observations into `CoachingMoment` records with transcript location, skill category, what happened, affected objective, available information, why it mattered, better action, example wording, expected response, recovery option, severity, and confidence.
- [x] Produce both outcome coaching and technique coaching: whether the action improved the case and whether the action was performed correctly.
- [x] Generate example questions or arguments only from facts and evidence legally available at that moment.
- [x] Prioritize coaching by severity, causal impact, repeated skill pattern, confidence, and educational usefulness.
- [x] Produce a session-level improvement plan that groups related moments into practice themes rather than listing every evaluator observation.

### Skill Evidence Updates

- [x] Add skill evidence records for legal grounding, issue spotting, theory development, objective selection, procedure, role adherence, evidence use, foundation, contradiction handling, witness control, objection handling, adaptation, opening, closing, judicial reasoning, and professional conduct.
- [x] Update skill profiles by appending evidence with citations, direction, strength, confidence, decay or recency metadata, and source evaluator version; do not overwrite a skill score from one run.
- [x] Keep AI actor skill evidence separate from future human learner profiles so AI-vs-AI simulation quality does not pollute human coaching data.
- [x] Support future AI-vs-Human reuse by designing skill evidence around actor IDs and role IDs, not hardcoded prosecution/defense model names.

### Tests And Acceptance

- [x] Add deliberation unit tests proving the judge record excludes private truth, excluded evidence, hidden contradiction labels, private strategy, and evaluator-only material.
- [x] Add verdict validation tests for missing element findings, burden mismatch, unsupported dispositive findings, excluded evidence reliance, unresolved legal questions, and invalid verdict options.
- [x] Add evaluation tests proving deterministic checks run before LLM-style evaluators and block structurally invalid records.
- [x] Add grounded-observation tests proving evaluator observations must cite valid facts, evidence, transcript events, strategy records, ruling records, findings, or verdict records.
- [x] Add missed-opportunity tests for at least one available contradiction, one abandoned objective, and one failure to use admitted evidence on a required element.
- [x] Add counterfactual comparison tests proving alternatives are generated only from procedurally allowed actions and legally available information.
- [x] Add coaching readiness tests proving coaching refuses invalid or citation-free evaluator observations.
- [x] Add coaching output tests proving every coaching moment traces to a valid observation and every example action stays within the reconstructed moment state.
- [x] Add skill evidence tests proving updates are append-only, cited, actor-scoped, role-scoped, and separated between AI actor metrics and future human learner profiles.
- [x] Gate completion on a reviewer being able to answer from structured outputs: what verdict was reached, which admitted records support each finding, which participant decisions changed case strength, which better actions were available, why those actions were better, and what skill evidence should drive future coaching.

## Skills And Policy Packs

- [x] Implement a skill registry with explicit loading rules.
- [x] Add global skills: citation grounding, source hierarchy, uncertainty handling, role-boundary compliance, professional conduct, and evidence provenance.
- [x] Add California jurisdiction skills for civil procedure, evidence, CACI instructions, and local court rules.
- [x] Add role skills for plaintiff/prosecution lawyer, defense lawyer, trial judge, juror, and witness.
- [x] Add phase skills for opening, direct, cross, redirect, objections, closing, and deliberation.
- [x] Add tactical skills for authentication, personal knowledge, impeachment, perception challenge, bias exposure, and causation.
- [x] Enforce that LLM calls cannot freely load arbitrary skills outside the current role, phase, jurisdiction, and allowed action.

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
