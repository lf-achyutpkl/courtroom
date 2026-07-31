# Courtroom Intelligence Engine

## Technical Architecture Blueprint

## 1. North-Star Research Question

> **How do we teach an AI to think like an elite trial lawyer, and how do we teach a human to do the same?**

This should guide every technical and product decision.

The system should not merely generate realistic courtroom dialogue. It should understand:

* What must legally be proved.
* Which facts and evidence support each element.
* Which weaknesses exist in each party’s case.
* Which legal objective matters at the current moment.
* Which action has the best strategic value.
* What the opponent is likely to do next.
* Why one action is better than another.
* How a lawyer’s decision changed the likely outcome.
* What the lawyer should do differently next time.

The long-term product is therefore not a transcript generator.

It is a **legal decision, simulation, evaluation, and training platform**.

---

# 2. Strategic Recommendation

Do not continue evolving V1 into a larger collection of prompts.

Instead, introduce a reusable intelligence layer underneath all three product modes:

```text
AI Simulation
AI vs Human
Human vs Human
        │
        ▼
Courtroom Intelligence Engine
        │
        ├── Case Intelligence
        ├── Legal Knowledge
        ├── Strategy Planning
        ├── Courtroom Execution
        ├── Evaluation
        ├── Coaching
        └── Learning
```

The three modes should differ mainly in **who supplies each courtroom action**.

| Mode           | Prosecution/Plaintiff | Defense     | Witnesses   | Judge       | Evaluation                       |
| -------------- | --------------------- | ----------- | ----------- | ----------- | -------------------------------- |
| AI Simulation  | AI                    | AI          | AI          | AI          | All actors and case              |
| AI vs Human    | Human or AI           | AI or Human | Mostly AI   | AI          | Human performance and simulation |
| Human vs Human | Human                 | Human       | AI or human | AI or human | Both humans and overall trial    |

The underlying case representation, procedural controller, strategy models, evidence tracking, evaluators, and coaching system remain shared.

---

# 3. Core Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                       Product Modes                           │
│  AI Simulation        AI vs Human        Human vs Human      │
└──────────────────────────────┬───────────────────────────────┘
                               │
                     Mode Configuration Layer
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│              Courtroom Session Orchestrator                   │
│                                                              │
│  Procedure Controller  │ Turn Router │ State Manager         │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                Courtroom Intelligence Engine                  │
│                                                              │
│  1. Case Analyzer                                             │
│  2. Legal Knowledge Engine                                    │
│  3. Strategy Planner                                          │
│  4. Role Execution Agents                                     │
│  5. Evaluation Engine                                         │
│  6. Coaching Engine                                           │
│  7. Learning Engine                                           │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                 Shared Intelligence Models                    │
│                                                              │
│ Case Graph       Evidence Graph       Timeline Graph          │
│ Issue Graph      Strategy Graph       Contradiction Graph     │
│ Trial State      Actor Knowledge      Skill Model             │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                    Platform Services                          │
│                                                              │
│ Legal Retrieval │ Model Gateway │ Event Store │ Observability │
│ Evaluation Data │ Expert Labels │ Versioned Jurisdiction Packs│
└──────────────────────────────────────────────────────────────┘
```

The main architectural principle is:

> **LLMs propose decisions. Structured state, procedural rules, evidence provenance, and evaluators control the system.**

---

# 4. Build a Modular Monolith First

Do not begin by creating separate microservices for every engine.

Implement the Courtroom Intelligence Engine as a modular Python application with strongly separated packages:

```text
courtroom_engine/
├── domain/
│   ├── case_models/
│   ├── evidence_models/
│   ├── strategy_models/
│   ├── evaluation_models/
│   └── events/
│
├── case_intelligence/
├── legal_knowledge/
├── planning/
├── procedure/
├── execution/
├── evaluation/
├── coaching/
├── learning/
├── orchestration/
├── persistence/
└── observability/
```

Each module should communicate through typed domain objects rather than formatted prompt strings.

Separate services can be extracted later when evaluation workloads, simulation workloads, or legal retrieval need independent scaling.

---

# 5. Foundational Design Principles

## 5.1 Structured State Before Generated Text

Your current implementation converts the case into text:

```text
CASE FILE
Case title: ...
Disputed facts: ...
Evidence: ...
```

That format can remain as a final prompt-rendering layer, but it should no longer be the system’s source of truth.

The source of truth should be structured:

```text
Case
 ├── Claims and charges
 ├── Legal elements
 ├── Burdens and standards
 ├── Parties
 ├── Material facts
 ├── Disputed facts
 ├── Evidence
 ├── Witness knowledge
 ├── Contradictions
 ├── Procedural status
 └── Strategies
```

Prompts should be generated from these structures only when an LLM needs to make a specific decision.

## 5.2 Separate Legal Decisions from Dialogue Generation

A lawyer agent should not receive the case and immediately generate the next speech.

Instead:

```text
Observe courtroom state
        ↓
Identify current legal objective
        ↓
Generate possible actions
        ↓
Reject invalid actions
        ↓
Score valid actions
        ↓
Choose one action
        ↓
