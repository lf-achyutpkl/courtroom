import {
  getSceneLabel,
  getSpeakerShortName,
  type TranscriptData,
} from "@/lib/courtroom";

import { PlaybackControls } from "@/components/courtroom/playback-controls";
import { CourtroomStage } from "@/components/courtroom/stage/courtroom-stage";

function formatTurnSummary({
  currentSpeakerId,
  currentTurnIndex,
  currentTurnScene,
  totalTurnCount,
  transcript,
}: {
  currentSpeakerId: string | null;
  currentTurnIndex: number;
  currentTurnScene: string | null;
  totalTurnCount: number;
  transcript: TranscriptData;
}) {
  const sceneLabel = currentTurnScene ? getSceneLabel(currentTurnScene) : "Awaiting scene";
  const speakerName = currentSpeakerId
    ? getSpeakerShortName(transcript, currentSpeakerId)
    : "No speaker";

  return `${sceneLabel} · ${speakerName} · Turn ${currentTurnIndex + 1} of ${totalTurnCount}`;
}

export function CourtroomStagePanel({
  currentLineProgress,
  currentSpeakerId,
  currentTimeMs,
  currentTurnIndex,
  currentTurnScene,
  isFullscreen,
  isPlaying,
  isTranscriptVisible,
  onNextTurn,
  onPreviousTurn,
  onRestart,
  onSeek,
  onToggleFullscreen,
  onTogglePlayback,
  onToggleTranscript,
  onVolumeChange,
  overallProgress,
  playbackRate,
  setPlaybackRate,
  subtitle,
  totalDurationMs,
  totalTurnCount,
  transcript,
  volume,
  witnessInBoxId,
}: {
  currentLineProgress: number;
  currentSpeakerId: string | null;
  currentTimeMs: number;
  currentTurnIndex: number;
  currentTurnScene: string | null;
  isFullscreen: boolean;
  isPlaying: boolean;
  isTranscriptVisible: boolean;
  onNextTurn: () => void;
  onPreviousTurn: () => void;
  onRestart: () => void;
  onSeek: (timeMs: number) => void;
  onToggleFullscreen: () => void;
  onTogglePlayback: () => void;
  onToggleTranscript: () => void;
  onVolumeChange: (nextValue: number) => void;
  overallProgress: number;
  playbackRate: number;
  setPlaybackRate: (nextValue: number) => void;
  subtitle: string | null;
  totalDurationMs: number;
  totalTurnCount: number;
  transcript: TranscriptData;
  volume: number;
  witnessInBoxId: string | null;
}) {
  return (
    <section className="flex h-full min-h-0 flex-col overflow-hidden rounded-[10px] border border-[#c8bcaa] bg-[#fbf7f1]">
      <div className="border-b border-[#dbcfbf] bg-[#f3ece2] px-4 py-2 text-sm text-[#4f473d]">
        <span className="block truncate font-medium text-[#211c17]">
          {formatTurnSummary({
            currentSpeakerId,
            currentTurnIndex,
            currentTurnScene,
            totalTurnCount,
            transcript,
          })}
        </span>
      </div>

      <div className="relative aspect-video w-full flex-1 bg-[#110d0a] min-[1024px]:aspect-auto min-[1024px]:min-h-0">
        <CourtroomStage
          activeSpeakerId={currentSpeakerId}
          currentLineProgress={currentLineProgress}
          isPlaying={isPlaying}
          scene={currentTurnScene}
          transcript={transcript}
          witnessInBoxId={witnessInBoxId}
        />
      </div>

      <PlaybackControls
        currentTimeMs={currentTimeMs}
        isFullscreen={isFullscreen}
        isPlaying={isPlaying}
        isTranscriptVisible={isTranscriptVisible}
        onNextTurn={onNextTurn}
        onPreviousTurn={onPreviousTurn}
        onRestart={onRestart}
        onSeek={onSeek}
        onToggleFullscreen={onToggleFullscreen}
        onTogglePlayback={onTogglePlayback}
        onToggleTranscript={onToggleTranscript}
        onVolumeChange={onVolumeChange}
        overallProgress={overallProgress}
        playbackRate={playbackRate}
        setPlaybackRate={setPlaybackRate}
        totalDurationMs={totalDurationMs}
        volume={volume}
      />

      <div className="border-t border-[#ddd1c1] bg-[#f7f1e8] px-4 py-3">
        <p className="text-sm leading-6 text-[#433c34]">
          {subtitle ?? "The current line will appear here while playback advances."}
        </p>
      </div>
    </section>
  );
}
