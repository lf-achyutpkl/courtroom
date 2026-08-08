import type { RecorderState } from "@/hooks/use-audio-recorder";

type Turn = {
  context: {
    action: "opening" | "closing" | "question" | "objection";
    instruction: string;
    examinationPhase?: string;
    witness?: { name: string; persona: string };
  };
};

export function ParticipantTurnCard({
  turn,
  recorderState,
  hasRecording,
  processing,
  isFinalQuestion,
  onFinalQuestionChange,
  onStart,
  onStop,
  onSubmit,
  onSkip,
  onDiscard,
}: {
  turn: Turn;
  recorderState: RecorderState;
  hasRecording: boolean;
  processing: boolean;
  isFinalQuestion: boolean;
  onFinalQuestionChange: (value: boolean) => void;
  onStart: () => void;
  onStop: () => void;
  onSubmit: () => void;
  onSkip: () => void;
  onDiscard: () => void;
}) {
  const { action, instruction, witness, examinationPhase } = turn.context;
  const label =
    action === "objection"
      ? "objection"
      : action === "question"
        ? "question"
        : `${action} statement`;

  return (
    <aside className="interactive-trial__turn" aria-live="assertive">
      <p className="interactive-trial__eyebrow">Action required</p>
      <h2>
        {action === "question" && witness
          ? `${examinationPhase ?? "Direct"} examination: ${witness.name}`
          : `Your ${action}`}
      </h2>
      {witness && <p>{witness.persona}</p>}
      {processing ? (
        <p className="interactive-trial__processing">
          Response submitted. The court is processing it.
        </p>
      ) : (
        <>
          <p className="interactive-trial__recorder-status">{instruction}</p>
          {action === "question" && (
            <label>
              <input
                type="checkbox"
                checked={isFinalQuestion}
                onChange={(event) => onFinalQuestionChange(event.target.checked)}
              />{" "}
              This is my final question for this examination.
            </label>
          )}
          <div className="interactive-trial__recording-controls">
            <button
              className="interactive-trial__button interactive-trial__button--record"
              onClick={onStart}
              disabled={recorderState !== "idle" || hasRecording}
            >
              Record {label}
            </button>
            <button
              className="interactive-trial__button"
              onClick={onStop}
              disabled={recorderState !== "recording"}
            >
              Stop recording
            </button>
            <button
              className="interactive-trial__button interactive-trial__button--primary"
              onClick={onSubmit}
              disabled={!hasRecording || recorderState !== "idle"}
            >
              Submit {label}
            </button>
            {action === "objection" && (
              <button
                className="interactive-trial__button"
                onClick={onSkip}
                disabled={recorderState === "recording"}
              >
                No objection — continue
              </button>
            )}
          </div>
          {hasRecording && (
            <button
              className="interactive-trial__discard"
              type="button"
              onClick={onDiscard}
            >
              Discard and record again
            </button>
          )}
        </>
      )}
    </aside>
  );
}
