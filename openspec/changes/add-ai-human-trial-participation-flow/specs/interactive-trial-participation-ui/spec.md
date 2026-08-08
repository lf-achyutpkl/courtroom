## ADDED Requirements

### Requirement: Start an AI-vs-human trial from the web app
The web app SHALL provide a dedicated, basic AI-vs-human trial route that lets a user select an available case file and human attorney side, creates the interactive run through its server-side API proxy, and navigates or renders the resulting run state.

#### Scenario: User starts a trial
- **WHEN** a user selects a case file and attorney side and starts the flow
- **THEN** the web app creates the interactive run and shows its queued or running state

### Requirement: Show durable trial progress
The web app SHALL poll the run-detail API while an interactive run is queued, running, or resuming and SHALL render status, available transcript content, terminal result, and failures in a plain accessible interface.

#### Scenario: Graph is processing
- **WHEN** the interactive run is queued or running
- **THEN** the page shows processing state and continues to refresh without enabling an unrelated recording submission

### Requirement: Record, upload, and submit the expected human turn
The web app SHALL enable browser audio recording only when the run reports an active pending human turn. It SHALL obtain upload authorization through its API proxy, upload the recorded `Blob` directly to R2, submit the active turn, and return to progress polling.

#### Scenario: Participant submits recorded speech
- **WHEN** the user records supported audio and submits it for the active turn
- **THEN** the page uploads the recording, queues the resume, and displays that the trial is processing

#### Scenario: Recording unavailable
- **WHEN** microphone permission is denied or browser recording is unsupported
- **THEN** the page clearly reports that the turn cannot be recorded and does not submit an empty response

### Requirement: Keep the initial experience minimal
The participation route SHALL prioritize functional case selection, status, transcript, recorder controls, and error feedback. It SHALL not require timeline playback, waveform rendering, or realtime streaming to complete a trial.

#### Scenario: Pending turn display
- **WHEN** the run awaits the human attorney
- **THEN** the page displays the expected scene and controls necessary to record and submit a response