Generate courtroom language
```

The strategic decision and the spoken dialogue are different outputs.

## 5.3 Restrict Information by Role

Every actor must receive a different projection of the same case.

For example:

* A witness sees what that witness personally knows.
* A lawyer sees the party’s files, private strategy and disclosed evidence.
* The opposing lawyer sees only discoverable or revealed material.
* The judge sees the admitted record and permitted submissions.
* The evaluator may see the complete ground-truth case.
* The coach may see both the human’s actions and the ideal strategy.

This prevents witnesses from knowing hidden evidence and prevents judges from deciding based on information never admitted at trial.

## 5.4 Separate Court Procedure from the Judge Agent

The Judge Agent should not control the entire application flow.

Create a deterministic **Procedure Controller** responsible for:

* Current trial phase.
* Whose turn it is.
* Which actions are allowed.
* Whether a witness is under direct or cross-examination.
* Whether an objection is pending.
* Whether evidence has been offered or admitted.
* Whether a phase can be closed.
* Whether the trial can proceed to verdict.

The Judge Agent handles discretionary legal decisions such as rulings and findings. The Procedure Controller enforces application-level state transitions.

## 5.5 Store Decision Records, Not Hidden Reasoning

Do not depend on or persist private model chain-of-thought.

Store structured decision summaries instead:

```json
{
  "objective": "Challenge the witness's identification reliability",
  "selected_action": "cross_examination_question",
  "target_fact_ids": ["fact_12"],
  "target_evidence_ids": ["evidence_07"],
  "expected_effect": "Reduce confidence in nighttime identification",
  "confidence": 0.74
}
```

This provides observability without requiring raw internal reasoning.

---

# 6. Shared Domain Models

## 6.1 Case Graph

The Case Graph represents the complete legal problem.

### Principal node types

* Claim or charge.
* Defense.
* Legal issue.
* Legal element.
* Burden of proof.
* Standard of proof.
* Party.
* Material fact.
* Disputed fact.
* Legal authority.
* Remedy or possible verdict.

### Principal relationships

```text
Claim REQUIRES Element
Fact SUPPORTS Element
Fact CONTRADICTS Element
Defense NEGATES Element
Party BEARS_BURDEN_FOR Claim
Authority DEFINES Element
Evidence SUPPORTS Fact
Witness HAS_KNOWLEDGE_OF Fact
```

This allows the system to answer:

* Which element remains weak?
* What evidence supports it?
* Which witness can establish it?
* Which defense attacks it?
* Which legal issue could determine the outcome?

LegalBench was created with legal professionals and contains 162 tasks covering six categories of legal reasoning, illustrating why “legal reasoning” should be decomposed into capabilities instead of represented by one generic score.

## 6.2 Evidence Graph

Each evidence item should include more than a description.

```text
Evidence
 ├── Identity and type
 ├── Source
 ├── Provenance
 ├── Authenticity status
 ├── Admissibility status
 ├── Foundation requirements
 ├── Chain-of-custody information
 ├── Facts supported
 ├── Facts contradicted
 ├── Reliability
 ├── Revealed-to roles
 └── Transcript references
```

Example relationships:

```text
Evidence A SUPPORTS Fact B
Evidence A CONTRADICTS Statement C
Witness D AUTHENTICATES Evidence A
Evidence A REQUIRES_FOUNDATION_FROM Witness D
Evidence A IMPEACHES Witness E
```

Jurisdiction-specific evidence packs can encode concepts such as personal knowledge, authentication, hearsay and impeachment. For example, the US Federal Rules of Evidence separately address personal knowledge, impeachment, prior statements, hearsay and authentication, demonstrating why admissibility should not be represented by a single Boolean property.

## 6.3 Timeline Graph

The Timeline Graph represents:

* Events.
* Date or time ranges.
* Participants.
* Sources supporting each event.
* Conflicting versions of the same event.
* Confidence.
* Sequence constraints.

It should detect issues such as:

* A witness claiming to be in two locations simultaneously.
* Evidence created before the alleged event.
* A testimony sequence conflicting with a document timestamp.
* Missing periods that require explanation.

## 6.4 Contradiction Graph

A contradiction should be a first-class domain object.

```text
Contradiction
 ├── Statement A
 ├── Statement B
 ├── Contradiction type
 ├── Materiality
 ├── Affected legal element
 ├── Available impeachment source
 ├── Whether it was discoverable
 ├── Whether a lawyer used it
 └── Result of attempting to use it
```

Types might include:

* Witness versus earlier statement.
* Witness versus document.
* Witness versus witness.
* Argument versus admitted fact.
* Timeline inconsistency.
* Internal testimony inconsistency.
* Theory-of-case inconsistency.

## 6.5 Strategy Graph

The Strategy Graph represents the intended path from the current case state to a legal outcome.

```text
Case Theory
    ↓
Strategic Objectives
    ↓
Tactical Objectives
    ↓
Candidate Actions
    ↓
Expected Responses
    ↓
Fallback Actions
```

Each strategy objective should contain:

```text
Objective
 ├── Description
 ├── Target legal element
 ├── Target fact or witness
 ├── Required evidence
 ├── Preconditions
 ├── Candidate tactics
 ├── Expected opponent response
 ├── Success signals
 ├── Failure signals
 ├── Risk
 ├── Priority
 └── Current status
```

Example:

```text
Objective:
Undermine the eyewitness identification.

Prerequisites:
- Establish poor lighting.
- Establish short observation duration.
- Establish witness stress.
- Introduce prior uncertainty.

Candidate tactics:
- Closed leading cross-examination.
- Prior inconsistent statement.
- Demonstrative timeline.
- Expert testimony.

Success signal:
Witness admits limited opportunity to observe.
```

Research on deliberate language-model planning shows that exploring and evaluating multiple candidate reasoning paths can outperform single left-to-right generation on tasks requiring lookahead. This supports using bounded candidate search for important courtroom decisions rather than generating every move directly.

## 6.6 Trial State

The Trial State represents the live courtroom position.

```text
TrialState
 ├── Current phase
 ├── Active actor
 ├── Current witness
 ├── Examination type
 ├── Pending objection
 ├── Admitted evidence
 ├── Excluded evidence
 ├── Established facts
 ├── Contested facts
 ├── Completed objectives
 ├── Open objectives
 ├── Transcript events
 ├── Actor-specific knowledge
 ├── Procedural warnings
 └── Session configuration
