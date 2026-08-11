# Review v1 — AI-vs-Human Interactive Trial (branch `feat/ai-vs-human` vs `main`)

Scope: full diff of `feat/ai-vs-human` against `main` (82 files, ~4.3k lines — agent-service
interactive graph, api-service participation API/workers, web-app recording UI, DB migrations)
plus the two uncommitted files (`interactive/graph.py`, `interactive/witness_graph.py`), which
are already staged as a real fix and are reviewed as part of the branch.

This is not a "nice job, minor nits" review. You asked for brutal, and the honest read is: **the
happy path is well designed, but almost nothing that goes wrong on the way to the happy path is
handled.** The architecture docs (`openspec/changes/.../design.md`) are unusually good — they
name real trade-offs and even predict some of the failure modes below in "Risks/Trade-offs" and
then explicitly punt on them ("a future explicit retry flow"). That's fine for a design doc. It's
not fine for the punch list below, several of which are not edge cases — they are the *normal*
failure modes of a browser recording audio, uploading it, and a worker calling three external
services (Postgres, R2, Deepgram) to advance a stateful graph. If this ships as-is, expect trials
to get permanently stuck mid-proceeding on ordinary hiccups (a dropped Redis connection, a Deepgram
timeout, a double-tapped submit button on a phone) with no way for the user or an operator to
recover them except "start a new run."

Findings are grouped by severity, each with a concrete repro and a proposed fix. Part 7 is the
forward-looking architecture section for VAD / TTS / streaming, which you asked for explicitly.

---

## Part 1 — Bugs that will actually bite in normal operation

### 1.1 CRITICAL — A transient enqueue failure on submit permanently strands the run, and the client's own retry can't fix it

`apps/api-service/src/api_service/api/routers/interactive_trials.py:181-201`

```python
stored_turn, enqueue = runs.submit_response(run_id, turn_id, ...)   # commits status="submitted"
...
if enqueue:
    try:
        queue.enqueue_resume(run_id, turn_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Unable to queue participant response.") from exc
```

`submit_response` (`apps/api-service/src/api_service/repositories/interactive_trial_runs.py:186-227`)
commits the turn to `status="submitted"` *before* the router ever tries to enqueue the resume job.
If Redis is briefly unreachable (a redeploy, a network blip — this is not exotic in a
Redis/RQ setup), the enqueue throws, the endpoint correctly returns 503... but the DB now
disagrees with reality: the turn is `submitted`, no job exists to consume it.

The client's natural response to a 503 is to retry the same submit call. But look at the top of
`submit_response`:

```python
if turn.status in {"submitted", "resuming", "consumed"}:
    return _stored_turn(turn), False        # <-- enqueue=False
```

The retry hits this idempotency guard, returns `enqueue=False`, and the router *does not
re-enqueue*. The run is now permanently wedged in `awaiting_human` with a turn that will never be
resumed — no error surfaced to the run's `status`/`error_message`, no way for the user to recover
except abandoning the trial. This is the exact bug the author clearly anticipated for run
*creation* (`create_interactive_trial_run` calls `runs.mark_failed(...)` when `enqueue_initial`
fails) but the same handling was not carried over to `submit_participant_turn`.

**Fix**: on `enqueue_resume` failure, either (a) revert the turn to a re-submittable state so the
idempotency check doesn't block a retry, or (b) call `runs.mark_failed(run_id, ...)` exactly like
the create path does, so the run at least surfaces as failed instead of silently hanging forever.
(a) is preferable — a Redis blip shouldn't kill an otherwise-healthy trial. Add a `queued_at` /
"enqueue attempted" marker so a retry can distinguish "still waiting for the first enqueue" from
"already running," and reconsider making `submit_response` and `enqueue_resume` transactionally
coupled (e.g., an outbox pattern, or an idempotent RQ `enqueue_call` with a deterministic job id
tied to `turn_id` that's safe to call twice) rather than "DB commit, then best-effort enqueue."

### 1.2 HIGH — `mark_running` has no guard against a run already being `running`

`apps/api-service/src/api_service/repositories/interactive_trial_runs.py:113-138`

```python
def mark_running(self, run_id, *, turn_id=None):
    ...
    if run.status in {"completed", "failed"}:
        raise InteractiveTrialStateError(...)
    ...
    run.status = "running"
```

There's no check rejecting (or no-op'ing) re-entry when `run.status == "running"` already. RQ's
default delivery semantics are at-least-once, not exactly-once — a worker crash/restart, a job
visibility-timeout retry, or a manual re-enqueue during an incident can dispatch `run_initial` or
`resume_turn` for the same run twice. Both invocations pass the row-lock in `_locked_run`
sequentially (fine), but neither sees a state that stops it from calling `_execute(...)` — i.e.
invoking the same LangGraph `thread_id` — a second time. Two concurrent `graph.invoke()` calls
against the same Postgres-checkpointed thread is exactly the kind of thing that produces corrupted
or duplicated checkpoints and non-deterministic transcript ordering, and it would be very hard to
diagnose after the fact because nothing here logs or rejects it.

