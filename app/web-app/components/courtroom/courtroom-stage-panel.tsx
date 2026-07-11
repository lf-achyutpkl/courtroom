import {
  getSceneLabel,
  getSpeakerShortName,
  type TranscriptData,
} from "@/lib/courtroom";

import { PlaybackControls } from "@/components/courtroom/playback-controls";
import { CourtroomStage } from "@/components/courtroom/stage/courtroom-stage";
import type { PlaybackMode } from "@/hooks/use-courtroom-playback";

export function CourtroomStagePanel({
  currentLineProgress,
  currentSpeakerId,
  currentTurnScene,
  isPlaying,
  manifestSource,
  mode,
  onRestart,
  onTogglePlayback,
  overallProgress,
  transcript,
  witnessInBoxId,
}: {
  currentLineProgress: number;
  currentSpeakerId: string | null;
  currentTurnScene: string | null;
  isPlaying: boolean;
  manifestSource: string;
  mode: PlaybackMode;
  onRestart: () => void;
  onTogglePlayback: () => void;
  overallProgress: number;
  transcript: TranscriptData;
  witnessInBoxId: string | null;
}) {
  const speakerName = currentSpeakerId
    ? getSpeakerShortName(transcript, currentSpeakerId)
    : "No one speaking";
  const sceneLabel = currentTurnScene ? getSceneLabel(currentTurnScene) : "Awaiting Scene";
  const showHeader = isPlaying && mode === "audio";
  const sectionLabelClassName =
    "text-[0.65rem] uppercase tracking-[0.35em] text-[var(--muted)]";
  const sectionValueClassName =
    "mt-1 font-display text-lg leading-none text-[var(--foreground)] sm:text-xl pb-0.5";

  return (
    <div className="panel flex flex-col rounded-[32px] p-3 sm:p-4 lg:min-h-0 lg:p-3.5">
      <div
        aria-hidden={!showHeader}
        className={`flex shrink-0 items-start justify-between gap-4 px-3 py-3 transition-opacity duration-200 sm:px-4 lg:px-3 lg:py-2.5 ${
          showHeader ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
      >
        <div>
          <p className={sectionLabelClassName}>Active Scene</p>
          <p className={sectionValueClassName}>{sceneLabel}</p>
        </div>

        <div className="min-w-0 text-right">
          <p className={sectionLabelClassName}>Speaking Now</p>
          <div className="mt-1 flex items-center justify-end gap-3">
            <div className="flex items-end gap-1.5" aria-hidden="true">
              <span className="h-2 w-1 rounded-full bg-[var(--accent-soft)] animate-[speaker-bar_0.9s_ease-in-out_infinite]" />
              <span className="h-4 w-1 rounded-full bg-[var(--accent)] animate-[speaker-bar_0.9s_ease-in-out_0.18s_infinite]" />
              <span className="h-3 w-1 rounded-full bg-[var(--accent-soft)] animate-[speaker-bar_0.9s_ease-in-out_0.36s_infinite]" />
            </div>
            <div className="min-w-0">
              <p className={`truncate ${sectionValueClassName}`}>{speakerName}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="relative h-[clamp(20rem,48vh,42rem)] min-h-[20rem] overflow-hidden rounded-[24px] sm:h-[clamp(24rem,52vh,44rem)] lg:h-[clamp(21rem,39vh,31rem)]">
        <CourtroomStage
          activeSpeakerId={currentSpeakerId}
          currentLineProgress={currentLineProgress}
          isPlaying={isPlaying}
          scene={currentTurnScene}
          transcript={transcript}
          witnessInBoxId={witnessInBoxId}
        />
      </div>

      <div className="mt-2.5 px-1 sm:px-2">
        <PlaybackControls
          isPlaying={isPlaying}
          manifestSource={manifestSource}
          mode={mode}
          onRestart={onRestart}
          onTogglePlayback={onTogglePlayback}
          overallProgress={overallProgress}
        />
      </div>
    </div>
  );
}