```

This is the courtroom equivalent of a chess position.

## 6.7 Skill Model

For human participants, maintain a longitudinal skill model:

```text
AdvocacySkillProfile
 ├── Issue spotting
 ├── Case theory development
 ├── Direct examination
 ├── Cross-examination
 ├── Evidence foundation
 ├── Objection recognition
 ├── Objection response
 ├── Contradiction exploitation
 ├── Witness control
 ├── Adaptability
 ├── Opening statement
 ├── Closing argument
 ├── Procedural knowledge
 └── Ethical and professional conduct
```

Every evaluation should update skill evidence, not simply overwrite a score.

---

# 7. Courtroom Engines

## 7.1 Case Analyzer

### Responsibility

Convert uploaded or manually entered case information into the shared legal structures.

### High-level pipeline

```text
Raw case file
    ↓
Entity and event extraction
    ↓
Claim and defense identification
    ↓
Legal element mapping
    ↓
Fact classification
    ↓
Evidence-to-fact linking
    ↓
Timeline construction
    ↓
Contradiction detection
    ↓
Missing-information analysis
    ↓
Human confirmation
```

### Outputs

* Case Graph.
* Evidence Graph.
* Timeline Graph.
* Initial Contradiction Graph.
* List of unsupported claims.
* List of missing foundation.
* List of unresolved legal issues.
* Case confidence warnings.

### Important recommendation

The Case Analyzer should not silently convert uncertain interpretations into facts.

Each extracted object needs:

```text
source_reference
extraction_confidence
human_verified
model_version
created_at
```

## 7.2 Legal Knowledge Engine

The engine needs versioned **Jurisdiction Packs**.

```text
JurisdictionPack
 ├── Country and court
 ├── Case type
 ├── Effective dates
 ├── Procedural phases
 ├── Allowed courtroom actions
 ├── Evidence rules
 ├── Burdens and standards
 ├── Legal elements
 ├── Authorities
 ├── Role constraints
 ├── Evaluation rubrics
 └── Prompt/rendering configuration
```

This is essential because legal reasoning depends on jurisdiction, applicable authority, procedural posture and legal tradition. Current legal-AI research identifies choosing the correct jurisdictional framework, applying burdens of proof and resolving conflicting legal provisions as separate core challenges.

The Legal Knowledge Engine should support:

* Hybrid keyword and semantic retrieval.
* Authority hierarchy.
* Effective-date filtering.
* Citation verification.
* Source provenance.
* Frozen retrieval snapshots for reproducible simulations.
* Separation of binding authority, persuasive authority and general guidance.

A graph-enhanced retrieval layer may eventually model rules, facts and authorities separately. Recent legal GraphRAG research is exploring hierarchical ontology, fact and rule layers for this reason.

## 7.3 Strategy Planner

The planner should operate at three levels.

### Level 1: Global Case Strategy

Created before trial:

* Theory of the case.
* Required elements.
* Primary and alternative narratives.
* Witness order.
* Evidence presentation order.
* Primary vulnerabilities.
* Anticipated opponent strategy.
* Opening and closing themes.

### Level 2: Phase Strategy

Created or updated for:

* Pretrial preparation.
* Opening statement.
* Direct examination.
* Cross-examination.
* Redirect.
* Objections.
* Closing argument.
* Judicial deliberation.

### Level 3: Tactical Turn Planning

Executed before an important action:

```text
Current state
    ↓
Current objective
    ↓
Candidate actions
    ↓
Constraint filtering
    ↓
Candidate scoring
    ↓
Selected action
    ↓
Execution instruction
```

### Candidate action structure

```json
{
  "action_type": "impeach_with_prior_statement",
  "objective_id": "objective_14",
  "target_actor_id": "witness_03",
  "target_fact_ids": ["fact_09"],
  "evidence_ids": ["statement_04"],
  "preconditions": [
    "witness has given inconsistent testimony",
    "prior statement is available"
  ],
  "expected_result": "reduce witness credibility",
  "risks": [
    "opens door to rehabilitation",
    "prior statement may require foundation"
  ],
  "estimated_value": 0.82
}
```

### Candidate scoring dimensions

* Legal relevance.
* Expected strategic value.
* Evidence support.
* Procedural validity.
* Information value.
* Risk of harmful response.
* Ability to advance the case theory.
* Ability to weaken the opposing theory.
* Cost in time or opportunity.
* Uncertainty.

Do not run expensive search for every simple courtroom utterance.

Use bounded lookahead for:

* Witness selection.
* Witness order.
* Whether to introduce significant evidence.
* High-value cross-examination moments.
* Major objections.
* Whether to pursue an impeachment.
* Closing strategy.
* Judicial findings.

## 7.4 Lawyer Execution Agent

The Lawyer Agent should receive an **Execution Brief**, not the full unrestricted case.

```text
ExecutionBrief
 ├── Current objective
 ├── Selected action type
 ├── Target facts
 ├── Permitted evidence
 ├── Known risks
 ├── Procedural constraints
 ├── Desired answer shape
 ├── Tone
 └── Maximum scope
```

The execution agent converts the decision into:

* A question.
* An objection.
* A response to objection.
* A motion.
* An argument.
* An opening segment.
* A closing segment.

This separation lets you evaluate:

1. Whether the planner selected the right move.
2. Whether the lawyer executed that move well.

A good strategy with badly phrased questions and a poor strategy with eloquent questions are different failure modes.

## 7.5 Witness Agent

The Witness Agent needs its own state machine and memory model.

```text
WitnessState
 ├── Ground-truth experiences
 ├── Personally known facts
 ├── Unknown facts
 ├── Prior statements
 ├── Memory strength
 ├── Confidence
 ├── Bias and motivation
 ├── Emotional state
 ├── Current testimony
 ├── Established inconsistencies
 └── Information revealed