**Fix**: treat `"running"` as a guarded state the same way `"completed"/"failed"` are — either
reject re-entry with `InteractiveTrialStateError` (and let the caller no-op, as `run_initial`
partially attempts by checking status before calling `mark_running`, but that check-then-act has a
TOCTOU gap since it's not done under the same lock) or use a dedicated `"resuming"`-style
compare-and-swap so only one job can hold the "currently executing this thread" state at a time.

### 1.3 HIGH — Any transient failure during a resume (Deepgram hiccup, R2 blip, checkpointer reconnect) permanently kills the entire trial

`apps/api-service/src/api_service/jobs/interactive_trials.py:44-48` and `:87-92`

```python
except Exception:
    runs.mark_failed(identifier, "Participant response could not be processed. Please start a new run.")
    raise
```

Every exception in `run_initial`/`resume_turn` — a Deepgram 5xx, a momentary R2 timeout on
`download_private_bytes`, a Postgres checkpointer reconnect blip, an OpenAI rate limit inside one
of the AI attorney nodes — terminalizes the *entire trial* with "start a new run." There is no
retry, no backoff, no distinction between "this is unrecoverable" (bad audio, invalid state) and
"this is a network hiccup that will succeed on the next attempt." For a product whose entire
interaction model is "record your voice, upload it, wait," transient failures are not rare —
they're the median case on a flaky conference-room wifi. The design doc even names this exact risk
("Deepgram or graph failure after an upload") and defers the fix to "a future explicit retry
flow." Given this is explicitly the foundation for a longer-lived product, I'd push back on
deferring it: losing an entire in-progress trial (openings done, three witnesses examined) because
Deepgram timed out once is a bad enough experience that it will dominate early user feedback.

**Fix, minimum bar**: configure RQ retry with backoff (`rq.Retry(max=3, interval=[10, 30, 60])`)
for both jobs, and only call `mark_failed` on the final attempt. **Better**: distinguish retryable
errors (network/timeout/5xx from Deepgram or R2) from terminal ones (bad payload shape, missing
witness) with a typed exception, and only mark the run failed for the latter.

### 1.4 MEDIUM — Dead, confusingly-wired branch in the shared AI-vs-AI witness node

`apps/agent-service/src/utils/nodes.py` (diff vs `main`):

```python
from ..interactive.witness_graph import build_ai_human_witness_graph
...
_ai_human_witness_graph = build_ai_human_witness_graph()
...
def examine_witness_node(state: TrialState) -> WitnessExaminationUpdate:
    ...
    witness_graph = (
        _ai_human_witness_graph if state.trial_mode == "ai_vs_human" else _witness_graph
    )
    result = witness_graph.invoke(witness_state)
```

This is `utils/nodes.py::examine_witness_node`, wired only into the **AI-vs-AI** graph builder
(`utils/graph.py:30`). But `apps/agent-service/src/service.py` (diff) explicitly refuses to run
the AI-vs-AI graph when `trial_mode == "ai_vs_human"`:

```python
if request.trial_mode == "ai_vs_human":
    raise ValueError("AI-vs-human trials require the checkpointed interactive runtime. ...")
```

So `state.trial_mode == "ai_vs_human"` can never be true at the point this branch checks it — the
AI-vs-human path uses its own entirely separate graph (`interactive/graph.py`) with its own
`examine_witness_node` (`interactive/witness_graph.py:99`, a different function, same name — see
1.6). This branch is unreachable dead code that (a) adds a spurious import from the shared
AI-vs-AI module into the interactive package, inverting the intended layering ("the agent service
owns only LangGraph invocation," per `docs/service-contract.md`), (b) instantiates an extra
compiled graph (`_ai_human_witness_graph`) at import time for no reason, and (c) will actively
mislead the next person who reads it into thinking this is how human witness examination is
wired. Delete it, or if there's a reason it needs to stay reachable, wire it for real and add a
test that exercises it.

### 1.5 MEDIUM — Presenter silently guesses when the pending-turn `scene` doesn't match a known action

`apps/api-service/src/api_service/presenters/interactive_trials.py:68-72`

```python
action = (
    turn.scene if turn.scene in {"opening", "closing", "question", "objection"} else "question"
)
```

`turn.scene` is derived from the graph's `interrupt["kind"]` (stripped of `human_`) — internal,
but not contractually pinned anywhere as an enum shared between the two services. If a future
graph change introduces a new interrupt `kind` (very plausible once VAD/streaming turns are added
— see Part 7) and the API isn't updated in lockstep, this silently mislabels the turn as
`"question"` instead of surfacing an error. A participant would then see "Ask the witness the next
question" for what might actually be, say, a closing statement — wrong instructions with no error
anywhere in the logs pointing at the mismatch.

**Fix**: raise (or at least log at error level and mark the run failed with a clear message)
instead of silently defaulting. A `Literal` shared between the graph's interrupt `kind` values and
the API's action enum, checked in one place, would remove the need for this guess entirely.

### 1.6 LOW — Two unrelated functions named `examine_witness_node` in the same call graph

`apps/agent-service/src/utils/nodes.py:210` (AI-vs-AI, `TrialState` in / `WitnessExaminationUpdate`
out) and `apps/agent-service/src/interactive/witness_graph.py:99` (AI-vs-human,
`InteractiveTrialState` + `RunnableConfig` in / raw dict out) are different functions with
different signatures and different semantics (the second is specifically a wrapper working around
a duplication bug in reducer-based state merging — see its docstring). Same name, same directory
tree, imported side-by-side into `interactive/graph.py` (`from .witness_graph import
examine_witness_node`) right after a diff that changed which one it imports. This is a
maintenance trap; the next refactor is one bad IDE auto-import away from silently wiring the wrong
one into the wrong graph. Rename one (e.g. `run_ai_human_witness_examination`).

---

## Part 2 — Error handling & resilience (the thing you specifically asked about)

### 2.1 HIGH — Frontend has no in-flight guard on "Start trial" or "Submit" — double-click creates duplicate state

`apps/web-app/components/interactive-trial/interactive-trial-page.tsx:38-44, 45-59`

`create()`'s button is disabled only by `!caseFileId || !witnessPlan.length` — nothing disables it
while the POST is in flight. A double-click (trivially easy on a touch device, or from an
impatient user) fires two `POST /interactive-trial-runs`, each of which creates a brand-new run
row and a brand-new LangGraph thread (no idempotency key on the request). The UI just keeps
whichever response lands last; the other run is silently orphaned, queued, and will run to
completion in the background consuming LLM/Deepgram calls for nothing.

`submit()` has the same problem: the Submit button's `disabled` is driven by `recorderState`
(idle/recording/stopping) and `hasRecording`, not by "is a submit request currently in flight."
`recorderState` never changes during `submit()` — so the button stays clickable for the full
upload-authorize → PUT → submit round trip, and a second click starts a second, fully independent
authorize/upload/submit sequence against the same turn while the first is still pending.

**Fix**: add an explicit `isSubmitting`/`isCreating` boolean, disable the relevant button (and
show a spinner/label change) for the duration of the async call, in addition to the existing
state-derived disabling.

### 2.2 MEDIUM — Polling silently gives up on error instead of telling the user anything

`apps/web-app/components/interactive-trial/interactive-trial-page.tsx:35`

```tsx
const refresh = useCallback(async () => {
  if (!run) return;
  const response = await fetch(`/api/interactive-trial-runs/${run.interactiveTrialRunId}`, { cache: "no-store" });
  if (response.ok) setRun(await response.json());
}, [run]);
```

On a non-OK response (run deleted, API 500, proxy 502) this does nothing — no `message` set, `run`
stays on its last good value, and the 2-second poll (`useEffect` at line 36) just keeps firing
forever. From the user's perspective the trial silently stops progressing with zero explanation.
Given the task's ask is "handle errors gracefully, with proper feedback to user," this is exactly
the kind of gap that matters: add an error branch that surfaces a retry/backoff message, and
consider backing off the poll interval after repeated failures instead of hammering a possibly-down
backend every 2s indefinitely.

### 2.3 MEDIUM — The four Next.js API routes are blind proxies with no error handling

`apps/web-app/app/api/interactive-trial-runs/route.ts` and its three siblings under
`[runId]/...` all follow this shape:

```ts
export async function POST(request: NextRequest) {
  const response = await fetch(buildApiServiceUrl("/interactive-trial-runs"), { ... });
  return NextResponse.json(await response.json(), { status: response.status });
}
```

No `try/catch`, no timeout on the upstream `fetch`. Two concrete failure modes this doesn't
handle:
- **api-service unreachable** (down, DNS failure, connection refused): the `fetch` throws, Next.js
  returns its generic unhandled-exception response (HTML, not JSON) to the browser. The client
  code does `await response.json()` in most places after checking `response.ok`, but a non-2xx
  HTML error body still breaks `.json()` parsing wherever it isn't guarded, and even where it is
  guarded, the resulting `message` is a generic string that gives the user and whoever's
  debugging nothing to go on.
- **api-service returns a non-JSON body** (e.g., a reverse proxy 502/504 in front of it): `await
  response.json()` inside the route handler itself throws, again producing an opaque 500 with no
  structured error for the browser to render.

**Fix**: wrap each proxy in try/catch, return a normalized `{ error: "..." }` JSON envelope with
an appropriate status on failure, and add a request timeout (`AbortSignal.timeout(...)`) so a
hung upstream doesn't hang the Next.js request indefinitely.

### 2.4 MEDIUM — Generic, lossy error messages hide the actual cause everywhere on the frontend

`create()` (`interactive-trial-page.tsx:42`): any non-OK response, whether it's "422: witness plan
invalid" or "503: queue unavailable" or "500: internal error," collapses to the same string:
"Unable to start trial. Check the selected witness plan." — actively misleading when the real
cause has nothing to do with the witness plan. `submit()`'s catch block (line 58) is similarly a
single string for three different failure points (authorization, upload, submit). Worth reading
the actual response body's `detail` (FastAPI's default error shape) and surfacing it, falling back
to a generic message only when the body isn't parseable.

### 2.5 MEDIUM — Presigned upload has no size ceiling — a client can upload arbitrarily large objects to R2 before any size check runs

`apps/api-service/src/api_service/services/storage/r2.py` (`create_private_upload`):

```python
url = self._client.generate_presigned_url(
    "put_object",
    Params={"Bucket": ..., "Key": key, "ContentType": content_type},
    ExpiresIn=expires_in_seconds,
    HttpMethod="PUT",
)
```

`get_interactive_recording_max_bytes()` is only enforced *after* upload, in
`submit_participant_turn`'s `HEAD` check. A presigned `PUT` URL (unlike a presigned POST with
policy conditions) carries no content-length constraint, so within the upload-authorization window
(default 300s) anything — a script, not just the browser recorder — holding that URL can `PUT` an
object of any size to your bucket. It'll get rejected at submit time, but the bytes are already
stored and billed, and nothing here deletes the rejected object. This is a real, low-effort cost/
DoS vector once this endpoint is reachable from the open internet, not just a correctness nit.

