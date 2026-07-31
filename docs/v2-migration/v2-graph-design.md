# AI-vs-AI Courtroom Graph Design

## 1. Recommended High-Level Flow

```text
START
  │
  ▼
┌───────────────────────────────────────┐
│ 1. SESSION INITIALIZATION             │
│                                       │
│ Load case                             │
│ Load simulation configuration         │
│ Load jurisdiction pack                │
│ Validate inputs                       │
└───────────────────┬───────────────────┘
                    ▼
┌───────────────────────────────────────┐
│ 2. CASE INTELLIGENCE                  │
│                                       │
│ Build case graph                      │
│ Build evidence graph                  │
│ Build timeline                        │
│ Detect contradictions                 │
│ Identify missing support              │
└───────────────────┬───────────────────┘
                    ▼
┌───────────────────────────────────────┐
│ 3. PRETRIAL STRATEGY                  │
│                                       │
│ Prosecution theory                    │
│ Defense theory                        │
│ Strategic objectives                  │
│ Witness plans                         │
│ Evidence plans                        │
│ Anticipated opponent strategy         │
└───────────────────┬───────────────────┘
                    ▼
┌───────────────────────────────────────┐
│ 4. OPENING PHASE                      │
│                                       │
│ Plan opening objectives               │
│ Generate prosecution opening          │
│ Generate defense opening              │
│ Update commitments and trial state    │
└───────────────────┬───────────────────┘
                    ▼
┌───────────────────────────────────────┐
│ 5. EVIDENCE PRESENTATION LOOP         │
│                                       │
│ Select witness                        │
│ Prepare witness examination           │
│ Direct examination                    │
│ Cross-examination                     │
│ Redirect / recross when allowed       │
│ Update evidence and strategy state    │
└───────────────────┬───────────────────┘
                    │ Repeat for witnesses
                    ▼
┌───────────────────────────────────────┐
│ 6. PRE-CLOSING ANALYSIS               │
│                                       │
│ Reconstruct trial record              │
│ Measure element satisfaction          │
│ Identify unresolved disputes          │
│ Update final strategies               │
└───────────────────┬───────────────────┘
                    ▼
┌───────────────────────────────────────┐
│ 7. CLOSING PHASE                      │
│                                       │
│ Plan prosecution closing              │
│ Generate prosecution closing          │
│ Plan defense closing                  │
│ Generate defense closing              │
└───────────────────┬───────────────────┘
                    ▼
┌───────────────────────────────────────┐
│ 8. JUDICIAL DECISION                  │
│                                       │
│ Build judge-only record               │
│ Apply legal elements and burden       │
│ Produce findings                      │
│ Produce verdict                       │
│ Validate verdict support              │
└───────────────────┬───────────────────┘
                    ▼
┌───────────────────────────────────────┐
│ 9. EVALUATION                         │
│                                       │
│ Deterministic validation              │
│ Prosecution evaluation                │
│ Defense evaluation                    │
│ Witness evaluation                    │
│ Judge evaluation                      │
│ Simulation evaluation                 │
│ Aggregate findings                    │
└───────────────────┬───────────────────┘
                    ▼
┌───────────────────────────────────────┐
│ 10. COACHING AND LEARNING DATA        │
│                                       │
│ Detect missed opportunities           │
│ Generate better alternatives          │
│ Produce case-strength report          │
│ Store structured learning traces      │
└───────────────────┬───────────────────┘
                    ▼
                   END
```

---

# 2. Root Graph

The root graph should represent the major phases of the trial. It should not contain every question and answer directly.

```python
def build_trial_graph():
    builder = StateGraph(TrialState)

    # Phase 1: Initialization
    builder.add_node(
        "initialize_session",
        initialize_session_node,
    )
    builder.add_node(
        "analyze_case",
        build_case_intelligence_graph(),
    )

    # Phase 2: Pretrial planning
    builder.add_node(
        "plan_prosecution_case",
        build_case_strategy_graph(side="prosecution"),
    )
    builder.add_node(
        "plan_defense_case",
        build_case_strategy_graph(side="defense"),
    )
    builder.add_node(
        "finalize_trial_plan",
        finalize_trial_plan_node,
    )

    # Phase 3: Trial
    builder.add_node(
        "run_opening_phase",
        build_opening_graph(),
    )
    builder.add_node(
        "select_next_witness",
        select_next_witness_node,
    )
    builder.add_node(
        "run_witness_examination",
        build_witness_examination_graph(),
    )
    builder.add_node(
        "update_trial_position",
        update_trial_position_node,
    )

    # Phase 4: Closing and verdict
    builder.add_node(
        "prepare_closings",
        prepare_closing_record_node,
    )
    builder.add_node(
        "run_closing_phase",
        build_closing_graph(),
    )
    builder.add_node(
        "run_deliberation",
        build_judicial_deliberation_graph(),
    )

    # Phase 5: Evaluation
    builder.add_node(
        "run_evaluation",
        build_evaluation_graph(),
    )
    builder.add_node(
        "generate_coaching",
        build_coaching_graph(),
    )
    builder.add_node(
        "persist_learning_trace",
        persist_learning_trace_node,
    )

    builder.add_edge(START, "initialize_session")
    builder.add_edge("initialize_session", "analyze_case")

    builder.add_edge("analyze_case", "plan_prosecution_case")
    builder.add_edge("analyze_case", "plan_defense_case")

    builder.add_edge(
        ["plan_prosecution_case", "plan_defense_case"],
        "finalize_trial_plan",
    )

    builder.add_edge("finalize_trial_plan", "run_opening_phase")
    builder.add_edge("run_opening_phase", "select_next_witness")

    builder.add_conditional_edges(
        "select_next_witness",
        route_after_witness_selection,
        {
            "examine": "run_witness_examination",
            "complete": "prepare_closings",
        },
    )

    builder.add_edge(
        "run_witness_examination",
        "update_trial_position",
    )
    builder.add_edge(
        "update_trial_position",
        "select_next_witness",
    )

    builder.add_edge("prepare_closings", "run_closing_phase")
    builder.add_edge("run_closing_phase", "run_deliberation")
    builder.add_edge("run_deliberation", "run_evaluation")
    builder.add_edge("run_evaluation", "generate_coaching")
    builder.add_edge(
        "generate_coaching",
        "persist_learning_trace",
    )
    builder.add_edge("persist_learning_trace", END)

    return builder.compile(checkpointer=production_checkpointer)
```

LangGraph supports using compiled subgraphs as nodes, conditional routing, checkpointed state, state inspection, and replay. That matches this design well because each major courtroom phase can be independently persisted and inspected.

---

# 3. Root Graph Node Responsibilities

## 3.1 `initialize_session`

### Goal

Create a valid, reproducible courtroom session.

### Responsibilities

* Load the original `CaseFile`.
* Load mode configuration.
* Load jurisdiction configuration.
* Assign models to roles.
* Create stable IDs.
* Initialize event history.
* Initialize procedural state.
* Initialize evidence admission state.
* Record model and prompt versions.

### Input

```text
CaseFile
SessionConfig
```

### Output