```

The witness response pipeline should be:

```text
Question interpretation
       ↓
Scope and objection check
       ↓
Knowledge retrieval
       ↓
Memory and personality transformation
       ↓
Consistency check
       ↓
Response generation
       ↓
Witness memory update
```

The witness must not invent knowledge merely because the information exists in the Case Graph.

## 7.6 Judge Agent

The Judge Agent should operate in two different roles.

### Trial Judge

Handles:

* Objection rulings.
* Procedural discretion.
* Admissibility decisions.
* Instructions.
* Findings where applicable.

### Evaluation Judge

Evaluates simulation quality and participant performance.

These must be separate agents with separate inputs and prompts.

The Trial Judge should normally see only:

* Admitted evidence.
* Courtroom submissions.
* Applicable legal standards.
* Permitted procedural context.

The Evaluation Judge may receive:

* Complete reference case.
* Hidden facts.
* Strategy expectations.
* Evaluation rubrics.
* Transcript and event history.

## 7.7 Evaluation Engine

The current approach:

```text
Transcript
    ↓
One rubric prompt
    ↓
Six numeric scores
```

should become a multi-stage evaluation pipeline.

```text
Trial events and transcript
        ↓
Deterministic validation
        ↓
Grounding and citation validation
        ↓
Structured performance extraction
        ↓
Specialist evaluators
        ↓
Counterfactual strategy comparison
        ↓
Score aggregation and confidence
        ↓
Human-review routing
```

### Evaluation Layer 1: Deterministic Checks

Examples:

* Was excluded evidence later treated as admitted?
* Did a witness mention facts outside their knowledge?
* Did a lawyer cite evidence that does not exist?
* Was an objection resolved before testimony continued?
* Did the verdict rely on an unproved element?
* Did the judge apply the configured burden?
* Did a role violate its information boundary?

These checks should be code, not LLM judgment.

### Evaluation Layer 2: Grounding Checks

Verify every important evaluator claim against:

* Transcript turn IDs.
* Evidence IDs.
* Fact IDs.
* Legal issue IDs.
* Strategy objective IDs.

An evaluation observation should be invalid when it cannot cite supporting records.

### Evaluation Layer 3: Specialist Evaluators

Use separate evaluators for:

* Legal grounding.
* Procedure.
* Evidence use.
* Strategy.
* Witness examination.
* Objection handling.
* Judicial reasoning.
* Verdict support.
* Role fidelity.
* Coaching relevance.

Avoid asking one model to score every dimension in one call.

### Evaluation Layer 4: Counterfactual Comparison

For significant moments, compare the chosen action against alternative candidates:

```text
Actual action
    versus
Alternative A
Alternative B
Alternative C
```

The evaluator should estimate:

* Which action better advanced the legal objective.
* Which evidence could have been used.
* What risk each action created.
* Whether the opportunity was recoverable.
* Whether the choice materially affected the case.

### Evaluation Layer 5: Aggregation

Each final evaluation should contain:

```text
score
confidence
severity
supporting observations
supporting transcript turns
affected objectives
alternative action
evaluator version
human validation status
```

### Do not rely on a single LLM judge

LLM evaluators can demonstrate position and presentation biases. Evaluation research recommends techniques such as reversing candidate order, balanced rubric permutations, repeated judgments and calibration against human labels.

For important evaluations:

* Hide actor and model identity.
* Randomize answer ordering.
* Run reversed-order pairwise evaluation.
* Use multiple evaluator samples.
* Require supporting citations.
* Allow the evaluator to abstain.
* Send low-confidence or high-impact cases for expert review.

LangSmith currently supports datasets, offline experiments, online evaluators, human review, code evaluators, LLM judges and pairwise comparison. Its recommended feedback loop is to move failing production traces into evaluation datasets, validate fixes offline and redeploy.

---

# 8. Actor-Specific Rubrics

## 8.1 Lawyer Evaluation

Evaluate lawyers across separate capabilities:

* Issue spotting.
* Theory-of-case coherence.
* Objective selection.
* Witness sequencing.
* Question design.
* Evidence foundation.
* Use of admitted evidence.
* Contradiction detection.
* Contradiction exploitation.
* Witness control.
* Objection recognition.
* Objection response.
* Adaptation to unexpected testimony.
* Procedural compliance.
* Opening effectiveness.
* Closing synthesis.
* Ethical and professional conduct.

Every low score should identify an observable event.

Bad feedback:

> Your cross-examination could have been stronger.

Good feedback:

> At turns 42–47, the witness said the parking area was dark but you changed topics before connecting poor lighting to identification reliability. This left Objective `OBJ-ID-04` incomplete. A stronger sequence would establish distance, lighting, observation duration and the witness’s earlier uncertainty before asking for an identification concession.

## 8.2 AI Witness Evaluation

Evaluate:

* Knowledge boundary compliance.
* Consistency with personal experience.
* Consistency with prior statements.
* Appropriate uncertainty.
* Personality stability.
* Responsiveness.
* Resistance to prompt leakage.
* Non-disclosure of hidden facts.
* Realistic memory behaviour.

## 8.3 Human Witness Evaluation

Be careful not to claim that a human is lying based only on model judgment.

Evaluate observable advocacy-related qualities such as:

* Consistency.
* Responsiveness.
* Clarity.
* Scope of answers.
* Handling of uncertainty.
* Alignment with supplied case materials.

## 8.4 Judge Evaluation

Evaluate:

* Neutrality.
* Record-only reasoning.
* Correct legal standard.
* Treatment of burdens.
* Handling of objections.
* Consideration of competing theories.
* Fact-to-element reasoning.
* Evidence-to-fact reasoning.
* Explanation quality.
* Verdict consistency.

## 8.5 Simulation Evaluation

Evaluate the complete trial for:

* Procedural realism.
* Legal issue coverage.
* Evidence coverage.
* Adversarial balance.
* Role separation.
* Contradiction handling.
* Narrative coherence.
* Verdict support.
* Educational usefulness.
* Absence of unsupported facts.

---

# 9. The “Stockfish for Trial Lawyers” Model

The chess analogy is useful, but the engine should not attempt exhaustive legal search.

Map the concepts as follows:

| Chess               | Courtroom system                              |
| ------------------- | --------------------------------------------- |
| Board position      | Trial State                                   |
| Pieces              | Witnesses, evidence and legal issues          |
| Legal moves         | Allowed courtroom actions                     |
| Game objective      | Satisfy or defeat legal elements              |
| Candidate moves     | Questions, objections, evidence and arguments |
| Position evaluator  | Strategy Evaluation Function                  |
| Opponent model      | Opposing Strategy Planner                     |
| Principal variation | Expected sequence of courtroom actions        |
| Blunder             | High-value missed or harmful action           |
| Opening book        | Expert strategy templates                     |
| Endgame table       | Known procedural or evidentiary patterns      |

The system should be capable of saying:

```text
You missed a high-value impeachment opportunity at turn 38.

