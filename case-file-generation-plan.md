# Feature Spec: Conversational Case Editor

## 1. Goal

Replace static case-file template selection with a two-column authoring UI: a chat panel (left) where the user describes or refines a case in natural language, and a live card grid (right) showing the structured `CaseFile` — case metadata, witnesses, evidence, disputed facts — which updates in near-real-time as the LLM or the user edits it directly.

This document covers **Phase 1 only**. Phase 2 (version history/undo, PDF/URL import, CourtListener integration) is explicitly out of scope — see Section 8.

---

## 2. Architecture Overview

```
Next.js (apps/web)
   |  useChat (Vercel AI SDK) + selected-card state
   |  streaming HTTP connection, per chat turn
   v
FastAPI (apps/api)
   |  POST /case-files/{id}/messages  -> SSE, AI SDK wire protocol
   |  PATCH/POST/DELETE /case-files/{id}/{card_type}/{card_id} -> plain CRUD, no LLM
   |  in-process import of agent-service graph
   v
agent-service (apps/agent-service)
   |  case_editor_graph: 2-node LangGraph, Postgres-backed checkpointer
   |  node 1: process_edit  (structured decision + DB write)
   |  node 2: narrate       (streamed conversational explanation)
   v
Postgres
   - case_files table            <- single source of truth for structured state
   - langgraph checkpoint tables  <- conversation memory only, keyed by thread_id = case_id
```

**Two fundamentally different flows exist here — do not conflate them:**
- The **chat/LLM path** (`POST /messages`) is for AI-assisted generation/edits.
- The **manual edit path** (`PATCH`/`POST`/`DELETE` on card sub-resources) is plain CRUD, no LLM involved, instant DB write.

Both converge on the same `case_files` row. Neither path is a background job — this is NOT the same async pattern as the multi-minute trial simulation. This is a fast (seconds), synchronous, streamed response.

---

## 3. Data Model

### 3.1 Required schema change before starting

`disputed_facts` currently is `list[str]` with no stable identifier. This MUST change to support card-based addressing:

```python
class DisputedFact(BaseModel):
    fact_id: str   # e.g. "F1", "F2" — stable, never reused after deletion
    text: str
```

`CaseFile.disputed_facts` becomes `list[DisputedFact]`. `WitnessProfile.witness_id` and `Evidence.evidence_id` already provide stable IDs — no change needed there.

### 3.2 Card type taxonomy (must match exactly — used as literal string keys throughout)

```python
class CardType(str, Enum):
    case_metadata = "case_metadata"   # singleton: charge_or_claim, parties, jurisdiction
    witness = "witness"
    evidence = "evidence"
    disputed_fact = "disputed_fact"
```

`case_metadata` is a singleton card — no `card_id` needed/used for it (pass `None` or omit).

### 3.3 process_edit structured output schema

```python
class EditAction(str, Enum):
    full_regenerate = "full_regenerate"
    edit_card = "edit_card"
    add_card = "add_card"
    delete_card = "delete_card"

class CaseEditResult(BaseModel):
    action: EditAction
    card_type: CardType | None = None      # None only when action == full_regenerate
    card_id: str | None = None              # None for case_metadata or full_regenerate
    updated_content: dict | None = None     # shape depends on card_type; None for delete_card
    narration_hint: str = Field(description="1-2 sentence internal note on what changed, feeds the narrate node")
```

This same object is used for BOTH the DB write AND the SSE payload sent to the frontend — do not construct a second, separate response shape.

### 3.4 Postgres tables

```
case_files:
  id (pk)
  status
  case_json (jsonb)     -- the full CaseFile object, always the current truth
  created_at, updated_at

-- LangGraph's Postgres checkpointer creates and manages its own tables.
-- Do not hand-roll a messages table. Do not duplicate chat history into case_files.
```

`thread_id` for the checkpointer = `case_file_id` (as a string). This is the entire mechanism for conversation memory — no custom messages table.

---

## 4. Backend Implementation

### 4.1 Endpoint: `POST /case-files/{id}/messages`

**Request body:**
```json
{
  "message": "make her testimony more evasive",
  "selected_card": { "card_type": "witness", "card_id": "W3" }
}
```
`selected_card` is `null` when nothing is selected.

**Response:** SSE stream conforming to the Vercel AI SDK data stream protocol (`x-vercel-ai-ui-message-stream: v1` header required). Two part types are used:
1. `text-delta` parts — narration tokens, streamed as generated.
2. A `data` part, `id = card_id` (or a fixed id like `"case_metadata"` / `"full_case"` for those action types) — carries the full `CaseEditResult` JSON, sent once, as soon as `process_edit` completes (do NOT wait for narration to finish before sending this).

### 4.2 `case_editor_graph` (LangGraph, in `apps/agent-service`)

Two nodes, linear edge, checkpointed:

```
START -> process_edit -> narrate -> END
```

**`process_edit` node — responsibilities:**
1. Load the CURRENT `case_files.case_json` fresh from Postgres. Never reconstruct state from checkpointer/chat history.
2. Build a structured-output LLM call (see Section 5 for prompt rules) with: full current case JSON, `selected_card` (if present), the user's message.
3. Receive `CaseEditResult`. Validate against the Pydantic schema (reject and retry once on validation failure; do not build an elaborate retry loop for v1).
4. Apply the result to `case_json` **server-side, in Python** — merge, don't trust the LLM's output to represent the whole object except when `action == full_regenerate`:
   - `edit_card`: locate the existing sub-object by `card_type` + `card_id`, replace only that sub-object.
   - `add_card`: generate a new stable id (`W{n+1}`, `E{n+1}`, `F{n+1}` — increment from the current max for that card type) if the LLM didn't supply one; append.
   - `delete_card`: remove the sub-object matching `card_type` + `card_id`.
   - `full_regenerate`: replace the entire `case_json` with `updated_content` (which must itself validate as a full `CaseFile`).
5. Write the merged `case_json` back to Postgres.
6. Pass `CaseEditResult` forward to `narrate`.

**`narrate` node — responsibilities:**
1. Read checkpointer message history for conversational continuity/tone.
2. Generate a short (1-3 sentence) explanation of what changed, using `narration_hint` from the prior node as grounding.
3. Stream this as `text-delta` parts.
4. Does NOT touch `case_json`. Read-only with respect to structured state.

### 4.3 Manual edit endpoints (no LLM, instant DB write)

```
POST /case-files/{case_file_id}/mutations
```
class ManualMutationRequest(BaseModel):
    action: Literal["add_card", "edit_card", "delete_card"]
    card_type: CardType
    card_id: str | None = None
    content: dict | None = None
    expected_revision: int

Examples:
{
  "action": "edit_card",
  "card_type": "case_metadata",
  "card_id": null,
  "content": {
    "case_title": "State v. Caldwell",
    "jurisdiction": "New York"
  },
  "expected_revision": 7
}

Add witness
{
  "action": "add_card",
  "card_type": "witness",
  "card_id": null,
  "content": {
    "name": "Laura Bennett",
    "role": "Forensic accountant",
    "knowledge_scope": "Reviewed selected ledger entries..."
  },
  "expected_revision": 7
}

Delete evidence
{
  "action": "delete_card",
  "card_type": "evidence",
  "card_id": "E3",
  "content": null,
  "expected_revision": 7
}

Response:
{
  "operation": {
    "action": "edit_card",
    "card_type": "case_metadata",
    "card_id": null,
    "updated_content": {
      "...": "..."
    }
  },
  "revision": 8
}

This provides:

one endpoint,
one validation pipeline,
one merge implementation,
one frontend mutation client,
consistent handling for every card type.

I would call it /mutations rather than /cards because metadata is also handled and is not an array card in the same sense.

Why POST rather than PATCH?

PATCH would also be defensible, but this endpoint represents a command with multiple possible actions. POST /mutations communicates that more clearly.


Plain CRUD against `case_json`. Same merge discipline as `process_edit` (never blind-replace the whole object). No LangGraph involvement.

---

## 5. LLM / Prompt Rules for `process_edit`

**Scope determination logic (must be followed exactly):**
- `selected_card` present + request clearly applies to it → `edit_card` targeting that card.
- `selected_card` present + request is CLEARLY about something else (e.g., "add a new witness who contradicts her" while a witness card is selected) → allow the model to create a new card (`add_card`) rather than force-fitting the edit onto the selected card. If the new content naturally implies a reciprocal change to the selected card (e.g., setting its `contradicts` field), that reciprocal change IS in-scope and may be included as part of the same result — but do not let the model wander into unrelated fields on the selected card.
- `selected_card` is `null` + narrow request (references a specific named witness/fact by name) → still prefer `edit_card` over `full_regenerate` if the target is unambiguous from the message text.
- `selected_card` is `null` + broad/whole-case request → `full_regenerate`.

**Hard rules:**
- NEVER modify `ground_truth` as a side effect of any `edit_card`, `add_card`, or `delete_card` action. `ground_truth` may only change via `full_regenerate`, and only when the user's message explicitly references the underlying true story (not just "make it more interesting" applied to a witness).
- NEVER return a full `CaseFile` object for `edit_card`/`add_card`/`delete_card` — `updated_content` for these actions should contain ONLY the sub-object being changed (a single witness, a single evidence item, a single disputed fact), not the whole case.
- Preserve information asymmetry when generating/editing witnesses: a witness's `knowledge_scope` must remain a plausible fragment, not the full `ground_truth`.
- When adding a witness (`add_card`), consider whether it should set `contradicts` pointing at an existing witness — but only when the user's request implies a contradiction; don't invent contradictions unprompted.