**Fix**: either move to presigned POST with a `content-length-range` policy condition (S3-
compatible, R2 supports it), or add a bucket lifecycle rule that expires objects under
`interactive-trial-runs/` after a short TTL regardless of submission outcome, and delete the
object explicitly when `submit_participant_turn` rejects it for size/type.

### 2.6 LOW — Recorder doesn't guarantee the microphone stream stops on navigation/unmount

`apps/web-app/hooks/use-audio-recorder.ts` only calls `stream.getTracks().forEach(track =>
track.stop())` inside `MediaRecorder.onstop`. If the user starts recording and then navigates away
or closes the tab without clicking "Stop," there's no `useEffect` cleanup stopping the active
stream — the mic indicator can stay lit longer than it should. Add a cleanup effect that stops any
live tracks on unmount.

### 2.7 LOW — No client-side recording duration limit or elapsed-time feedback

Nothing bounds how long a user can record before hitting the server's `INTERACTIVE_RECORDING_MAX_BYTES`
(10MB default) — the first feedback the user gets that their answer was too long is a rejected
submit after they've already finished talking and uploaded. A visible timer plus a soft client-side
cutoff (matching the server limit, accounting for the codec bitrate) would turn a late, confusing
rejection into an in-the-moment warning. (The design doc lists "max recording duration" as an open
question — this is where it surfaces as a real UX gap.)

