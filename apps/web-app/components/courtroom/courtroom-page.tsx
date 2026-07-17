"use client";

import Link from "next/link";

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

function CourtroomPageStatus({
  title,
  description,
  simulationRunId,
}: {
  title: string;
  description: string;
  simulationRunId?: string;
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
            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              <Link
                href="/"
                className="rounded-full border border-[var(--border)] px-4 py-2 text-xs uppercase tracking-[0.24em] text-[var(--accent-soft)] transition hover:border-[rgba(212,168,103,0.38)] hover:bg-white/[0.04]"
              >
                Browse simulations
              </Link>
              {simulationRunId ? (
                <span className="rounded-full border border-white/10 px-4 py-2 font-mono text-[0.68rem] uppercase tracking-[0.2em] text-[var(--muted)]">
                  {simulationRunId}
                </span>
              ) : null}
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}

function CourtroomPageContent({
  simulationRun,
  manifestSource,
  simulationRunId,
}: {
  simulationRun: SimulationRunPayload;
  manifestSource: string;
  simulationRunId: string;
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
        <div className="flex items-center justify-between gap-3 px-1">
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-white/[0.03] px-4 py-2 text-[0.68rem] uppercase tracking-[0.28em] text-[var(--accent-soft)] transition hover:border-[rgba(212,168,103,0.38)] hover:bg-white/[0.05]"
          >
            Back to simulations
          </Link>
          <span className="rounded-full border border-white/10 px-3 py-2 font-mono text-[0.68rem] uppercase tracking-[0.2em] text-[var(--muted)]">
            Run {simulationRunId}
          </span>
        </div>

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

export function CourtroomPage({
  simulationRunId,
}: {
  simulationRunId: string;
}) {
  const selectedRunId = simulationRunId;
  const { errorMessage, requestState, responseSource, simulationRun } =
    useSimulationRun(selectedRunId);

  if (requestState === "loading") {
    return (
      <CourtroomPageStatus
        title="Loading simulation run"
        description={`Fetching playback data for run ${selectedRunId}.`}
        simulationRunId={selectedRunId}
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
        simulationRunId={selectedRunId}
      />
    );
  }

  if (!simulationRun) {
    return (
      <CourtroomPageStatus
        title="No playback payload returned"
        description="The selected simulation run did not return transcript and manifest data."
        simulationRunId={selectedRunId}
      />
    );
  }

  return (
    <CourtroomPageContent
      manifestSource={responseSource}
      simulationRun={simulationRun}
      simulationRunId={selectedRunId}
    />
  );
}
