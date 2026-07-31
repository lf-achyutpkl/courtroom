# How do we make each LLM call stick to persona and objective?

  Do not represent persona as one prose field: "You are a highly experienced aggressive lawyer..."
  That is weak and difficult to enforce. Break the actor configuration into five separate concepts.

  Role contract
    Defines legal authority and responsibilities.
    class RoleContract(BaseModel):
      role: ActorRole
      responsibilities: list[str]
      allowed_actions: list[ActionType]
      forbidden_actions: list[str]
      information_policy_id: str

    Example
    You are defense trial counsel.

      You may:
      - Ask questions permitted during the current examination.
      - Raise legally supported objections.
      - Use evidence available to the defense.
      - Pursue active defense objectives.

      You must not:
      - Use evaluator-only facts.
      - Invent evidence or testimony.
      - Refer to the private prosecution strategy.
      - Treat excluded evidence as admitted.

  Knowledge boundary
    Defines what the actor can know.
      class ActorKnowledgeView(BaseModel):
        public_case_information: CaseSlice
        private_case_information: CaseSlice
        admitted_trial_information: AdmittedRecord
        unavailable_information_ids: list[str]

  Strategic brief
    Defines what the actor is trying to accomplish.
    class StrategicBrief(BaseModel):
      case_theory_id: str
      active_objective: StrategicObjective
      completed_objectives: list[str]
      blocked_objectives: list[str]
      available_tactics: list[ActionType]

  Behaviour profile
    Especially important for witnesses:
    class BehaviorProfile(BaseModel):
      confidence: float
      cooperativeness: float
      verbosity: float
      evasiveness: float
      anxiety: float
      hostility: float
      memory_reliability: float

  Every node must state one exact responsibility.
  Example for the planner:
    Task:
    Select the next tactical action.

    Do not write the courtroom question.

    Choose one action that advances the active objective using only
    available facts, evidence and permitted procedures.


  Example for the question generator:
  Task:
    Convert the selected action into one courtroom question.

    Do not change the objective.
    Do not select a different strategy.
    Do not include an answer.

  Validate after generation
  Persona adherence should be checked through code:

  LLM output
      ↓
  Schema validation
      ↓
  Access-policy validation
      ↓
  Evidence-reference validation
      ↓
  Procedure validation
      ↓
  Objective-alignment validation
      ↓
  Accept or repair
