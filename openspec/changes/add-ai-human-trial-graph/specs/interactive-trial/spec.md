# Interactive Trial Requirements

## ADDED Requirements

### Requirement: Interactive attorney selection
The runtime SHALL support `ai_vs_human` with a selectable prosecution or
defense human attorney, defaulting to defense.

#### Scenario: Defense is the default human side
- **WHEN** an interactive run omits `human_attorney_side`
- **THEN** the graph treats defense as the human attorney

### Requirement: Voice turns
The runtime SHALL interrupt for human attorney speech and transcribe base64
audio through Deepgram before adding a transcript turn.

#### Scenario: A human opening is resumed
- **WHEN** Studio resumes a human opening interrupt with valid base64 audio
- **THEN** the Deepgram transcript is appended as that attorney's opening turn
