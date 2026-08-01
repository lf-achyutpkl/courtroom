## ADDED Requirements

### Requirement: Studio configures live prompt execution

The V2 Studio AI-vs-AI graph SHALL be constructed with an `OpenAIResponsesPromptExecutor` so that live-prompt graph nodes have an executor.

#### Scenario: Studio graph executes a prompt node

- **WHEN** Studio invokes the AI-vs-AI graph with valid OpenAI runtime configuration
- **THEN** the graph SHALL pass a configured structured prompt executor to each prompt node