```text
TrialState
 ├── session_id
 ├── case_file
 ├── mode_config
 ├── jurisdiction_pack
 ├── current_phase
 ├── actors
 ├── events
 └── runtime_metadata
```

### LLM required?

No.

This should be deterministic application code.

---

## 3.2 `analyze_case`

### Goal

Convert the supplied case file into structured legal intelligence.

This should be a subgraph.

```text
START
  ↓
normalize_case
  ↓
identify_claims_and_defenses
  ↓
map_legal_elements
  ↓
classify_facts
  ├───────────────┬────────────────┐
  ▼               ▼                ▼
build_evidence  build_timeline  build_witness_knowledge
  └───────────────┴────────────────┘
                  ↓
detect_contradictions
                  ↓
analyze_case_gaps
                  ↓
validate_case_intelligence
                  ↓
END
```

### Suggested graph

```python
def build_case_intelligence_graph():
    builder = StateGraph(CaseIntelligenceState)

    builder.add_node("normalize_case", normalize_case_node)
    builder.add_node(
        "identify_legal_issues",
        identify_legal_issues_node,
    )
    builder.add_node(
        "map_legal_elements",
        map_legal_elements_node,
    )
    builder.add_node(
        "classify_material_facts",
        classify_material_facts_node,
    )

    builder.add_node(
        "build_evidence_graph",
        build_evidence_graph_node,
    )
    builder.add_node(
        "build_timeline_graph",
        build_timeline_graph_node,
    )
    builder.add_node(
        "build_witness_knowledge",
        build_witness_knowledge_node,
    )

    builder.add_node(
        "detect_contradictions",
        detect_contradictions_node,
    )
    builder.add_node(
        "analyze_case_gaps",
        analyze_case_gaps_node,
    )
    builder.add_node(
        "validate_case_intelligence",
        validate_case_intelligence_node,
    )

    builder.add_edge(START, "normalize_case")
    builder.add_edge(
        "normalize_case",
        "identify_legal_issues",
    )
    builder.add_edge(
        "identify_legal_issues",
        "map_legal_elements",
    )
    builder.add_edge(
        "map_legal_elements",
        "classify_material_facts",
    )

    builder.add_edge(
        "classify_material_facts",
        "build_evidence_graph",
    )
    builder.add_edge(
        "classify_material_facts",
        "build_timeline_graph",
    )
    builder.add_edge(
        "classify_material_facts",
        "build_witness_knowledge",
    )

    builder.add_edge(
        [
            "build_evidence_graph",
            "build_timeline_graph",
            "build_witness_knowledge",
        ],
        "detect_contradictions",
    )

    builder.add_edge(
        "detect_contradictions",
        "analyze_case_gaps",
    )
    builder.add_edge(
        "analyze_case_gaps",
        "validate_case_intelligence",
    )
    builder.add_edge(
        "validate_case_intelligence",
        END,
    )

    return builder.compile()
```

The three graph-building operations can run in parallel because they consume the same normalized fact set and produce independent outputs. LangGraph supports fan-out and fan-in execution for independent tasks.

---

# 4. Case Intelligence Nodes

## 4.1 `normalize_case`

### Goal

Normalize IDs, fields, references and classifications.

### Responsibilities

* Ensure every fact, evidence item and witness has a stable ID.
* Resolve duplicate references.
* Normalize party and actor names.
* Normalize dates.
* Reject malformed relationships.
* Preserve source provenance.

### LLM required?

Mostly no.

An LLM may help interpret free-text fields, but schema normalization should be deterministic.

---

## 4.2 `identify_legal_issues`

### Goal

Identify charges, claims, defenses and disputed legal questions.

### Example output

```json
{
  "claims": [
    {
      "claim_id": "claim_theft",
      "name": "Theft",
      "asserted_by": "prosecution"
    }
  ],
  "defenses": [
    {
      "defense_id": "defense_mistaken_identity",
      "name": "Mistaken identity",
      "asserted_by": "defense"
    }
  ]
}
```

### LLM required?

Yes, when the case file is unstructured.

Use structured output rather than natural-language strategy.

---

## 4.3 `map_legal_elements`

### Goal

Determine what each party must prove or defeat.

### Output

```text
Claim
  ├── Element 1
  ├── Element 2
  └── Element 3

Defense
  └── Negates or qualifies specific elements
```

Each legal element should include:

```text
element_id
description
burden_holder
standard
supporting_fact_ids
contradicting_fact_ids
current_status
```

### LLM required?

Potentially.

Eventually this should be driven primarily by the jurisdiction pack and legal retrieval, with the LLM mapping the case to known legal elements.

---

## 4.4 `classify_material_facts`

### Goal

Determine how each fact relates to the legal issues.

### Output classification

* Undisputed.
* Disputed.
* Supporting prosecution.
* Supporting defense.
* Neutral context.
* Credibility-related.
* Procedural.
* Missing or uncertain.

---

## 4.5 `build_evidence_graph`

### Goal

Connect evidence to facts, elements, witnesses and admissibility requirements.

### Output example

```text
E-03
 ├── supports F-08
 ├── contradicts statement S-02
 ├── authenticatable_by W-02
 ├── relevant_to element identity
 └── status not_offered
```

---

## 4.6 `build_timeline_graph`

### Goal

Create the event sequence and identify temporal gaps or conflicts.

### Output

* Ordered events.
* Approximate events.
* Conflicting timestamps.
* Unsupported time periods.
* Relevant sequence constraints.

---

## 4.7 `build_witness_knowledge`

### Goal

Create an explicit information boundary for every witness.

### Output

```text
WitnessKnowledge
 ├── personally_known_fact_ids
 ├── uncertain_fact_ids
 ├── unknown_fact_ids
 ├── prior_statement_ids
 ├── evidence_they_can_authenticate
 └── prohibited_hidden_information
```

This becomes the source of truth for witness answers.

---

## 4.8 `detect_contradictions`

### Goal

Create the initial contradiction graph.

### Detect

* Witness versus witness.
* Witness versus document.
* Witness versus prior statement.
* Fact versus timeline.
* Claim versus evidence.
* Internal case-theory inconsistency.

---

## 4.9 `analyze_case_gaps`

### Goal

Identify what is missing before strategies are created.

### Example output

```text
Gap:
Element "identity" depends on one eyewitness.

Weakness:
No corroborating physical evidence.

Possible response:
Challenge lighting, distance and prior uncertainty.
```

---

## 4.10 `validate_case_intelligence`

### Goal

Prevent unsupported or malformed analysis from entering the trial.

### Deterministic checks

* Every evidence relationship points to a real fact.
* Every strategy-relevant fact has source provenance.
* Every legal element belongs to a claim or defense.
* Every witness knowledge reference exists.
* Contradiction references are valid.
* No original fact was silently rewritten.
* Confidence is present for inferred relationships.

---

# 5. Case Strategy Graph

Replace your current single `prosecution_strategy` and `defense_strategy` calls with one reusable strategy subgraph configured by side.

```text
START
  ↓
build_actor_case_view
  ↓
assess_case_position
  ↓
develop_case_theory
  ↓
generate_strategic_objectives
  ↓
plan_witness_usage
  ↓
plan_evidence_usage
  ↓
anticipate_opponent_strategy
  ↓
rank_and_validate_strategy
  ↓
finalize_strategy
  ↓
END
```