---

## Part 3 — Trust boundary / security (explicitly out of scope per design doc — flagging anyway since this is meant to grow)

The design doc's Non-Goals explicitly exclude authentication/authorization for v1, which is a
reasonable scoping call for a foundation behind an internal demo. Naming it here so it's a
conscious, revisited decision rather than something that quietly ships to production:

- **No auth on any endpoint.** `run_id`/`turn_id` UUIDs are the only "credential." Anyone who
  obtains a run URL (browser history, a shared link, a referrer header, server logs) can read the
  full transcript, submit audio on someone else's behalf, or hijack an in-progress trial.
- **No rate limiting** on run creation, upload-authorization, or submit — combined with 2.5 above,
  an unauthenticated caller can create unbounded runs (each spinning up an LLM-backed LangGraph
  invocation) and unbounded presigned uploads.
- These are fine to defer *if* this stays behind an internal/trusted network for the "foundation"
  phase, but should be a hard gate before this is reachable from the public internet.

---

## Part 4 — Data model

`infra/db/migrations/`

- `pending_turn_id` on `interactive_trial_runs` (006) has no FK to `participant_turns(id)` — every
  other relationship in this schema is FK-enforced; this one relies entirely on application code
  keeping it in sync. Add the FK (nullable, `ON DELETE SET NULL`).
