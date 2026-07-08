import {
  getSpeakerLabel,
  type TranscriptData,
} from "@/lib/courtroom";

export function CourtroomNotes({
  currentSpeakerId,
  mode,
  transcript,
}: {
  currentSpeakerId: string | null;
  mode: "audio" | "timeline";
  transcript: TranscriptData;
}) {
  return (
    <div className="panel shrink-0 rounded-[28px] px-5 py-5">
      <p className="text-xs uppercase tracking-[0.35em] text-[var(--muted)]">
        Courtroom Notes
      </p>
      <div className="mt-4 space-y-4">
        <div>
          <p className="text-[0.7rem] uppercase tracking-[0.28em] text-[var(--accent-soft)]">
            Current speaker
          </p>
          <p className="mt-1 text-lg leading-7 text-[var(--foreground)]">
            {currentSpeakerId
              ? getSpeakerLabel(transcript, currentSpeakerId)
              : "No active turn"}
          </p>
        </div>
        <div>
          <p className="text-[0.7rem] uppercase tracking-[0.28em] text-[var(--accent-soft)]">
            Defendant
          </p>
          <p className="mt-1 text-base leading-7 text-[var(--foreground)]">
            {transcript.case_metadata.defendant}
          </p>
        </div>
        <div>
          <p className="text-[0.7rem] uppercase tracking-[0.28em] text-[var(--accent-soft)]">
            Playback source
          </p>
          <p className="mt-1 text-base leading-7 text-[var(--foreground)]">
            {mode === "audio"
              ? "Using generated audio from public/audio."
              : "Running from estimated turn timings until Kokoro output exists."}
          </p>
        </div>
      </div>
    </div>
  );
}