## Suggested graph

```python
def build_case_strategy_graph(side: PartySide):
    builder = StateGraph(CaseStrategyState)

    builder.add_node(
        "build_actor_case_view",
        build_actor_case_view_node,
    )
    builder.add_node(
        "assess_case_position",
        assess_case_position_node,
    )
    builder.add_node(
        "develop_case_theory",
        develop_case_theory_node,
    )
    builder.add_node(
        "generate_objectives",
        generate_strategic_objectives_node,
    )

    builder.add_node(
        "plan_witness_usage",
        plan_witness_usage_node,
    )
    builder.add_node(
        "plan_evidence_usage",
        plan_evidence_usage_node,
    )
    builder.add_node(
        "anticipate_opponent",
        anticipate_opponent_strategy_node,
    )

    builder.add_node(
        "rank_strategy",
        rank_strategy_node,
    )
    builder.add_node(
        "validate_strategy",
        validate_strategy_node,
    )
    builder.add_node(
        "finalize_strategy",
        finalize_strategy_node,
    )

    builder.add_edge(START, "build_actor_case_view")
    builder.add_edge(
        "build_actor_case_view",
        "assess_case_position",
    )
    builder.add_edge(
        "assess_case_position",
        "develop_case_theory",
    )
    builder.add_edge(
        "develop_case_theory",
        "generate_objectives",
    )

    builder.add_edge(
        "generate_objectives",
        "plan_witness_usage",
    )
    builder.add_edge(
        "generate_objectives",
        "plan_evidence_usage",
    )
    builder.add_edge(
        "generate_objectives",
        "anticipate_opponent",
    )

    builder.add_edge(
        [
            "plan_witness_usage",
            "plan_evidence_usage",
            "anticipate_opponent",
        ],
        "rank_strategy",
    )

    builder.add_edge("rank_strategy", "validate_strategy")

    builder.add_conditional_edges(
        "validate_strategy",
        route_strategy_validation,
        {
            "valid": "finalize_strategy",
            "revise": "generate_objectives",
        },
    )

    builder.add_edge("finalize_strategy", END)

    return builder.compile()
```

---

# 6. Strategy Node Objectives

## 6.1 `build_actor_case_view`

### Goal

Give each lawyer only the information available to that side.

### Prosecution view

* Its witnesses’ private profiles.
* Prosecution evidence.
* Disclosed defense evidence.
* Public case information.
* Opposing witness information permitted by the case.

### Defense view

The corresponding defense-specific projection.

This is where access control occurs. Do not depend on prompt instructions such as “do not use hidden information.”

---

## 6.2 `assess_case_position`

### Goal

Create an element-by-element assessment.

### Output

```text
Element: Identity
Current strength: Weak
Supporting evidence: W-01 identification
Contrary evidence: Poor lighting, inconsistent description
Primary risk: Credibility collapse
```

This is an analytical step, not yet a strategy.

---

## 6.3 `develop_case_theory`

### Goal

Create the coherent narrative the party will attempt to prove.

### Output

```text
Primary theory
Alternative theory
Core theme
Required conclusions
Dangerous facts
Facts requiring explanation
```

A case theory should not merely summarize facts. It should connect:

```text
Legal elements
    +
Material facts
    +
Evidence
    +
Credibility arguments
    =
Desired conclusion
```

---

## 6.4 `generate_strategic_objectives`

### Goal

Convert the theory into measurable objectives.

Example:

```json
{
  "objective_id": "OBJ-DEF-IDENTITY-01",
  "description": "Undermine eyewitness identification",
  "target_element_ids": ["ELEMENT-IDENTITY"],
  "priority": 0.94,
  "preconditions": [
    "W-01 testifies to identification"
  ],
  "success_signals": [
    "witness admits poor visibility",
    "witness admits prior uncertainty"
  ],
  "failure_signals": [
    "witness provides confident corroborated identification"
  ],
  "status": "planned"
}
```

---

## 6.5 `plan_witness_usage`

### Goal

Decide:

* Which witnesses to call.
* Why each witness is needed.
* Which objectives each witness serves.
* Witness order.
* Direct examination topics.
* Expected cross-examination risks.
* Whether a witness should be omitted.

The output should replace your current basic witness queue generation.

The queue should be a result of legal objectives, not simply available witnesses.

---

## 6.6 `plan_evidence_usage`

### Goal

Determine:

* Which evidence should be introduced.
* Through which witness.
* What foundation is required.
* Which fact and element it supports.
* When it should be introduced.
* What objections are expected.
* What fallback exists if excluded.

---

## 6.7 `anticipate_opponent`

### Goal

Create a limited opponent model.

It should predict:

* Likely opposing theory.
* Likely attacks.
* Dangerous contradictions.
* Expected objections.
* Evidence the opponent may use.
* Possible alternative narratives.

This does not need deep recursive simulation yet.

---

## 6.8 `rank_strategy`

### Goal

Rank objectives and plans by:

* Legal importance.
* Evidence strength.
* Feasibility.
* Risk.
* Dependency.
* Expected impact.
* Cost.
* Opponent response.

---

## 6.9 `validate_strategy`

### Goal

Reject strategies that:

* Depend on evidence the actor cannot access.
* Require witnesses who lack personal knowledge.
* Depend on nonexistent facts.
* Conflict with legal elements.
* Cannot procedurally be performed.
* Contradict the party’s own theory.
* Contain no observable success criteria.

---

## 6.10 `finalize_strategy`

### Goal

Store the approved strategy graph and initialize objective states.

---

# 7. `finalize_trial_plan`

### Goal

Reconcile the two independently produced strategies into the simulation setup without exposing one private plan to the other.

### Responsibilities

* Create witness schedule rules.
* Determine which side presents first.
* Initialize party-private strategies.
* Initialize shared procedural state.
* Create public versus private strategy storage.
* Record anticipated conflict points for later evaluation.

### Important

Do not merge prosecution and defense strategies into a shared lawyer context.

The evaluator may access both, but each lawyer should only access its own plan and the public trial record.

---

# 8. Opening Phase Graph

Your current opening nodes directly generate statements. Add planning and validation.

```text
START
  ↓
prepare_prosecution_opening
  ↓
execute_prosecution_opening
  ↓
record_prosecution_commitments
  ↓
prepare_defense_opening
  ↓
execute_defense_opening
  ↓
record_defense_commitments
  ↓
validate_openings
  ↓
END
```

## Suggested graph