- `participant_turns.scene` (006) is a free-text `VARCHAR NOT NULL` even though every consumer
  treats it as a closed enum (`opening|closing|question|objection`, see 1.5). A `CHECK` constraint
  matching the app-level enum would turn the silent-fallback bug in 1.5 into a loud, immediate
  failure at the source instead of a mislabeled UI three hops downstream.
- Four sequential `ALTER TABLE` migrations (007, 008, 009) each bolt one nullable column onto
  tables from 006, before any of this has shipped to a real environment. Since nothing here is
  deployed yet, there's no cost to squashing these into a clean 006 with the final column list —
  worth doing before merge so the migration history doesn't permanently carry three columns' worth
  of "add nullable column" churn for a feature that was never live in between.

---

## Part 5 — Testing gaps

The tests that exist are fine as far as they go (unit-level, mocked node behavior, straightforward
assertions), but the coverage is concentrated on the parts least likely to break and largely
absent from the parts this review found actual or likely bugs in:

- **No test exercises `build_ai_human_graph` end-to-end.** `test_interactive_witness_graph.py`
  only tests `build_ai_human_witness_graph` in isolation, invoked directly with its *own*
  `InMemorySaver()` at the top level. Production never does that — production invokes the witness
  subgraph nested inside `examine_witness_node` (`interactive/witness_graph.py:96-133`), compiled
  with `checkpointer=None`, relying on LangGraph's config propagation (`CONFIG_KEY_CHECKPOINTER`
  flowing from the parent's task config into the nested `.invoke()` call) to inherit the parent's
  real checkpointer. I traced this through the installed `langgraph` source
  (`pregel/_algo.py:737-739`, `pregel/main.py`) and the mechanism is legitimate and correctly used
  — but it is a non-obvious, easy-to-break pattern with zero integration coverage. One test that
  runs `build_ai_human_graph(checkpointer=InMemorySaver())` through opening → a witness question
  interrupt → resume → an objection interrupt → resume → verdict would lock in the exact behavior
  that a future change (especially the streaming/VAD changes in Part 7) is most likely to break
  silently.
