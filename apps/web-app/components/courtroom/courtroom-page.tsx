"use client";

import transcript from "@/app/courtroom-transcript.json";
import { CaseSummary } from "@/components/courtroom/case-summary";
import { CaptionFeed } from "@/components/courtroom/caption-feed";
import { CourtroomHeader } from "@/components/courtroom/courtroom-header";
import { CourtroomStagePanel } from "@/components/courtroom/courtroom-stage-panel";
import { DocketTimeline } from "@/components/courtroom/docket-timeline";
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
  const currentSpeakerId = currentTurn?.speakerId ?? null;
  const witnessInBoxId = getWitnessOccupant(manifest, index);

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
    <main className="relative flex min-h-screen flex-col px-3 pt-3 pb-8 sm:px-5 sm:pt-4 sm:pb-10 lg:min-h-dvh lg:px-6 lg:pt-3 lg:pb-6">
      <section className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-4 lg:min-h-0">
        <CourtroomHeader transcript={transcript} />

        <section className="grid flex-1 gap-4 lg:min-h-0 lg:grid-cols-[minmax(0,1.62fr)_minmax(18rem,0.72fr)] lg:items-stretch">
          <div className="flex flex-col lg:min-h-0 lg:h-full">
            <CourtroomStagePanel
              currentLineProgress={
                currentTurn ? Math.min(1, currentTimeMs / currentTurn.durationMs) : 0
              }
              currentSpeakerId={currentSpeakerId}
              currentTurnScene={currentTurn?.scene ?? null}
              isPlaying={isPlaying}
              manifestSource={manifestSource}
              mode={mode}
              onRestart={handleRestart}
              onTogglePlayback={handleTogglePlayback}
              overallProgress={overallProgress}
              transcript={transcript}
              witnessInBoxId={witnessInBoxId}
            />
            <CaptionFeed
              currentSubtitle={currentSubtitle}
            />
          </div>

          <aside className="flex flex-col gap-4 lg:min-h-0 lg:h-full">
            <CaseSummary transcript={transcript} />
            <DocketTimeline
              currentTurnId={currentTurn?.turnId ?? null}
              transcript={transcript}
              turns={manifest}
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