```python
def build_opening_graph():
    builder = StateGraph(OpeningPhaseState)

    builder.add_node(
        "plan_prosecution_opening",
        plan_prosecution_opening_node,
    )
    builder.add_node(
        "execute_prosecution_opening",
        execute_prosecution_opening_node,
    )
    builder.add_node(
        "record_prosecution_commitments",
        record_opening_commitments_node,
    )

    builder.add_node(
        "plan_defense_opening",
        plan_defense_opening_node,
    )
    builder.add_node(
        "execute_defense_opening",
        execute_defense_opening_node,
    )
    builder.add_node(
        "record_defense_commitments",
        record_opening_commitments_node,
    )

    builder.add_node(
        "validate_openings",
        validate_openings_node,
    )

    builder.add_edge(START, "plan_prosecution_opening")
    builder.add_edge(
        "plan_prosecution_opening",
        "execute_prosecution_opening",
    )
    builder.add_edge(
        "execute_prosecution_opening",
        "record_prosecution_commitments",
    )
    builder.add_edge(
        "record_prosecution_commitments",
        "plan_defense_opening",
    )
    builder.add_edge(
        "plan_defense_opening",
        "execute_defense_opening",
    )
    builder.add_edge(
        "execute_defense_opening",
        "record_defense_commitments",
    )
    builder.add_edge(
        "record_defense_commitments",
        "validate_openings",
    )
    builder.add_edge("validate_openings", END)

    return builder.compile()
```

## Why record commitments?

Openings create promises and themes:

* “The evidence will show…”
* “You will hear…”
* “The prosecution cannot prove…”

These should be stored so closing evaluation can determine:

* Whether promised evidence appeared.
* Whether the theory changed.
* Whether the lawyer failed to address a broken promise.

---

# 9. Witness Selection Node

Your current `select_next_witness` can remain, but it should become objective-driven.

## `select_next_witness`

### Goal

Select the next witness based on the current strategy and actual trial state.

### Inputs

* Remaining witnesses.
* Active strategic objectives.
* Evidence foundation dependencies.
* What previous witnesses established.
* Unexpected testimony.
* Witness availability.
* Procedural order.

### Output

```json
{
  "witness_id": "W-03",
  "calling_side": "prosecution",
  "objectives": [
    "OBJ-PROV-02",
    "OBJ-AUTH-01"
  ],
  "reason": "Needed to authenticate E-04 and establish possession",
  "examination_plan_required": true
}
```

### Difference from V1

The witness order can now change dynamically.

For example:

* A previous witness unexpectedly authenticates an exhibit.
* A planned witness is no longer necessary.
* New testimony creates an urgent rebuttal need.
* The intended foundation failed.

---

# 10. Redesigned Witness Examination Graph

Your existing witness graph is the correct place to focus first.

Current:

```text
ask_question
    ↓
objection_check
    ↓
judge_ruling
    ↓
witness_answer
    ↓
repeat
```

Target:

```text
Prepare examination
        ↓
Select active objective
        ↓
Generate candidate action
        ↓
Validate and select action
        ↓
Realize action as courtroom question
        ↓
Opponent objection decision
        ↓
Judge ruling
        ↓
Witness response
        ↓
Validate witness response
        ↓
Update facts/evidence/contradictions
        ↓
Evaluate objective progress
        ↓
Replan or continue
```

## Full witness graph

```text
START
  ↓
initialize_examination
  ↓
select_examination_objective
  ↓
plan_next_action
  ↓
validate_planned_action
  ├── invalid ────────────────┐
  │                           │
  └── valid                   │
       ↓                      │
generate_question             │
       ↓                      │
opponent_objection_decision   │
       ├── no objection       │
       │       ↓              │
       │   witness_answer     │
       │                      │
       └── objection          │
               ↓              │
          judge_ruling        │
          ├── sustained ──────┘
          ├── overruled ───── witness_answer
          └── rephrase ────── plan_next_action
                                  ↓
                         validate_witness_answer
                                  ↓
                         update_trial_evidence
                                  ↓
                         detect_new_contradictions
                                  ↓
                         assess_objective_progress
                           ┌──────┼────────┐
                           │      │        │
                        continue replan  section done
                           │      │        │
                           └──────┘        ▼
                                     route_examination
                                      ├── cross
                                      ├── redirect
                                      ├── recross
                                      └── witness complete
```

## Suggested graph structure

```python
def build_witness_examination_graph():
    builder = StateGraph(WitnessExaminationState)

    builder.add_node(
        "initialize_examination",
        initialize_examination_node,
    )
    builder.add_node(
        "select_objective",
        select_examination_objective_node,
    )
    builder.add_node(
        "plan_action",
        plan_examination_action_node,
    )
    builder.add_node(
        "validate_action",
        validate_examination_action_node,
    )
    builder.add_node(
        "generate_question",
        generate_question_node,
    )

    builder.add_node(
        "objection_decision",
        opponent_objection_decision_node,
    )
    builder.add_node(
        "judge_ruling",
        judge_ruling_node,
    )

    builder.add_node(
        "witness_answer",
        witness_answer_node,
    )
    builder.add_node(
        "validate_witness_answer",
        validate_witness_answer_node,
    )

    builder.add_node(
        "update_evidence_state",
        update_evidence_state_node,
    )
    builder.add_node(
        "detect_new_contradictions",
        detect_new_contradictions_node,
    )
    builder.add_node(
        "assess_objective_progress",
        assess_objective_progress_node,
    )

    builder.add_node(
        "transition_examination",
        transition_examination_node,
    )
    builder.add_node(
        "finalize_witness",
        finalize_witness_node,
    )

    builder.add_edge(START, "initialize_examination")
    builder.add_edge(
        "initialize_examination",
        "select_objective",
    )
    builder.add_edge("select_objective", "plan_action")
    builder.add_edge("plan_action", "validate_action")

    builder.add_conditional_edges(
        "validate_action",
        route_after_action_validation,
        {
            "valid": "generate_question",
            "replan": "plan_action",
            "objective_complete": "transition_examination",
        },
    )

    builder.add_edge(
        "generate_question",
        "objection_decision",
    )

    builder.add_conditional_edges(
        "objection_decision",
        route_after_objection_decision,
        {
            "no_objection": "witness_answer",
            "object": "judge_ruling",
        },
    )

    builder.add_conditional_edges(
        "judge_ruling",
        route_after_ruling,
        {
            "overruled": "witness_answer",
            "sustained_replan": "plan_action",
            "sustained_rephrase": "generate_question",
        },
    )

    builder.add_edge(
        "witness_answer",
        "validate_witness_answer",
    )

    builder.add_conditional_edges(
        "validate_witness_answer",
        route_after_witness_validation,
        {
            "valid": "update_evidence_state",
            "repair": "witness_answer",
            "flag": "update_evidence_state",
        },
    )

    builder.add_edge(
        "update_evidence_state",
        "detect_new_contradictions",
    )
    builder.add_edge(
        "detect_new_contradictions",
        "assess_objective_progress",
    )

    builder.add_conditional_edges(
        "assess_objective_progress",
        route_after_objective_assessment,
        {
            "continue": "plan_action",
            "change_objective": "select_objective",
            "finish_section": "transition_examination",
        },
    )

    builder.add_conditional_edges(
        "transition_examination",
        route_examination_transition,
        {
            "direct": "select_objective",
            "cross": "select_objective",
            "redirect": "select_objective",
            "recross": "select_objective",
            "complete": "finalize_witness",
        },
    )

    builder.add_edge("finalize_witness", END)

    return builder.compile()
```

---

# 11. Witness Examination Node Objectives

## 11.1 `initialize_examination`

### Goal