Why:
The witness stated that the room was brightly lit, but Statement S-04
described the room as “almost completely dark.”

Why it mattered:
The identification depended on the witness having a clear view.

Better sequence:
1. Commit the witness to the current statement.
2. Establish the earlier statement.
3. Confirm the inconsistency.
4. Connect lighting to identification reliability.

Estimated consequence:
The missed contradiction left the prosecution's identification evidence
substantially stronger.
```

This requires five components:

1. A structured courtroom position.
2. A list of available actions.
3. An evaluation function.
4. A limited opponent-response model.
5. Comparison between actual and preferred action sequences.

---

# 10. Coaching Engine

The Coach Engine should not summarize the evaluator output.

It should transform evaluation observations into an educational intervention.

## Coaching pipeline

```text
Evaluation observations
        ↓
Identify important learning moments
        ↓
Map moments to legal skills
        ↓
Reconstruct the courtroom state
        ↓
Compare actual and preferred actions
        ↓
Explain cause and consequence
        ↓
Generate improved alternative
        ↓
Update learner skill model
```

## Coaching output model

```text
CoachingMoment
 ├── Transcript location
 ├── Skill category
 ├── What happened
 ├── Why it mattered
 ├── Missed objective
 ├── Evidence available at that moment
 ├── Better action
 ├── Example wording
 ├── Expected response
 ├── Recovery opportunity
 ├── Severity
 └── Confidence
```

## Coaching levels

### Level 1: Immediate Hint

Used during practice:

> You have a prior inconsistent statement available.

### Level 2: Post-Turn Feedback

> You introduced the document before establishing who created it.

### Level 3: Post-Session Analysis

> Across three witnesses, you repeatedly moved to substantive questions before establishing foundation.

### Level 4: Skill Development Plan

> Your evidence recognition is strong, but foundation and witness control remain inconsistent. The next practice scenario should focus on authenticating documents through a reluctant witness.

The Coach should support both:

* **Outcome coaching:** Did the action improve the case?
* **Technique coaching:** Was the action performed correctly?

---

# 11. Winning Percentage and Verdict Design

Treat these as separate outputs.

## 11.1 Simulated Verdict

The verdict reached by the AI judge in one simulated trial.

## 11.2 Case Strength Assessment

A structured assessment of:

* Elements strongly supported.
* Elements weakly supported.
* Defenses strongly supported.
* Missing evidence.
* Credibility risks.
* Procedural risks.

## 11.3 Scenario Outcome Distribution

Run multiple controlled simulations with different:

* Reasoning seeds.
* Witness behaviour.
* Strategy selections.
* Evidentiary rulings.
* Judge configurations.

Then report:

```text
Under the configured assumptions:
- Plaintiff/prosecution prevailed in 62% of simulations.
- Defense prevailed in 38%.
- The result was most sensitive to eyewitness credibility.
```

This is a simulation distribution, not a real-world legal probability.

## 11.4 Calibrated Case Outcome Probability

Only introduce a real “chance of winning” model when you possess:

* Sufficient real historical cases.
* Jurisdiction-specific outcomes.
* Comparable case features.
* Reliable labels.
* Temporal validation.
* Probability calibration.
* Bias analysis.
* Expert review.

Until then, label the result as:

* Simulated outcome distribution.
* Case strength score.
* Scenario confidence.
* Evidence sufficiency assessment.

Do not present an uncalibrated LLM percentage as a factual prediction.

---

# 12. LangGraph Redesign

LangGraph is suitable for this architecture because it provides state-based orchestration, subgraphs, persistence, streaming and human-interrupt support. Its documentation recommends storing raw state rather than only formatted prompts and decomposing workflows into inspectable steps.

## 12.1 Root Session Graph

```text
START
  ↓
Load Session Configuration
  ↓
Normalize Case
  ↓
Validate Case Graph
  ↓
Load Jurisdiction Pack
  ↓
Retrieve Applicable Law
  ↓
Build Evidence/Timeline/Contradiction Graphs
  ↓
Generate Initial Strategies
  ↓
Initialize Trial State
  ↓
Courtroom Loop
  ↓
Judicial Deliberation
  ↓
Verdict Validation
  ↓