- **No test covers any of the state-machine edge cases in the repository** — the enqueue-failure-
  after-commit path (1.1), concurrent `mark_running` re-entry (1.2), or the idempotent-turn early
  return actually doing the right thing under a real retry.
- **No test covers the RQ job failure paths** (`run_initial`/`resume_turn` catching an exception
  and marking the run failed) — this is the code path most in need of a test given 1.3.
  `apps/api-service/tests/test_interactive_trial_uploads.py` only tests a MIME-normalization
  helper and a schema field; it doesn't touch the jobs or repository at all.
- **Frontend test coverage is a single 15-line smoke test**
  (`interactive-trial-page.test.tsx`) that only checks the "Start trial" button's disabled state.
  Nothing tests `submit()`, `refresh()`, the double-click scenarios in 2.1, the error-message
  paths in 2.2-2.4, or the recorder error states. The other three component tests
  (`participant-turn-card`, `live-proceeding-transcript`, `interactive-trial-verdict`) are
  reasonable presentational tests but cover the least risky code in the feature.

---

## Part 6 — Code quality / maintainability

- **`interactive-trial-page.tsx` is written as dense, largely unformatted single-line JSX**
  (e.g. line 64, 66, 67 are each one enormous line mixing multiple elements, conditionals, and
  handlers). This isn't a style nitpick — it materially hurt this review (diffs against it will be
  unreadable) and it's a strong signal the file was never run through Prettier/`eslint --fix`.
  Given `package.json` already has `lint` wired up, add `format`/`format:check` and run it before
  merge; break this component into the setup form / proceeding view as separate components while
  you're at it — it's currently one component doing case selection, witness planning, polling,
  recording orchestration, and three different submit flows.
- **`apps/agent-service/langgraph.json`** diff shows inconsistent indentation introduced by the
  edit (`"trial"` line loses two spaces of indent relative to its siblings). Harmless to JSON
  parsing, but another sign this branch's diffs weren't run through a formatter — worth a
  `pre-commit`/CI formatting gate if one doesn't already exist for this file type.
- See 1.6 for the duplicate-name `examine_witness_node` issue, which is as much a readability
  problem as a bug risk.

---

## Part 7 — Architecture, with VAD / TTS / streaming specifically in mind

You said this is the foundation and more is coming (VAD for speaker input, TTS for AI
participants in the UI). A few of the decisions in this branch will make that harder than it needs
to be if left as-is; better to name them now while the surface area is still small.

### 7.1 Polling is the wrong transport to keep building on

The current model — client polls `GET /interactive-trial-runs/{id}` every 2s, server projects a
`live_transcript` from the latest persisted checkpoint — works for "record a whole utterance,
upload, wait." It does not extend to VAD or TTS at all:

- **VAD** implies the client needs to tell the server "the human started/stopped speaking" in
  near-real-time, and likely needs server-side signals too (e.g., "the AI attorney is about to
  speak, mute your mic" or barge-in support). A 2-second poll loop has no channel for that.
- **TTS playback for AI participants** implies the client needs to know the moment an AI turn's
  audio is ready, not "sometime in the next 2 seconds." It also implies turns need an audio
  reference, not just text (see 7.3).

You don't need to build streaming now, but I'd treat "replace polling with SSE/WebSocket push from
the API on every `store_progress` write" as the *next* piece of foundation, before VAD/TTS work
starts, rather than layering VAD on top of the poll loop and having to rip it out. The read-model
projection code in `presenters/interactive_trials.py` is already a clean seam to push through a
different transport later — that part's in good shape.

### 7.2 Turn granularity assumes "one big blob per turn"; VAD will want smaller, streamed chunks

The whole pipeline — presigned single-object upload, one R2 key per turn
(`interactive-trial-runs/{run}/turns/{turn}/recording.{ext}`), one Deepgram prerecorded call per
turn — is built around "record everything, then upload one file." VAD-driven interaction usually
wants either continuous streaming ASR (Deepgram's streaming API, not the prerecorded endpoint
currently used in `transcription.py`) or at least short, frequent chunks so the system can react to
pauses. That's a materially different ingestion path (websocket or chunked upload, not a single
presigned `PUT`). Worth deciding explicitly now whether v2 keeps "whole utterance" turns and adds
VAD only as a client-side UX aid (auto-stop recording on silence, still one upload) — which fits
today's architecture with no backend changes — versus true streaming ASR, which doesn't. My
recommendation: scope the first VAD pass as the former (client-side auto-stop-on-silence using the
existing `MediaRecorder` pipeline); it gets most of the UX win without a transport rewrite, and
defer streaming ASR to when/if latency actually demands it.