Create the examination-specific state.

### Responsibilities

* Load witness knowledge.
* Load examining lawyer’s witness plan.
* Load opposing lawyer’s attack plan.
* Set direct or cross mode.
* Determine available evidence.
* Initialize examination objectives.
* Initialize question history.
* Initialize topic history.
* Initialize contradiction opportunities.

---

## 11.2 `select_objective`

### Goal

Choose what the lawyer is trying to accomplish now.

Examples:

### Direct examination

* Establish witness background.
* Establish opportunity to observe.
* Establish event facts.
* Authenticate evidence.
* Establish damages.
* Explain an apparent inconsistency.

### Cross-examination

* Attack perception.
* Attack memory.
* Expose bias.
* Establish inconsistent statement.
* Obtain favourable admission.
* Limit damaging testimony.
* Support an alternative theory.

### Output

```json
{
  "objective_id": "OBJ-CROSS-04",
  "description": "Establish poor visibility",
  "target_fact_ids": ["F-12", "F-13"],
  "success_conditions": [
    "witness admits area was dark",
    "witness admits viewing duration was brief"
  ],
  "priority": 0.91
}
```

---

## 11.3 `plan_action`

### Goal

Choose the legal or tactical action before phrasing the question.

### Candidate action types

```text
establish_foundation
elicit_fact
clarify_answer
control_witness
commit_witness
refresh_recollection
introduce_exhibit
authenticate_exhibit
impeach_with_statement
impeach_with_evidence
expose_bias
challenge_perception
challenge_memory
obtain_admission
repair_credibility
move_to_new_topic
end_examination
```

### Important distinction

This node produces:

```text
What should be done?
```

It does not yet produce:

```text
Exactly what should the lawyer say?
```

---

## 11.4 `validate_action`

### Goal

Reject impossible or strategically unsound actions before generating courtroom language.

### Deterministic checks

* Is the action allowed in this examination type?
* Does the referenced evidence exist?
* Does this side have access to the evidence?
* Is foundation required?
* Has foundation already been established?
* Does the witness have relevant knowledge?
* Was this objective already completed?
* Is the action repetitive?
* Does the action violate a judge ruling?
* Is the target contradiction actually present?

### LLM-assisted checks

* Is the move strategically coherent?
* Does it meaningfully advance the objective?
* Is there a less risky alternative?
* Is this the right moment?

---

## 11.5 `generate_question`

### Goal

Translate the selected action into courtroom language.

### Input

```text
ExecutionBrief
 ├── action_type
 ├── objective
 ├── target_facts
 ├── target_evidence
 ├── expected_answer
 ├── examination_type
 ├── question constraints
 └── previous question and answer
```

### Output

```json
{
  "spoken_text": "The parking area had no functioning streetlights, correct?",
  "action_type": "challenge_perception",
  "objective_id": "OBJ-CROSS-04",
  "target_fact_ids": ["F-12"],
  "expected_answer_shape": "yes_or_no"
}
```

Your current `ask_question_node` can evolve into this node, but it should no longer decide the complete strategy internally.

---

## 11.6 `objection_decision`

### Goal

Let opposing counsel decide whether an objection is strategically and legally appropriate.

Do not automatically object whenever a possible defect exists.

The agent should consider:

* Is there a valid legal ground?
* Is the issue material?
* Would objecting highlight harmful testimony?
* Is the defect curable by rephrasing?
* Would silence be strategically better?
* Has the judge already warned counsel?

### Output

```json
{
  "decision": "object",
  "ground": "leading",
  "confidence": 0.87,
  "strategic_reason": "Question supplies a disputed fact on direct"
}
```

---

## 11.7 `judge_ruling`

### Goal

Apply the relevant procedural and evidentiary rule to the exact question.

### Input

* Question.
* Objection.
* Examination type.
* Applicable rule.
* Existing foundation.
* Trial record.
* Prior rulings.

### Output

```json
{
  "ruling": "sustained",
  "reason": "Leading question on direct examination",
  "remedy": "rephrase",
  "evidence_effect": null
}
```

The Procedure Controller then enforces the ruling. The judge does not directly choose arbitrary next nodes.

---

## 11.8 `witness_answer`

### Goal

Generate an answer solely from the witness’s permitted knowledge, memory and behaviour.

### Input

The Witness Agent should receive:

* Current question.
* Personally known facts.
* Prior statements.
* Already-given testimony.
* Memory strength.
* Confidence.
* Bias.
* Emotional state.
* Judge instructions.

It should not receive the complete Case Graph.

---

## 11.9 `validate_witness_answer`

### Goal

Detect witness simulation failures before they corrupt the trial state.

### Check

* Did the witness reveal hidden facts?
* Did the witness claim knowledge they do not possess?
* Did the answer contradict established ground truth?
* Is a contradiction intentional and supported by the profile?
* Did the witness answer a question that was sustained?
* Is the answer responsive?
* Did the model invent evidence?
* Did the witness’s confidence exceed its profile?

### Routing

* `valid`: accept.
* `repair`: regenerate because of simulation failure.
* `flag`: accept as testimony but record a genuine contradiction.

This distinction is critical:

```text
Model hallucination ≠ witness contradiction
```

---

## 11.10 `update_evidence_state`

### Goal

Translate the question and answer into structured trial-state changes.

Possible updates:

* Fact established.
* Fact weakened.
* Evidence authenticated.
* Foundation partially completed.
* Evidence offered.
* Evidence admitted.
* Credibility increased.
* Credibility decreased.
* Admission obtained.
* Prior statement established.
* New disputed claim introduced.

---

## 11.11 `detect_new_contradictions`

### Goal

Compare new testimony against:

* Prior testimony.
* Prior statements.
* Documents.
* Other witnesses.
* Timeline.
* Party theory.
* Opening commitments.

### Output

```json
{
  "contradiction_id": "C-19",
  "statement_a_turn_id": "T-42",
  "statement_b_id": "S-04",
  "type": "witness_prior_statement",
  "materiality": 0.88,
  "discoverable_by": ["defense"],
  "status": "available_for_impeachment"
}
```

---

## 11.12 `assess_objective_progress`

### Goal

Determine whether the current objective was achieved, failed or requires adaptation.

### Output

```text
Objective status:
- completed
- partially_completed
- blocked
- failed
- abandoned
- superseded
```

### Example

```text
Objective:
Establish poor lighting.

Progress:
Completed.

Evidence:
Witness admitted no streetlights and a viewing period below five seconds.

Next recommended objective:
Establish prior uncertainty.
```

This node is what prevents the examination from becoming a sequence of loosely related generated questions.

---

## 11.13 `transition_examination`

### Goal

Deterministically move between:

```text
Direct
  ↓
Cross
  ↓
Redirect
  ↓
Recross
  ↓
Witness complete
```

Redirect and recross should be conditional, not mandatory.

Examples:

* No redirect when cross produced no material damage.
* Redirect limited to subjects raised on cross.
* Recross limited to new matters raised on redirect.

---

## 11.14 `finalize_witness`

### Goal

Create a structured summary of what the witness actually contributed.

### Output