Evaluation
  ↓
Coaching
  ↓
Persist Learning Data
  ↓
END
```

## 12.2 Courtroom Loop

```text
Procedure Controller
        ↓
Determine Active Actor
        ↓
Load Actor-Specific State View
        ↓
Strategy Planner
        ↓
Action Source Router
   ┌──────────────┴──────────────┐
   │                             │
Human Actor                  AI Actor
   │                             │
Interrupt and wait          Execution Agent
   └──────────────┬──────────────┘
                  ↓
Validate Action
                  ↓
Resolve Objection or Response
                  ↓
Update Trial State
                  ↓
Update Graphs and Objectives
                  ↓
Turn-Level Evaluation
                  ↓
Next Procedural State
```

## 12.3 Role Subgraphs

Create reusable subgraphs:

```text
lawyer_subgraph
witness_subgraph
judge_subgraph
jury_subgraph
evaluator_subgraph
coach_subgraph
```

LangGraph subgraphs can retain multi-turn state, and interrupts allow execution to pause for human input and resume from persisted state. This naturally supports AI-vs-human and human-vs-human modes.

## 12.4 Mode Configuration

The graph itself should not be duplicated for each mode.

Use configuration:

```json
{
  "mode": "ai_vs_human",
  "actors": {
    "plaintiff_lawyer": "human",
    "defense_lawyer": "ai",
    "witnesses": "ai",
    "judge": "ai"
  },
  "coaching": {
    "during_trial": false,
    "after_trial": true
  },
  "evaluation_targets": [
    "plaintiff_lawyer",
    "simulation",
    "judge"
  ]
}
```

## 12.5 Persistence

Persist two related representations:

### Current state snapshots

Used for pause, resume and recovery.

### Immutable event stream

Used for evaluation, replay, auditing and learning.

Example events:

```text
CaseNormalized
StrategyCreated
ObjectiveActivated
QuestionAsked
WitnessAnswered
ObjectionRaised
ObjectionRuled
EvidenceOffered
EvidenceAdmitted
ContradictionDetected
ObjectiveCompleted
PhaseChanged
VerdictIssued
EvaluationProduced
CoachFeedbackAccepted
```

LangGraph checkpointers create state snapshots at graph steps and support retrieving historical thread state.

---

# 13. Engine Communication Contracts

Engines should not send each other arbitrary prompt strings.

Use versioned typed contracts.

## Planner input

```text
PlanningRequest
 ├── Session ID
 ├── Actor ID
 ├── Current Trial State
 ├── Actor Knowledge View
 ├── Active Strategy
 ├── Available Actions
 ├── Jurisdiction Constraints
 └── Planning Budget
```

## Planner output

```text
PlanningDecision
 ├── Current Objective
 ├── Candidate Actions
 ├── Selected Action
 ├── Structured Rationale
 ├── Expected Responses
 ├── Risk
 ├── Confidence
 └── Fallback
```

## Execution output

```text
CourtroomAction
 ├── Actor
 ├── Action Type
 ├── Spoken Content
 ├── Target Actor
 ├── Target Evidence
 ├── Target Fact
 ├── Objective
 └── Metadata
```

## Evaluation output

```text
EvaluationObservation
 ├── Evaluated Actor
 ├── Dimension
 ├── Observation
 ├── Transcript References
 ├── Graph References
 ├── Severity
 ├── Score
 ├── Confidence
 └── Recommended Alternative
```

Version every contract so old simulations remain replayable after schemas change.

---

# 14. Production Data and Learning System

## 14.1 Capture Data from the Beginning

Store:

* Normalized case structures.
* Retrieved legal sources.
* Strategy proposals.
* Candidate actions.
* Selected actions.
* Rejected actions and reasons.
* Human actions.
* AI actions.
* Courtroom events.
* Evaluator observations.
* Coach recommendations.
* Human feedback.
* Expert corrections.
* Model, prompt and rubric versions.
* Latency, cost and failure information.

## 14.2 Data Quality Tiers

### Tier 0: Raw Trace

Unreviewed production or synthetic interaction.

### Tier 1: Automatically Validated Trace

Passes schema, grounding and procedural checks.

### Tier 2: Human-Reviewed Trace

Reviewed for realism and obvious errors.

### Tier 3: Expert-Labeled Trace

A qualified legal expert validates strategies, actions and evaluation.

### Tier 4: Golden Trajectory

A high-quality reference trial with approved decision points and alternatives.

Never train a specialized model directly on unfiltered production transcripts.

## 14.3 Learning Artifacts

Convert traces into:

### Demonstrations

```text
State → preferred action
```

### Preference pairs

```text
State + action A + action B → preferred action
```

### Error examples

```text
State + incorrect action → error category and explanation
```

### Counterfactual branches

```text
Actual action versus alternative sequence
```

### Evaluator labels

```text
Transcript event → expert score and observations
```

## 14.4 Active Learning

Send interactions for expert review when:

* Evaluators disagree.
* Confidence is low.
* The action has high strategic impact.
* A new legal issue appears.
* A user disputes feedback.
* The system produces an unusual strategy.
* The outcome changes significantly across simulations.

This concentrates legal-expert time on the most informative cases.

## 14.5 Controlled Improvement Loop

```text
Production traces
      ↓
Automated failure detection
      ↓
Expert review queue
      ↓
Golden examples and preference data
      ↓
Offline experiments
      ↓
Planner/prompt/retrieval update
      ↓
Regression evaluation
      ↓
