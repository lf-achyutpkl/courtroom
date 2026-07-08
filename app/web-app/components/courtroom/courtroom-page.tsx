"use client";

import transcript from "@/app/courtroom-transcript.json";
import { CaptionFeed } from "@/components/courtroom/caption-feed";
import { CourtroomHeader } from "@/components/courtroom/courtroom-header";
import { CourtroomNotes } from "@/components/courtroom/courtroom-notes";
import { CourtroomStagePanel } from "@/components/courtroom/courtroom-stage-panel";
import { DocketTimeline } from "@/components/courtroom/docket-timeline";
import { PlaybackControls } from "@/components/courtroom/playback-controls";
import {
  getCurrentSubtitle,
  type TranscriptData,
} from "@/lib/courtroom";
import {
  getWitnessOccupant,
  useCourtroomPlayback,
} from "@/hooks/use-courtroom-playback";
import { useCourtroomManifest } from "@/hooks/use-courtroom-manifest";

function CourtroomPageContent({ transcript }: { transcript: TranscriptData }) {
  const { manifest, manifestSource } = useCourtroomManifest(transcript);
  const {
    currentTurn,
    currentTimeMs,
    index,
    isPlaying,
    mode,
    overallProgress,
    setCurrentTimeMs,
    setIndex,
    setIsPlaying,
  } = useCourtroomPlayback(manifest);

  const currentSubtitle = currentTurn
    ? getCurrentSubtitle(currentTurn.subtitleChunks, currentTimeMs)
    : null;
  const currentSpeakerId = currentTurn?.speakerId ?? "judge";
  const witnessInBoxId = getWitnessOccupant(manifest, index);
  const visibleTurns = manifest.slice(Math.max(0, index - 1), Math.min(index + 4, manifest.length));

  const handleTogglePlayback = () => {
    if (!currentTurn) {
      return;
    }

    if (!isPlaying && index === manifest.length - 1 && currentTimeMs >= currentTurn.durationMs) {
      setIndex(0);
      setCurrentTimeMs(0);
    }

    setIsPlaying((value) => !value);
  };

  const handleRestart = () => {
    setIndex(0);
    setCurrentTimeMs(0);
    setIsPlaying(false);
  };

  return (
    <main className="relative flex min-h-screen flex-col px-3 py-3 sm:px-5 sm:py-4 lg:px-8">
      <section className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-4">
        <CourtroomHeader transcript={transcript} />

        <section className="grid flex-1 gap-4 lg:grid-cols-[minmax(0,1.55fr)_minmax(20rem,0.75fr)] lg:items-start">
          <div className="flex flex-col">
            <CourtroomStagePanel
              currentLineProgress={
                currentTurn ? Math.min(1, currentTimeMs / currentTurn.durationMs) : 0
              }
              currentSpeakerId={currentSpeakerId}
              currentTurnScene={currentTurn?.scene ?? "opening"}
              isPlaying={isPlaying}
              transcript={transcript}
              witnessInBoxId={witnessInBoxId}
            />
            <CaptionFeed
              currentSubtitle={currentSubtitle}
              manifestLength={manifest.length}
              turnId={currentTurn?.turnId ?? null}
            />
            <PlaybackControls
              isPlaying={isPlaying}
              manifestSource={manifestSource}
              mode={mode}
              overallProgress={overallProgress}
              onRestart={handleRestart}
              onTogglePlayback={handleTogglePlayback}
            />
          </div>

          <aside className="flex flex-col gap-4">
            <CourtroomNotes
              currentSpeakerId={currentTurn?.speakerId ?? null}
              mode={mode}
              transcript={transcript}
            />
            <DocketTimeline
              currentTurnId={currentTurn?.turnId ?? null}
              transcript={transcript}
              turns={visibleTurns}
            />
          </aside>
        </section>
      </section>
    </main>
  );
}

export function CourtroomPage() {
  return <CourtroomPageContent transcript={transcript} />;
}