```text
WitnessResult
 ├── facts_established
 ├── facts_weakened
 ├── evidence_authenticated
 ├── evidence_admitted
 ├── credibility_changes
 ├── contradictions_created
 ├── contradictions_exploited
 ├── objectives_completed
 ├── objectives_failed
 └── unresolved_opportunities
```

This structured result is more valuable than a prose transcript summary.

---

# 12. `update_trial_position`

### Goal

Update both parties’ strategy after each witness.

This node is separate from witness examination because it assesses the impact on the complete case.

```text
Witness result
      ↓
Update element support
      ↓
Update prosecution position
      ↓
Update defense position
      ↓
Reprioritize objectives
      ↓
Modify remaining witness/evidence plan
```

### Responsibilities

* Update each legal element’s strength.
* Complete or fail objectives.
* Add newly discovered objectives.
* Reorder remaining witnesses.
* Remove unnecessary witnesses.
* Add rebuttal needs.
* Track fulfilled and broken opening promises.
* Update expected verdict sensitivity.

### Important

This is not a full strategy regeneration after every answer.

Run it:

* After each witness.
* After major evidence rulings.
* After serious unexpected testimony.
* Before closings.

---

# 13. Replace `summarize_trial_transcript`

Your existing `summarize_trial_transcript` should become `prepare_closing_record`.

A generic prose summary loses important legal structure.

## `prepare_closing_record`

### Goal

Build the exact record the lawyers and judge need for closings and verdict.

### Output

```text
ClosingRecord
 ├── admitted_evidence
 ├── excluded_evidence
 ├── established_facts
 ├── contested_facts
 ├── element_support_matrix
 ├── witness_credibility_findings
 ├── unresolved_contradictions
 ├── opening_commitments
 ├── completed_objectives
 ├── failed_objectives
 └── important_transcript_turns
```

The lawyers receive party-specific versions.

The judge receives only the legally permitted record.

The evaluator receives the complete record.

---

# 14. Closing Graph

```text
START
  ├───────────────┐
  ▼               ▼
assess_prosecution_position
                  assess_defense_position
  ▼               ▼
plan_prosecution_closing
                  plan_defense_closing
  │               │
  └───────┬───────┘
          ▼
execute_prosecution_closing
          ↓
execute_defense_closing
          ↓
optional_prosecution_rebuttal
          ↓
validate_closing_arguments
          ↓
END
```

The planning steps can run from private party views, but spoken closings remain procedurally ordered.

## Closing planner goal

Determine:

* Which elements are satisfied.
* Which weaknesses must be explained.
* Which contradictions matter most.
* Which evidence can legally be discussed.
* Which opponent theory must be attacked.
* Which opening promises were fulfilled.
* What conclusion should be requested.

## Closing validation

Check that counsel did not:

* Rely on excluded evidence.
* Invent testimony.
* Misstate an admitted exhibit.
* Refer to hidden strategy.
* Contradict its own theory without explanation.
* Ignore a required legal element.
* Misstate the applicable burden.

---

# 15. Judicial Deliberation Graph

Do not pass the transcript to a single verdict prompt.

```text
START
  ↓
build_judge_record
  ↓
identify_required_legal_questions
  ↓
evaluate_evidence_by_element
  ↓
assess_witness_credibility
  ↓
apply_burden_and_standard
  ↓
generate_candidate_findings
  ↓
challenge_candidate_findings
  ↓
finalize_findings
  ↓
generate_verdict
  ↓
validate_verdict
  ↓
END
```

## Suggested graph

```python
def build_judicial_deliberation_graph():
    builder = StateGraph(JudicialState)

    builder.add_node(
        "build_judge_record",
        build_judge_record_node,
    )
    builder.add_node(
        "identify_legal_questions",
        identify_legal_questions_node,
    )
    builder.add_node(
        "evaluate_elements",
        evaluate_elements_node,
    )
    builder.add_node(
        "assess_credibility",
        assess_witness_credibility_node,
    )
    builder.add_node(
        "apply_burden",
        apply_burden_node,
    )
    builder.add_node(
        "generate_findings",
        generate_candidate_findings_node,
    )
    builder.add_node(
        "challenge_findings",
        challenge_candidate_findings_node,
    )
    builder.add_node(
        "finalize_findings",
        finalize_findings_node,
    )
    builder.add_node(
        "generate_verdict",
        generate_verdict_node,
    )
    builder.add_node(
        "validate_verdict",
        validate_verdict_node,
    )

    builder.add_edge(START, "build_judge_record")
    builder.add_edge(
        "build_judge_record",
        "identify_legal_questions",
    )

    builder.add_edge(
        "identify_legal_questions",
        "evaluate_elements",
    )
    builder.add_edge(
        "identify_legal_questions",
        "assess_credibility",
    )

    builder.add_edge(
        ["evaluate_elements", "assess_credibility"],
        "apply_burden",
    )

    builder.add_edge("apply_burden", "generate_findings")
    builder.add_edge(
        "generate_findings",
        "challenge_findings",
    )

    builder.add_conditional_edges(
        "challenge_findings",
        route_findings_review,
        {
            "accept": "finalize_findings",
            "revise": "generate_findings",
        },
    )

    builder.add_edge(
        "finalize_findings",
        "generate_verdict",
    )
    builder.add_edge(
        "generate_verdict",
        "validate_verdict",
    )

    builder.add_conditional_edges(
        "validate_verdict",
        route_verdict_validation,
        {
            "valid": END,
            "revise_findings": "generate_findings",
        },
    )

    return builder.compile()
```

## Key output

The verdict should be generated from structured findings:

```text
Element 1:
Proved / not proved
Supporting evidence
Contrary evidence
Credibility treatment
Applied standard

Element 2:
Proved / not proved
...

Final legal consequence:
Verdict
```

---

# 16. Evaluation Graph

Evaluation should run after the trial, but lightweight event capture occurs throughout.

```text
START
  ↓
run_deterministic_checks
  ├────────────┬─────────────┬──────────────┐
  ▼            ▼             ▼              ▼
evaluate     evaluate      evaluate       evaluate
prosecution  defense       witnesses      judge
  └────────────┴─────────────┴──────────────┘
                       ↓
evaluate_simulation_quality
                       ↓
detect_missed_opportunities
                       ↓
compare_counterfactual_actions
                       ↓
aggregate_evaluation
                       ↓
calibrate_confidence
                       ↓
END
```

## Suggested graph

