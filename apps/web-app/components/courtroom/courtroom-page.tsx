"use client";

import { CaseSummary } from "@/components/courtroom/case-summary";
import { CaptionFeed } from "@/components/courtroom/caption-feed";
import { CourtroomHeader } from "@/components/courtroom/courtroom-header";
import { CourtroomStagePanel } from "@/components/courtroom/courtroom-stage-panel";
import { DocketTimeline } from "@/components/courtroom/docket-timeline";
import {
  getCurrentSubtitle,
  type SimulationRunPayload,
} from "@/lib/courtroom";
import {
  getWitnessOccupant,
  useCourtroomPlayback,
} from "@/hooks/use-courtroom-playback";
import { useSimulationRun } from "@/hooks/use-simulation-run";

const DEFAULT_SIMULATION_RUN_ID = process.env.NEXT_PUBLIC_DEFAULT_SIMULATION_RUN_ID ?? null;

function CourtroomPageStatus({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <main className="relative flex min-h-screen flex-col px-3 pt-3 pb-8 sm:px-5 sm:pt-4 sm:pb-10 lg:min-h-dvh lg:px-6 lg:pt-3 lg:pb-6">
      <section className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-4">
        <section className="panel flex flex-1 items-center justify-center rounded-[32px] px-6 py-10 sm:px-8">
          <div className="max-w-2xl text-center">
            <p className="text-xs uppercase tracking-[0.42em] text-[var(--accent-soft)]">
              Courtroom simulation
            </p>
            <h1 className="mt-4 font-display text-3xl leading-[0.92] text-[var(--foreground)] sm:text-[3rem]">
              {title}
            </h1>
            <p className="mt-4 text-sm leading-7 text-[var(--muted)] sm:text-[0.98rem]">
              {description}
            </p>
          </div>
        </section>
      </section>
    </main>
  );
}

function CourtroomPageContent({
  simulationRun,
  manifestSource,
}: {
  simulationRun: SimulationRunPayload;
  manifestSource: string;
}) {
  const { playbackManifest: manifest, transcript } = simulationRun;
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
  const selectedRunId = DEFAULT_SIMULATION_RUN_ID;
  const { errorMessage, requestState, responseSource, simulationRun } =
    useSimulationRun(selectedRunId);

  if (!selectedRunId) {
    return (
      <CourtroomPageStatus
        title="Simulation run selection is not wired yet"
        description="The playback page now expects a single backend simulation-run payload. Once the run list lands, selecting a run will fetch that payload and start playback here."
      />
    );
  }

  if (requestState === "loading") {
    return (
      <CourtroomPageStatus
        title="Loading simulation run"
        description={`Fetching playback data for run ${selectedRunId}.`}
      />
    );
  }

  if (requestState === "error") {
    return (
      <CourtroomPageStatus
        title="Simulation run unavailable"
        description={
          errorMessage ??
          "The backend playback payload could not be loaded for the selected simulation run."
        }
      />
    );
  }

  if (!simulationRun) {
    return (
      <CourtroomPageStatus
        title="No playback payload returned"
        description="The selected simulation run did not return transcript and manifest data."
      />
    );
  }

  return (
    <CourtroomPageContent
      manifestSource={responseSource}
      simulationRun={simulationRun}
    />
  );
}
