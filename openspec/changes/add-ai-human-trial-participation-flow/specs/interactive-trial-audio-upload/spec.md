## ADDED Requirements

### Requirement: Authorize a scoped participant-audio upload
The API service SHALL issue a short-lived R2 presigned upload authorization only for an active human turn. The authorization SHALL bind to the run and turn object key and state the allowed content type, maximum size, and expiry without exposing R2 credentials.

#### Scenario: Upload authorization for an active turn
- **WHEN** a client requests an upload authorization for its active pending turn
- **THEN** the API returns a scoped, expiring upload URL and required upload metadata for that turn

#### Scenario: Authorization for a stale turn
- **WHEN** a client requests upload authorization for a non-active or completed turn
- **THEN** the API rejects the request and does not authorize an R2 object

### Requirement: Verify and attach an uploaded recording
The API service SHALL verify the expected R2 object exists and meets configured MIME-type and size constraints before marking the participant turn upload complete or enqueueing graph resumption. It SHALL persist object metadata/key rather than audio bytes or base64 content.

#### Scenario: Valid uploaded recording
- **WHEN** the browser uploads a supported recording to its authorized key and submits that turn
- **THEN** the API stores the verified object metadata and queues the turn for resumption

#### Scenario: Missing or invalid upload
- **WHEN** a client submits a turn whose R2 object is missing or violates audio constraints
- **THEN** the API rejects the submission and does not queue graph resumption

### Requirement: Protect participant recording objects
Participant recordings SHALL use private R2 object keys distinct from generated playback audio. Only the API service and workers SHALL access recordings with service credentials after upload; public run responses SHALL not expose a public recording URL.

#### Scenario: Detail response after recording upload
- **WHEN** an uploaded participant recording is represented in a run response
- **THEN** the response exposes no reusable public R2 URL or credential