```python
def build_evaluation_graph():
    builder = StateGraph(EvaluationState)

    builder.add_node(
        "deterministic_checks",
        deterministic_checks_node,
    )

    builder.add_node(
        "evaluate_prosecution",
        evaluate_prosecution_node,
    )
    builder.add_node(
        "evaluate_defense",
        evaluate_defense_node,
    )
    builder.add_node(
        "evaluate_witnesses",
        evaluate_witnesses_node,
    )
    builder.add_node(
        "evaluate_judge",
        evaluate_judge_node,
    )

    builder.add_node(
        "evaluate_simulation",
        evaluate_simulation_node,
    )
    builder.add_node(
        "detect_missed_opportunities",
        detect_missed_opportunities_node,
    )
    builder.add_node(
        "compare_alternatives",
        compare_counterfactual_actions_node,
    )
    builder.add_node(
        "aggregate_evaluation",
        aggregate_evaluation_node,
    )
    builder.add_node(
        "calibrate_confidence",
        calibrate_evaluation_confidence_node,
    )

    builder.add_edge(START, "deterministic_checks")

    builder.add_edge(
        "deterministic_checks",
        "evaluate_prosecution",
    )
    builder.add_edge(
        "deterministic_checks",
        "evaluate_defense",
    )
    builder.add_edge(
        "deterministic_checks",
        "evaluate_witnesses",
    )
    builder.add_edge(
        "deterministic_checks",
        "evaluate_judge",
    )

    builder.add_edge(
        [
            "evaluate_prosecution",
            "evaluate_defense",
            "evaluate_witnesses",
            "evaluate_judge",
        ],
        "evaluate_simulation",
    )

    builder.add_edge(
        "evaluate_simulation",
        "detect_missed_opportunities",
    )
    builder.add_edge(
        "detect_missed_opportunities",
        "compare_alternatives",
    )
    builder.add_edge(
        "compare_alternatives",
        "aggregate_evaluation",
    )
    builder.add_edge(
        "aggregate_evaluation",
        "calibrate_confidence",
    )
    builder.add_edge("calibrate_confidence", END)

    return builder.compile()
```

Independent actor evaluators are a good candidate for parallel execution. Running evaluations independently also avoids one actor’s score influencing another actor’s assessment. LangGraph explicitly supports parallel branches for independent analyses and repeated scoring.

---

# 17. Evaluation Node Goals

## 17.1 `deterministic_checks`

### Goal

Find objectively detectable errors.

Examples:

* Hidden information leak.
* Nonexistent evidence cited.
* Excluded evidence used in verdict.
* Invalid phase transition.
* Witness answered after sustained objection.
* Judge relied on unadmitted evidence.
* Unsupported transcript fact.
* Evidence introduced without required status transition.
* Role spoke out of turn.

No LLM required.

---

## 17.2 `evaluate_prosecution` and `evaluate_defense`

### Goal

Evaluate decision quality separately from language quality.

### Evaluation groups

#### Case strategy

* Theory coherence.
* Element coverage.
* Witness order.
* Evidence plan.
* Risk management.

#### Tactical decisions

* Objective selection.
* Action selection.
* Adaptation.
* Contradiction use.
* Missed opportunities.

#### Execution

* Question quality.
* Witness control.
* Foundation.
* Objections.
* Opening and closing.

---

## 17.3 `evaluate_witnesses`

### Goal

Evaluate whether simulated witnesses behaved consistently with their profiles and knowledge.

This is primarily an AI-system quality evaluation, not an advocacy score.

---

## 17.4 `evaluate_judge`

### Goal

Determine whether rulings, findings and verdict were:

* Based on the permitted record.
* Legally grounded.
* Internally consistent.
* Neutral.
* Supported by element-level findings.

---

## 17.5 `detect_missed_opportunities`

### Goal

Find moments where an available strategic action was materially better than the action taken.

### Process

```text
Reconstruct state at turn N
        ↓
Identify available facts/evidence/actions
        ↓
Inspect active strategy objective
        ↓
Generate best alternatives
        ↓
Compare with actual action
        ↓
Estimate strategic difference
```

Only run this on important moments, not every transcript turn.

Candidate moments:

* A contradiction became available.
* Foundation was completed.
* A damaging admission was made.
* An objection opportunity appeared.
* A witness opened the door to a new topic.
* A required element remained unsupported.
* A lawyer abandoned an unfinished objective.

---

## 17.6 `compare_alternatives`

### Goal

Provide the Stockfish-like comparison.

```text
Actual action:
Changed topic.

Alternative:
Commit witness to current testimony, then use prior statement.

Why alternative is stronger:
It directly attacks the credibility of the only identification witness.

Risk:
Witness may explain the inconsistency.

Expected value:
High.
```

---

## 17.7 `aggregate_evaluation`

### Goal

Combine observations without hiding individual evidence.

The final report should retain:

* Dimension scores.
* Observation severity.
* Transcript citations.
* Graph references.
* Evaluator confidence.
* Deterministic failures.
* Strategic consequences.

---

# 18. Coaching Graph

```text
START
  ↓
select_high_value_learning_moments
  ↓
map_moments_to_skills
  ↓
generate_causal_explanations
  ↓
generate_better_action_sequences
  ↓
generate_example_execution
  ↓
prioritize_feedback
  ↓
build_case_improvement_plan
  ↓
END
```

## Coaching output

For each major mistake:

```text
1. What happened
2. What objective was affected
3. What information was available at that moment
4. Why the chosen action was weak
5. What a stronger action would be
6. Example question or argument
7. Likely response
8. How to recover
```

The coach consumes evaluation observations. It should not independently rescore the entire trial.

---

# 19. Recommended State Separation

Do not put everything directly into one massive `TrialState`.

Use the root state as a collection of references and phase outputs.

```python
class TrialState(BaseModel):
    session: SessionState
    case_file: CaseFile

    case_intelligence: CaseIntelligence
    prosecution_strategy: PartyStrategy
    defense_strategy: PartyStrategy

    procedure: ProcedureState
    trial_record: TrialRecord
    evidence_state: EvidenceState
    objective_state: ObjectiveState

    current_witness: WitnessRuntimeState | None
    latest_witness_result: WitnessResult | None

    judicial_result: JudicialResult | None
    evaluation: TrialEvaluation | None
    coaching: CoachingReport | None

    events: list[CourtroomEvent]
```

Then use specialized subgraph states:

```text
CaseIntelligenceState
CaseStrategyState
OpeningPhaseState
WitnessExaminationState
ClosingPhaseState
JudicialState
EvaluationState
CoachingState
```

This prevents every node from reading and modifying the complete system state.

---

# 20. State Views by Actor

Create explicit state projection functions:

```python
def build_prosecution_view(
    state: TrialState,
) -> LawyerStateView:
    ...

def build_defense_view(
    state: TrialState,
) -> LawyerStateView:
    ...

def build_witness_view(
    state: TrialState,
    witness_id: str,
) -> WitnessStateView:
    ...

def build_judge_view(
    state: TrialState,
) -> JudgeStateView:
    ...

def build_evaluator_view(
    state: TrialState,
) -> EvaluatorStateView:
    ...
```

This is safer than placing the full state in a prompt and telling the model to ignore forbidden fields.

---

# 21. Node Categories

Each node should belong to one of four categories.

## Category A: Deterministic control nodes

Examples:

* `initialize_session`
* `validate_action`
* `transition_examination`
* `update_evidence_state`
* `validate_witness_answer`
* `validate_verdict`
* `persist_learning_trace`

These enforce truth, procedure and application state.

## Category B: Analytical LLM nodes

Examples:

* `develop_case_theory`
* `generate_objectives`
* `assess_case_position`
* `plan_action`
* `evaluate_elements`
* `detect_missed_opportunities`

These produce structured decisions.

## Category C: Generative LLM nodes

Examples:

