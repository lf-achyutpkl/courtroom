import {
  getSceneLabel,
  getSpeakerShortName,
  getSpeakerTone,
  type TranscriptData,
} from "@/lib/courtroom";

import { CourtroomStage } from "@/components/courtroom/stage/courtroom-stage";

export function CourtroomStagePanel({
  currentLineProgress,
  currentSpeakerId,
  currentTurnScene,
  isPlaying,
  transcript,
  witnessInBoxId,
}: {
  currentLineProgress: number;
  currentSpeakerId: string;
  currentTurnScene: string;
  isPlaying: boolean;
  transcript: TranscriptData;
  witnessInBoxId: string | null;
}) {
  const speakerTone = getSpeakerTone(transcript, currentSpeakerId);

  return (
    <div className="panel flex flex-col rounded-[32px] p-3 sm:p-4">
      <div className="shrink-0 px-3 py-3 sm:px-4">
        <p className="text-xs uppercase tracking-[0.35em] text-[var(--muted)]">
          Active Scene
        </p>
        <p className="font-display text-3xl text-[var(--foreground)]">
          {getSceneLabel(currentTurnScene)}
        </p>
      </div>

      <div className="relative h-[clamp(20rem,48vh,42rem)] min-h-[20rem] overflow-hidden rounded-[24px] sm:h-[clamp(24rem,52vh,44rem)] lg:h-[clamp(24rem,46vh,40rem)]">
        <CourtroomStage
          activeSpeakerId={currentSpeakerId}
          currentLineProgress={currentLineProgress}
          isPlaying={isPlaying}
          scene={currentTurnScene}
          transcript={transcript}
          witnessInBoxId={witnessInBoxId}
        />
        <div className="pointer-events-none absolute inset-x-0 top-0 flex items-start justify-between gap-3 p-4">
          <div className="rounded-full border border-white/10 bg-[rgba(3,6,16,0.78)] px-4 py-2 text-xs uppercase tracking-[0.3em] text-[var(--accent-soft)]">
            {getSpeakerShortName(transcript, currentSpeakerId)}
          </div>
          <div className="max-w-xs rounded-[20px] border border-white/10 bg-[rgba(3,6,16,0.78)] px-4 py-3 text-right text-xs leading-5 text-[var(--muted)]">
            {speakerTone}
          </div>
        </div>
      </div>
    </div>
  );
}