Controlled deployment
```

Do not allow the production system to rewrite its own core prompts or policies automatically.

Learning should occur through controlled offline releases.

Research such as Reflexion has shown that agents can reuse structured linguistic feedback without immediately updating model weights. This supports an early V3 where validated lessons and memories improve future decisions before fine-tuning is introduced.

---

# 15. Product Evolution

## V2 — Structured Intelligence

### Goal

Move from prompt-only simulation to structured, observable planning.

### Components

* Case Graph.
* Evidence Graph.
* Timeline and Contradiction Graphs.
* Jurisdiction Pack.
* Procedure Controller.
* Role-specific knowledge views.
* Global and turn-level Strategy Planner.
* Structured decision records.
* Deterministic validators.
* Improved transcript generation.

### Models

General-purpose frontier LLMs with structured outputs.

### No fine-tuning yet

The purpose of V2 is to create reliable data structures and traces.

---

## V2.5 — Expert Evaluation and Coaching

### Goal

Make the system useful for professional case analysis and human practice.

### Components

* Actor-specific rubrics.
* Specialist evaluators.
* Citation-grounded observations.
* Missed-opportunity detection.
* Counterfactual action comparison.
* Coaching moments.
* Human skill model.
* Expert review interface.
* Golden evaluation dataset.

---

## V3 — Learning Courtroom System

### Goal

Improve the engine from validated interactions.

### Components

* Active-learning pipeline.
* Expert correction workflow.
* Prompt and policy optimization.
* Retrieval improvement.
* Strategy-template library.
* Reusable validated memories.
* Personalised learner skill tracking.
* Planner ranking model.
* Evaluator calibration.
* Simulation outcome calibration.

At this stage, the system learns mainly through data selection, retrieval, ranking, prompts and policies rather than full model training.

---

## V4 — Domain-Specialized Reasoning Models

### Goal

Develop specialized courtroom intelligence unavailable from generic models.

Possible specialized models:

* Legal issue and element extractor.
* Evidence-to-fact linking model.
* Contradiction detector.
* Tactical action generator.
* Strategy action ranker.
* Witness behaviour model.
* Legal evaluator or reward model.
* Coaching model.
* Jurisdiction-specific legal reasoning model.

Training approaches may include:

* Supervised fine-tuning on expert trajectories.
* Preference optimization using ranked legal actions.
* Distillation from high-cost planner search.
* Process-level reward modelling.
* Simulation-based reinforcement learning.
* Separate specialist models rather than one courtroom model.

Fine-tune only after the evaluation system is trustworthy. Otherwise, the application will optimise toward unreliable labels.

---

# 16. Implementation Phases and Acceptance Gates

## Phase 0 — Domain Definition

### Deliverables

* Select one case type and one jurisdiction.
* Define courtroom phases.
* Define allowed actions.
* Define actor information boundaries.
* Create first expert rubrics.
* Create 20–50 reference cases.
* Define simulation and educational disclaimers.

### Gate

Two legal experts can independently understand and apply the schemas and rubrics.

---

## Phase 1 — Case Intelligence Foundation

### Deliverables

* Case Graph.
* Evidence Graph.
* Timeline Graph.
* Contradiction Graph.
* Case Analyzer.
* Human correction interface.
* Provenance and confidence tracking.

### Gate

Experts agree that the engine correctly represents the important claims, elements, facts and evidence in the reference dataset.

---

## Phase 2 — Procedure and Role Isolation

### Deliverables

* Procedure Controller.
* Allowed-action registry.
* Role-specific state projections.
* Witness knowledge boundaries.
* Evidence admission state.
* Event stream and replay.

### Gate

The system cannot continue through invalid phase transitions or leak hidden information in the reference scenarios.

---

## Phase 3 — Strategy Planner

### Deliverables

* Case theories.
* Global objectives.
* Phase objectives.
* Candidate action generation.
* Constraint filtering.
* Candidate ranking.
* Strategy updates after each important event.

### Gate

Experts prefer planner-selected actions to the V1 prompt-only actions in blind pairwise tests.

---

## Phase 4 — Execution and Shared Modes

### Deliverables

* Lawyer execution agent.
* Witness state model.
* Judge decision agent.
* Human interrupt routing.
* Shared mode configuration.
* AI Simulation mode migrated to new engine.
* AI vs Human prototype.

### Gate

The same root graph runs both AI Simulation and AI-vs-Human without duplicating business logic.

---

## Phase 5 — Evaluation Engine

### Deliverables

* Code validators.
* Specialist evaluators.
* Grounded evaluation observations.
* Judge-bias controls.
* Confidence and abstention.
* Expert-review queue.
* Offline regression suite.

### Gate

Evaluator scores and error categories show acceptable agreement with expert labels.

---

## Phase 6 — Coaching Engine

### Deliverables

* Missed-opportunity detection.
* Alternative-action comparison.
* Turn-level coaching.
* Session-level coaching.
* Skill profiles.
* Practice recommendations.

### Gate

Legal educators rate feedback as specific, correct, actionable and educationally useful.

---

## Phase 7 — Learning System

### Deliverables

* Production trace datasets.
* Data quality tiers.
* Expert correction workflow.
* Active learning.
* Preference pairs.
* Golden trajectories.
* Planner and evaluator optimisation pipeline.

### Gate

New planner versions demonstrate measurable improvement on a frozen test set without introducing regressions in procedure, grounding or fairness.

---

# 17. Validation Metrics

## Case Intelligence

* Element extraction precision and recall.
* Evidence-to-fact linking accuracy.
* Contradiction detection precision and recall.
* Timeline consistency.
* Expert correction rate.
* Unsupported assertion rate.

## Strategy Planner

* Expert preference rate.
* Objective completion rate.
* Evidence utilisation.
* Missed high-value opportunity rate.
* Invalid-action rate.
* Strategy recovery after unexpected testimony.
* Candidate diversity.
* Planning cost and latency.

## Witness Simulation

* Hidden-information leakage.
* Contradiction rate.
* Ground-truth fidelity.
* Persona consistency.
* Appropriate uncertainty.
* Repetition and evasiveness realism.

## Judge

* Correct standard application.
* Record-only verdict rate.
* Ruling consistency.
* Unsupported verdict finding rate.
* Expert agreement.
* Neutrality across actor or model identities.

## Evaluation

* Expert correlation.
* Error-category accuracy.
* Citation correctness.
* Evaluator disagreement.
* Calibration.
* Abstention quality.
* Position-order stability.
* Repeated-run stability.

## Coaching

* Expert usefulness rating.
* User acceptance rate.
* User dispute rate.
* Skill improvement across sessions.
* Reduction in repeated errors.
* Ability to identify the causal decision point.

## Platform

* Simulation completion rate.
* Resume and replay reliability.
* Cost per session.
* Planning latency.
* Evaluation latency.
* Token use by engine.
* Failure rate by model and graph node.

---

# 18. Principal Risks

## 18.1 False Legal Confidence

The system may sound authoritative even when its legal analysis is weak.

### Mitigation

* Require source grounding.
* Expose assumptions.
* Display jurisdiction and effective dates.
* Use uncertainty.
* Permit evaluator abstention.
* Require expert approval for high-impact benchmarks.

## 18.2 Information Leakage

Agents may receive facts they should not know.

### Mitigation

* Role-specific state projections.
* Explicit access-control metadata.
* Automated leakage evaluators.
* Separate public and private memory.

## 18.3 Evaluator Circularity

The same model may generate, evaluate and coach its own output.

### Mitigation

* Separate prompts and contexts.
* Prefer separate model families for important evaluations.
* Use deterministic checks.
* Calibrate against humans.
* Blind actor identity.
* Compare reversed answer orders.

## 18.4 Unrealistic Procedure

The dialogue may sound legal while violating courtroom process.

### Mitigation

* Procedure Controller.
* Jurisdiction Packs.
* Allowed-action registry.
* Procedural unit tests.
* Legal-expert scenario review.

## 18.5 Optimising for Winning Rather Than Legal Quality

A model may learn aggressive tactics that improve simulated outcomes but reduce ethics or realism.

### Mitigation

* Separate strategy effectiveness from professional conduct.
* Include ethical and procedural hard constraints.
* Penalise unsupported or manipulative tactics.
* Include expert review in the reward signal.

## 18.6 Premature Fine-Tuning

Fine-tuning on low-quality synthetic transcripts could reinforce hallucinations and unrealistic behaviour.

### Mitigation

* Build evaluation first.
* Introduce data quality tiers.
* Train only on expert-validated examples.
* Maintain frozen benchmark sets.
* Compare against the general model baseline.

## 18.7 Overreliance on Outcome Scores

A lawyer may make the correct decision but lose because of weak facts.

### Mitigation

Evaluate separately:

* Quality of decision.
* Quality of execution.
* Strength of underlying case.
* Simulated outcome.
* Procedural correctness.

## 18.8 Governance and Auditability

Because this is a high-impact legal system, every recommendation should be traceable to data, configuration and model versions. NIST’s AI Risk Management Framework organises trustworthy-system work around governance, mapping, measurement and management, which is a useful structure for your internal risk process.

---

# 19. Important Anti-Patterns to Avoid

Do not:

* Send the complete case to every agent.
* Generate an entire trial in one LLM call.
* Let the Judge Agent control procedural state.
* Use transcript text as the only application memory.
* Let one evaluator score all actors and dimensions.
* Treat evaluator scores as objective truth.
* expose or persist unrestricted internal chain-of-thought.
* Fine-tune before creating expert labels.
* Present a single simulated result as a real win probability.
* Allow production feedback to modify prompts automatically.
* Build separate engines for each product mode.
* Start with every jurisdiction and case type.
* Build a graph database before proving graph-query requirements.

---

# 20. Recommended First Vertical Slice

Do not rebuild the entire courtroom immediately.

Choose one narrow scenario, such as:

```text
Criminal jury trial
One jurisdiction
Eyewitness identification dispute
Two witnesses
Three evidence items
Direct examination
Cross-examination
Objections
Closing
Verdict
```

Implement the complete intelligence loop:

```text
Case Analyzer
    ↓
