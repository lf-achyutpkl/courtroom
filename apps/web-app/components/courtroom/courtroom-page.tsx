"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

import { CaseSummary } from "@/components/courtroom/case-summary";
import { CourtroomStagePanel } from "@/components/courtroom/courtroom-stage-panel";
import { DocketTimeline } from "@/components/courtroom/docket-timeline";
import {
  getCaseTitle,
  getCurrentSubtitle,
  getWitnessSpeakerIds,
  type SimulationRunPayload,
} from "@/lib/courtroom";
import {
  getWitnessOccupant,
  useCourtroomPlayback,
} from "@/hooks/use-courtroom-playback";
import { useSimulationRun } from "@/hooks/use-simulation-run";

function formatPlaybackTime(timeMs: number) {
  const totalSeconds = Math.max(0, Math.floor(timeMs / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  return `${minutes}m ${seconds.toString().padStart(2, "0")}s`;
}

function CourtroomPageStatus({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <main className="min-h-screen bg-[#f4efe7] px-4 py-6 text-[#1b1916] sm:px-6 sm:py-8">
      <section className="mx-auto flex min-h-[calc(100vh-3rem)] w-full max-w-6xl items-center">
        <section className="w-full rounded-[12px] border border-[#d4c8b8] bg-[#fbf7f1] px-6 py-10 sm:px-8">
          <h1 className="text-[1.75rem] font-medium tracking-[-0.03em] text-[#1b1916] sm:text-[2.2rem]">
            {title}
          </h1>
          <p className="mt-3 text-sm leading-6 text-[#554d43] sm:text-[0.96rem]">
            {description}
          </p>
          <div className="mt-6">
            <Link
              href="/"
              className="inline-flex h-10 items-center rounded-[8px] border border-[#cbbbab] bg-[#f5eee4] px-4 text-sm text-[#26231f] transition-colors duration-150 hover:bg-[#ede3d6] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f4efe7]"
            >
              Back to simulations
            </Link>
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
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isTranscriptVisible, setIsTranscriptVisible] = useState(true);
  const [transcriptFollowNonce, setTranscriptFollowNonce] = useState(0);
  const fullscreenHostRef = useRef<HTMLDivElement | null>(null);

  const { playbackManifest: manifest, transcript } = simulationRun;
  const {
    currentTurn,
    currentTimeMs,
    elapsedMs,
    index,
    isPlaying,
    overallProgress,
    playbackRate,
    seekTo,
    setIsPlaying,
    setPlaybackRate,
    setVolume,
    totalDurationMs,
    volume,
    goToTurn,
  } = useCourtroomPlayback(manifest);

  const currentSubtitle = currentTurn
    ? getCurrentSubtitle(currentTurn.subtitleChunks, currentTimeMs)
    : null;
  const currentSpeakerId = currentTurn?.speakerId ?? null;
  const witnessInBoxId = getWitnessOccupant(manifest, index);
  const caseTitle = getCaseTitle(transcript);
  const caseType =
    transcript.case_metadata.case_type.charAt(0).toUpperCase() +
    transcript.case_metadata.case_type.slice(1);
  const witnessCount = getWitnessSpeakerIds(transcript).length;
  const transcriptTurnCount = manifest.length;
  const metadataLine = [
    caseType,
    `${witnessCount} ${witnessCount === 1 ? "witness" : "witnesses"}`,
    `${transcriptTurnCount} transcript ${transcriptTurnCount === 1 ? "turn" : "turns"}`,
    formatPlaybackTime(totalDurationMs),
  ].join(" · ");

  useEffect(() => {
    document.body.classList.add("body-light-surface");

    const handleFullscreenChange = () => {
      setIsFullscreen(document.fullscreenElement === fullscreenHostRef.current);
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => {
      document.body.classList.remove("body-light-surface");
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
    };
  }, []);

  const bumpTranscriptFollow = () => {
    setTranscriptFollowNonce((value) => value + 1);
  };

  const handleTogglePlayback = () => {
    if (!currentTurn) {
      return;
    }

    if (!isPlaying && index === manifest.length - 1 && currentTimeMs >= currentTurn.durationMs) {
      seekTo(0);
    }

    bumpTranscriptFollow();
    setIsPlaying((value) => !value);
  };

  const handleRestart = () => {
    bumpTranscriptFollow();
    seekTo(0);
    setIsPlaying(false);
  };

  const handlePreviousTurn = () => {
    bumpTranscriptFollow();
    goToTurn(Math.max(0, index - 1));
    setIsPlaying(false);
  };

  const handleNextTurn = () => {
    bumpTranscriptFollow();
    goToTurn(Math.min(manifest.length - 1, index + 1));
    setIsPlaying(false);
  };

  const handleSelectTurn = (turnIndex: number) => {
    bumpTranscriptFollow();
    goToTurn(turnIndex);
    setIsPlaying(false);
  };

  const handleSeek = (timeMs: number) => {
    bumpTranscriptFollow();
    seekTo(timeMs);
  };

  const handleReturnToCurrent = () => {
    bumpTranscriptFollow();
  };

  const handleToggleFullscreen = async () => {
    if (!fullscreenHostRef.current) {
      return;
    }

    if (document.fullscreenElement === fullscreenHostRef.current) {
      await document.exitFullscreen();
      return;
    }

    await fullscreenHostRef.current.requestFullscreen();
  };

  const watchGridClassName = isTranscriptVisible
    ? "grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-stretch"
    : "grid gap-5";

  return (
    <main className="min-h-screen bg-[#f4efe7] px-4 py-4 text-[#1b1916] sm:px-6 sm:py-5">
      <section className="mx-auto w-full max-w-[90rem]">
        <div className="pb-3">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-[#3f382f] transition-colors duration-150 hover:text-[#161411] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f4efe7]"
          >
            <span aria-hidden="true" className="text-base leading-none">
              ←
            </span>
            <span>Home</span>
          </Link>
        </div>

        <section className={`${watchGridClassName} lg:h-[80vh]`}>
          <div ref={fullscreenHostRef} className="min-h-0 min-w-0 lg:h-full">
            <CourtroomStagePanel
              currentLineProgress={
                currentTurn ? Math.min(1, currentTimeMs / currentTurn.durationMs) : 0
              }
              currentSpeakerId={currentSpeakerId}
              currentTimeMs={elapsedMs}
              currentTurnIndex={index}
              currentTurnScene={currentTurn?.scene ?? null}
              isFullscreen={isFullscreen}
              isPlaying={isPlaying}
              isTranscriptVisible={isTranscriptVisible}
              onNextTurn={handleNextTurn}
              onPreviousTurn={handlePreviousTurn}
              onRestart={handleRestart}
              onSeek={handleSeek}
              onToggleFullscreen={() => void handleToggleFullscreen()}
              onTogglePlayback={handleTogglePlayback}
              onToggleTranscript={() => setIsTranscriptVisible((value) => !value)}
              onVolumeChange={setVolume}
              overallProgress={overallProgress}
              playbackRate={playbackRate}
              setPlaybackRate={setPlaybackRate}
              subtitle={currentSubtitle?.text ?? null}
              totalDurationMs={totalDurationMs}
              totalTurnCount={manifest.length}
              transcript={transcript}
              volume={volume}
              witnessInBoxId={witnessInBoxId}
            />
          </div>

          {isTranscriptVisible ? (
            <aside className="min-h-0 min-w-0 lg:h-full">
              <DocketTimeline
                currentTurnId={currentTurn?.turnId ?? null}
                followNonce={transcriptFollowNonce}
                isPlaying={isPlaying}
                onReturnToCurrent={handleReturnToCurrent}
                onSelectTurn={handleSelectTurn}
                transcript={transcript}
                turns={manifest}
              />
            </aside>
          ) : null}
        </section>

        <section className="mt-4 w-full">
          <h1 className="text-[1.5rem] font-medium leading-tight tracking-[-0.03em] text-[#1b1916] sm:text-[1.8rem]">
            {caseTitle}
          </h1>
          <p className="mt-1 text-base text-[#2c2721]">{transcript.case_metadata.charge}</p>
          <p className="mt-2 text-sm text-[#62584d]">{metadataLine}</p>

          <div className="mt-5">
            <CaseSummary
              responseSource={manifestSource}
              simulationRunId={simulationRunId}
              transcript={transcript}
            />
          </div>
        </section>
      </section>
    </main>
  );
}

export function CourtroomPage({ simulationRunId }: { simulationRunId: string }) {
  const { errorMessage, requestState, responseSource, simulationRun } =
    useSimulationRun(simulationRunId);
  const loading = requestState === "idle" || requestState === "loading";
  const error = requestState === "error" ? errorMessage : null;

  if (loading) {
    return (
      <CourtroomPageStatus
        title="Loading simulation"
        description="Preparing the courtroom playback, transcript, and case materials."
      />
    );
  }

  if (error || !simulationRun) {
    return (
      <CourtroomPageStatus
        title="Simulation unavailable"
        description={
          error ??
          "The requested simulation could not be loaded. Verify the run identifier and try again."
        }
      />
    );
  }

  return (
    <CourtroomPageContent
      manifestSource={responseSource}
      simulationRun={simulationRun}
      simulationRunId={simulationRunId}
    />
  );
}