Model choice: same as the simulation graph — a fast instruct model (no reasoning/thinking mode needed), higher temperature for `narrate` (natural variation in phrasing), lower/moderate temperature for `process_edit` (consistency in following the scope rules above matters more than variety here).

---

## 6. Frontend Implementation (`apps/web`)

### 6.1 Layout
Two-column page: `ChatPanel` (left), `CardGrid` (right). `CardGrid` renders one card component per entry in the current `CaseFile`: `CaseMetadataCard` (singleton), `WitnessCard[]`, `EvidenceCard[]`, `DisputedFactCard[]`.

### 6.2 Chat integration
- Use Vercel AI SDK's `useChat` with a custom transport pointed at `POST /case-files/{id}/messages`.
- Selected card state (`{card_type, card_id} | null`) lives in local React state (e.g. `useState` at the page level, lifted above both `ChatPanel` and `CardGrid`), NOT inferred from message text. Include it in the request body on every send.
- Register an `onData` handler to receive the `card_update` data part. On receipt, patch ONLY the matching card in local state by `id` — do not refetch the whole case file. Use `full_regenerate` results to replace all local card state at once.

### 6.3 Card selection and editing
- Each card has exactly two actions: **select** (sets the lifted selection state, visually highlights the card, shown back to the user near the chat input e.g. "Editing: Laura Bennett") and **edit** (inline form).
- Manual edits call the plain CRUD endpoints directly (Section 4.3) on blur/save. Update local state optimistically; these are instant, no approval step, no LLM involved.
- AI-driven edits also commit instantly (no approval/preview step in this phase) — the only feedback is the narration text explaining what changed.

### 6.4 Initial load
`GET /case-files/{id}` fetches the full `CaseFile` once on page mount to seed `CardGrid`. All subsequent updates come from `onData` (chat path) or optimistic local updates (manual-edit path) — do not poll or refetch the whole object after every message.

---

## 7. DOs and DON'Ts (checklist)

**DO:**
- Fetch `case_json` fresh from Postgres at the start of every `process_edit` call.
- Merge scoped edits server-side in Python; never trust the LLM to return a complete object for anything but `full_regenerate`.
- Generate stable, incrementing IDs for any new card (`W{n}`, `E{n}`, `F{n}`).
- Keep manual-edit REST endpoints entirely separate from the chat endpoint; both write to the same row.
- Send narration via `text-delta` parts and the structured update via a `data` part reconciled by `id`, in the same response.
- Use `case_file_id` as the LangGraph `thread_id`.
- Validate `CaseEditResult` against its Pydantic schema before writing to DB.
- Always include `selected_card` as explicit metadata on every chat request — never infer scope from message phrasing alone.
- Deletion must handle cross-card references
   When deleting a card, remove references to that card from all relationship fields in the same atomic server-side mutation. This is a server responsibility, not an LLM responsibility. Similarly, define whether evidence or disputed facts can reference witnesses and apply the same cleanup.

**DON'T:**
- Don't let the LLM touch `ground_truth` implicitly during a scoped edit.
- Don't implement version history, undo, or diffing in this phase. No snapshot table.
- Don't implement PDF upload or CourtListener/URL import in this phase. Case creation in this phase is text-only.
- Don't add an approval/preview gate before AI edits commit to the DB.
- Don't reconstruct structured case state from the LangGraph checkpointer — checkpointer is conversation memory only.
- Don't stream the structured card JSON token-by-token; it must arrive as one complete, validated object.
- Don't build a job-queue/polling pattern for this feature — it's a synchronous streamed response, not a background job.
- Don't use Streamlit or any non-React UI toolkit for the frontend.
- Do not use raw dict as the final validation layer
   LLM-facing schema can use discriminated unions so each card receives its correct shape.

---

## 8. Explicitly Out of Scope (Phase 2)

- Version history / revert / diff view (git-like snapshot table)
- PDF upload as a case source
- CourtListener API / URL import as a case source
- Any approval-before-commit UX for AI edits

---

## 9. Acceptance Criteria

1. Creating a case from a short text prompt populates all card types correctly.
2. Selecting a witness card and requesting a persona change updates only that witness — no other card changes.
3. Manually editing a card persists instantly and is reflected in the next chat instruction that references it (proves DB-as-truth).
4. A broad request with no card selected triggers `full_regenerate` and replaces all cards.
5. Selecting a card and requesting something clearly out of scope (e.g., "add a contradicting witness") creates a new card without unrelated changes to the selected one.
6. Reloading the page shows persisted state (survives refresh) — confirms Postgres, not client memory, is authoritative.
7. Returning to a case in a new session resumes with contextual chat memory (confirms checkpointer is working).
