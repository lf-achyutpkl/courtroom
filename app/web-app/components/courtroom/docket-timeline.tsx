import {
  getSceneLabel,
  getSpeakerShortName,
  type PlaybackManifestTurn,
  type TranscriptData,
} from "@/lib/courtroom";

export function DocketTimeline({
  currentTurnId,
  transcript,
  turns,
}: {
  currentTurnId: number | null;
  transcript: TranscriptData;
  turns: PlaybackManifestTurn[];
}) {
  return (
    <div className="panel overflow-hidden rounded-[28px] px-5 py-5 lg:flex-1">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs uppercase tracking-[0.35em] text-[var(--muted)]">
          Docket Timeline
        </p>
        <p className="text-xs uppercase tracking-[0.3em] text-[var(--accent-soft)]">
          turn queue
        </p>
      </div>

      <div className="mt-5 max-h-[24rem] space-y-3 overflow-y-auto pr-1 lg:max-h-[42rem]">
        {turns.map((turn) => {
          const isActive = turn.turnId === currentTurnId;

          return (
            <article
              key={turn.turnId}
              className={`rounded-[22px] border px-4 py-4 transition-colors duration-300 ${
                isActive
                  ? "border-[rgba(212,168,103,0.4)] bg-[rgba(212,168,103,0.08)]"
                  : "border-white/10 bg-white/[0.03]"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-[0.68rem] uppercase tracking-[0.28em] text-[var(--accent-soft)]">
                    {getSceneLabel(turn.scene)}
                  </p>
                  <p className="mt-2 text-sm font-medium leading-6 text-[var(--foreground)]">
                    {getSpeakerShortName(transcript, turn.speakerId)}
                  </p>
                </div>
                <span className="rounded-full border border-white/10 px-2.5 py-1 text-[0.65rem] uppercase tracking-[0.25em] text-[var(--muted)]">
                  {turn.turnId}
                </span>
              </div>
              <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
                {turn.cleanText}
              </p>
            </article>
          );
        })}
      </div>
    </div>
  );
}