* `generate_question`
* `execute_opening`
* `witness_answer`
* `execute_closing`
* `generate_verdict_explanation`

These produce human-facing language.

## Category D: Hybrid validator nodes

Examples:

* `validate_strategy`
* `challenge_findings`
* `evaluate_lawyer`
* `compare_alternatives`

These combine deterministic checks with bounded model judgment.

The most important architectural rule is:

> Do not combine analytical and generative responsibilities unless the action is trivial.

---

# 22. Mapping Current Nodes to V2

| Current node                 |            Keep? | V2 replacement                                           |
| ---------------------------- | ---------------: | -------------------------------------------------------- |
| `load_case_template`         |     Yes, renamed | `initialize_session` followed by `analyze_case`          |
| `prosecution_strategy`       |           Expand | Prosecution `case_strategy_graph`                        |
| `defense_strategy`           |           Expand | Defense `case_strategy_graph`                            |
| `build_witness_queue`        |    Replace logic | `finalize_trial_plan` plus dynamic `select_next_witness` |
| `opening_prosecution`        |            Split | Plan, execute and record commitments                     |
| `opening_defense`            |            Split | Plan, execute and record commitments                     |
| `select_next_witness`        | Keep and improve | Objective-driven dynamic selection                       |
| `examine_witness`            |   Major redesign | Structured witness examination subgraph                  |
| `summarize_trial_transcript` |          Replace | `prepare_closing_record`                                 |
| `closing_prosecution`        |            Split | Plan and execute                                         |
| `closing_defense`            |            Split | Plan and execute                                         |
| `verdict`                    |   Major redesign | Judicial deliberation subgraph                           |
| None                         |              Add | Evaluation subgraph                                      |
| None                         |              Add | Coaching subgraph                                        |
| None                         |              Add | Learning trace persistence                               |

---

# 23. Minimum Practical V2 Graph

The complete design above is the target. Do not implement every node immediately.

Your first practical upgrade should be:

```text
initialize_session
        ↓
analyze_case
        ↓
prosecution_strategy
defense_strategy
        ↓
opening phase
        ↓
select witness
        ↓
initialize examination
        ↓
select objective
        ↓
plan action
        ↓
generate question
        ↓
objection and ruling
        ↓
witness answer
        ↓
update evidence and contradiction state
        ↓
assess objective progress
        ↓
repeat
        ↓
prepare closing record
        ↓
closing phase
        ↓
structured judicial deliberation
        ↓
evaluation
```

For the first V2 release, combine some nodes internally:

```text
Case analysis:
- One subgraph.

Strategy:
- One subgraph per side.

Question cycle:
- Planner.
- Question generator.
- Objection/ruling.
- Witness.
- State updater.
- Objective assessor.

Verdict:
- Element evaluator.
- Verdict generator.
- Validator.

Evaluation:
- Deterministic checks.
- Lawyer evaluator.
- Judge evaluator.
- Aggregator.
```

That is enough to create the architectural separation without exploding the implementation scope.

---

# 24. Recommended Implementation Order

## Step 1: Extend the state

Add:

```text
case_intelligence
party_strategies
strategic_objectives
evidence_state
contradiction_state
opening_commitments
courtroom_events
```

Do this before changing prompts.

## Step 2: Introduce structured outputs

Convert your existing strategy calls from free text into:

```text
PartyStrategy
CaseTheory
StrategicObjective
WitnessPlan
EvidencePlan
```

## Step 3: Split question planning from question generation

Replace:

```text
case + history → next question
```

with:

```text
state → objective
objective → action
action → question
```

This is the most valuable immediate architectural change.

## Step 4: Add a deterministic state updater

After every answer, update:

* Facts.
* Evidence.
* Contradictions.
* Objective progress.
* Witness credibility signals.

## Step 5: Replace transcript summary

Produce a structured closing record.

## Step 6: Split verdict into findings and final decision

Do not let the verdict generator discover and decide everything in one call.

## Step 7: Add evaluation after the simulation

Start with:

* Deterministic validation.
* Strategy evaluation.
* Evidence-use evaluation.
* Verdict-support evaluation.
* Missed-opportunity detection.

## Step 8: Add coaching after evaluator quality is acceptable

---

# 25. Reuse for AI vs Human

Once AI-vs-AI uses the architecture, AI-vs-Human requires changing only the action source.

```text
select objective
      ↓
action source router
   ┌─────────────┴─────────────┐
   ▼                           ▼
AI lawyer                   Human lawyer
plan action                 interrupt()
generate question           wait for input
   └─────────────┬─────────────┘
                 ▼
validate action
```

For human participants, the system may still create a hidden reference strategy for evaluation, but it must not force the human to follow that strategy.

LangGraph interrupts can pause execution, persist state and resume through `Command(resume=...)`, making the same graph suitable for human participation. A durable checkpointer and stable `thread_id` are required.

One implementation caution: when an interrupt occurs inside a subgraph invoked from a parent node, code before the interrupt can execute again on resume. Side effects before interrupts therefore need to be idempotent.

---

# 26. Final Recommended Shape

```text
ROOT TRIAL GRAPH
│
├── Case Intelligence Subgraph
│   ├── Claims and elements
│   ├── Evidence graph
│   ├── Timeline
│   ├── Witness knowledge
│   └── Contradictions
│
├── Prosecution Strategy Subgraph
│   ├── Position assessment
│   ├── Case theory
│   ├── Objectives
│   ├── Witness plan
│   └── Evidence plan
│
├── Defense Strategy Subgraph
│   └── Same structure
│
├── Opening Subgraph
│   ├── Plan
│   ├── Execute
│   └── Record commitments
│
├── Witness Loop
│   ├── Select witness
│   ├── Examination Subgraph
│   │   ├── Select objective
│   │   ├── Plan action
│   │   ├── Generate question
│   │   ├── Objection
│   │   ├── Ruling
│   │   ├── Witness answer
│   │   ├── State update
│   │   └── Objective assessment
│   └── Update full trial position
│
├── Closing Subgraph
│   ├── Prepare record
│   ├── Plan
│   └── Execute
│
├── Judicial Deliberation Subgraph
│   ├── Element findings
│   ├── Credibility
│   ├── Burden
│   ├── Finding challenge
│   └── Verdict
│
├── Evaluation Subgraph
│   ├── Deterministic checks
│   ├── Actor evaluations
│   ├── Missed opportunities
│   └── Counterfactual comparison
│
└── Coaching Subgraph
    ├── Learning moments
    ├── Better alternatives
    └── Improvement plan
```

The biggest improvement is not adding more LangGraph nodes by itself.

The improvement comes from making every important courtroom action traceable through:

```text
Legal issue
    ↓
Strategic objective
    ↓
Selected action
    ↓
Generated courtroom language
    ↓
Resulting testimony or ruling
    ↓
Trial-state change
    ↓
Objective progress
    ↓
Evaluation
```

That chain gives you the information required to explain:

> You were trying to undermine identification. Poor lighting was established, but you moved to a different topic before introducing the witness’s earlier uncertainty. As a result, the contradiction remained unused and the identification evidence retained more weight than it should have.

That is the foundation of the Courtroom Intelligence Engine.