### 7.3 Transcript turns carry text only — add a nullable audio reference now, before TTS needs it

`TranscriptTurn` (shared type used throughout) and the API's transcript/live-transcript payloads
are text-only. When TTS is added for AI participants, each AI turn will need an audio reference
(R2 key or URL) attached. Retrofitting that onto an existing, already-public
`transcript`/`liveTranscript` response shape later is a breaking or at least awkward additive
change for every existing client. Since the AI-vs-AI simulation pipeline already has a working
generated-audio-per-turn convention (per `docs/service-contract.md`'s references to a TTS
pipeline and R2-backed generated audio), the cheapest move is to add an optional `audio_url`
(or `audio_key`) field to `TranscriptTurn`/the presenter output *now*, nullable and unused until
TTS lands, reusing whatever convention the existing simulation-run TTS pipeline already
established rather than inventing a second one for interactive runs.

### 7.4 No per-run/per-turn correlation id in logs

Right now, diagnosing a failed run means correlating `error_message` (a short user-safe string)
back to worker logs by timestamp guessing. As more moving parts get added (VAD client events, TTS
generation jobs, streaming transport), you'll want every log line touching a run to carry
`run_id`/`turn_id`/`langgraph_thread_id` consistently so a support/debugging flow is "grep this id"
rather than "reconstruct the timeline." Worth setting up now, before there are three more services
in the chain to correlate across.

### 7.5 The typed pending-turn abstraction (`action` kind + context) is a good foundation — keep extending it, don't bypass it

Unlike the items above, this is a compliment with a warning attached. `PendingHumanTurnContextResponse`
(action: opening/closing/question/objection, witness, phase) is a solid, extensible shape — it's
the right place to add e.g. a `speaking` action for VAD-driven turn-taking or an `ai_turn` variant
carrying a TTS audio reference for the frontend to play back automatically. Resist the temptation,
under future time pressure, to have the frontend special-case raw graph state instead of going
through this projection — the design doc is explicit that "the browser never interprets raw
LangGraph state itself," and that boundary is worth defending as the feature set grows.

---

## Part 8 — Priority punch list

If you can only do a subset before calling this mergeable as a foundation:

1. **1.1** — fix the submit-enqueue-failure orphan (silent, permanent stuck state; will happen in
   normal operation, not just under attack).
2. **1.3** — add RQ retry/backoff so transient failures don't nuke entire trials.
3. **2.1** — in-flight guards on Start/Submit to stop double-submit from creating duplicate runs
   and racing turn submissions.
4. **1.2** — guard `mark_running` against duplicate concurrent execution of the same thread.
5. **2.3 / 2.2 / 2.4** — make the Next.js proxy layer and polling loop fail loudly and usefully
   instead of silently/opaquely.
6. **1.4** — delete the dead `ai_vs_human` branch in the shared AI-vs-AI witness node before it
   confuses someone.
7. **Part 5** — add the one integration test that runs the full interactive graph through an
   interrupt/resume cycle; this is the test most likely to catch a real regression as the graph
   evolves toward VAD/TTS.
8. Everything else (Parts 3, 4, 6, 7) — good to schedule deliberately, not blocking, but don't let
   Part 3 (no auth) drift past the point where this is reachable from outside a trusted network.