Graphs
    ↓
Strategy Planner
    ↓
Courtroom Action
    ↓
State Update
    ↓
Evaluator
    ↓
Missed Opportunity
    ↓
Coaching
```

The first major success criterion should not be:

> The transcript sounds realistic.

It should be:

> The system can identify the legally important objective, choose a defensible action, explain why it selected that action, detect when a lawyer misses a stronger alternative, and ground its feedback in the case record.

Once this works reliably for one narrow scenario, the same engine can expand to more witnesses, evidence types, jurisdictions and case categories.

---

# 21. Final Target Architecture

The finished system should behave as follows:

```text
Case materials
      ↓
Structured legal world model
      ↓
Competing case theories
      ↓
Strategic objectives
      ↓
Candidate courtroom actions
      ↓
Procedurally controlled execution
      ↓
Evidence-grounded state updates
      ↓
Actor-specific evaluation
      ↓
Counterfactual comparison
      ↓
Actionable coaching
      ↓
Expert-validated learning data
      ↓
Improved planners, evaluators and models
```

The main competitive advantage will not be the number of agents.

It will be the quality of the system’s:

1. Legal state representation.
2. Strategic objective model.
3. Courtroom action space.
4. Evaluation function.
5. Expert-labelled learning data.

That is what turns the application from a multi-agent courtroom demonstration into a genuine **Courtroom Intelligence Platform**.
