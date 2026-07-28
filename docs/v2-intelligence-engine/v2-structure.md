# How should the Intelligence Engine be separated?

Use a hexagonal or ports-and-adapters architecture.
packages/
└── courtroom-engine/
    ├── pyproject.toml
    ├── src/
    │   └── courtroom_engine/
    │       ├── domain/
    │       │   ├── case/
    │       │   ├── evidence/
    │       │   ├── strategy/
    │       │   ├── procedure/
    │       │   ├── trial/
    │       │   ├── evaluation/
    │       │   └── events/
    │       │
    │       ├── application/
    │       │   ├── case_analysis/
    │       │   ├── planning/
    │       │   ├── examination/
    │       │   ├── deliberation/
    │       │   ├── evaluation/
    │       │   └── coaching/
    │       │
    │       ├── orchestration/
    │       │   ├── trial_graph.py
    │       │   ├── case_graph.py
    │       │   ├── strategy_graph.py
    │       │   ├── witness_graph.py
    │       │   ├── deliberation_graph.py
    │       │   └── evaluation_graph.py
    │       │
    │       ├── policies/
    │       │   ├── access/
    │       │   ├── procedure/
    │       │   ├── evidence/
    │       │   └── model_routing/
    │       │
    │       ├── skills/
    │       │   ├── registry.py
    │       │   ├── global/
    │       │   ├── jurisdiction/
    │       │   ├── role/
    │       │   └── tactical/
    │       │
    │       ├── ports/
    │       │   ├── model.py
    │       │   ├── retrieval.py
    │       │   ├── event_store.py
    │       │   ├── checkpoint.py
    │       │   ├── document_store.py
    │       │   └── observability.py
    │       │
    │       ├── context/
    │       │   ├── assembler.py
    │       │   └── projections.py
    │       │
    │       └── facade.py
    │
    └── tests/
        ├── unit/
        ├── scenario/
        ├── regression/
        └── golden_cases/
