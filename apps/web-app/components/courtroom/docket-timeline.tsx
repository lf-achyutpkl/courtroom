"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import {
  getSceneLabel,
  getSpeakerShortName,
  type PlaybackManifestTurn,
  type TranscriptData,
} from "@/lib/courtroom";

function formatTurnTime(timeMs: number) {
  const totalSeconds = Math.max(0, Math.floor(timeMs / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

export function DocketTimeline({
  currentTurnId,
  followNonce,
  isPlaying,
  onReturnToCurrent,
  onSelectTurn,
  transcript,
  turns,
}: {
  currentTurnId: number | null;
  followNonce: number;
  isPlaying: boolean;
  onReturnToCurrent: () => void;
  onSelectTurn: (turnIndex: number) => void;
  transcript: TranscriptData;
  turns: PlaybackManifestTurn[];
}) {
  const [pausedFollowNonce, setPausedFollowNonce] = useState<number | null>(null);
  const isAutoFollowPaused = pausedFollowNonce === followNonce;
  const activeTurnRef = useRef<HTMLButtonElement | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);
  const ignoreScrollRef = useRef(false);
  const pauseTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (pauseTimeoutRef.current) {
        window.clearTimeout(pauseTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (currentTurnId === null || !listRef.current || !activeTurnRef.current || isAutoFollowPaused) {
      return;
    }

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const list = listRef.current;
    const activeTurn = activeTurnRef.current;
    const topPadding = 12;
    const targetScrollTop = Math.max(0, activeTurn.offsetTop - topPadding);

    ignoreScrollRef.current = true;
    list.scrollTo({
      top: targetScrollTop,
      behavior: prefersReducedMotion ? "auto" : "smooth",
    });

    if (pauseTimeoutRef.current) {
      window.clearTimeout(pauseTimeoutRef.current);
    }

    pauseTimeoutRef.current = window.setTimeout(() => {
      ignoreScrollRef.current = false;
    }, prefersReducedMotion ? 0 : 250);
  }, [currentTurnId, isAutoFollowPaused]);

  const turnsWithStartTime = useMemo(
    () =>
      turns.reduce<Array<{ turn: PlaybackManifestTurn; turnStartMs: number }>>(
        (items, turn) => {
          const previousItem = items[items.length - 1];
          const turnStartMs = previousItem
            ? previousItem.turnStartMs + previousItem.turn.durationMs
            : 0;

          return [...items, { turn, turnStartMs }];
        },
        [],
      ),
    [turns],
  );

  const handleScroll = () => {
    if (!isPlaying || ignoreScrollRef.current) {
      return;
    }

    setPausedFollowNonce(followNonce);
  };

  const handleReturnToCurrent = () => {
    setPausedFollowNonce(null);
    onReturnToCurrent();
  };

  return (
    <section className="flex h-[min(55vh,520px)] min-h-0 flex-col overflow-hidden rounded-[10px] border border-[#d5cab9] bg-[#fbf7f1] lg:h-full">
      <div className="flex shrink-0 items-center justify-between gap-3 border-b border-[#e1d6c7] px-4 py-3">
        <h2 className="text-sm font-medium text-[#1b1916]">Transcript</h2>
        {isAutoFollowPaused ? (
          <button
            type="button"
            onClick={handleReturnToCurrent}
            className="text-xs font-medium text-[#3c342b] underline decoration-[#b4a490] underline-offset-4 transition-colors duration-150 hover:text-[#1b1916] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#fbf7f1]"
          >
            Return to current
          </button>
        ) : null}
      </div>

      <div
        ref={listRef}
        onScroll={handleScroll}
        className="min-h-0 flex-1 overflow-y-auto px-3 py-3"
      >
        <div className="space-y-2 pb-16">
          {turnsWithStartTime.map(({ turn, turnStartMs }, turnIndex) => {
            const isActive = turn.turnId === currentTurnId;

            return (
              <button
                key={turn.turnId}
                ref={isActive ? activeTurnRef : null}
                type="button"
                onClick={() => onSelectTurn(turnIndex)}
                className={`block w-full rounded-[8px] border px-3 py-3 text-left transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#fbf7f1] ${
                  isActive
                    ? "border-[#a9967d] bg-[#efe5d6]"
                    : "border-[#e0d4c4] bg-[#fbf7f1] hover:bg-[#f3ebdf]"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-1.5 text-[0.78rem] text-[#665d52]">
                      <span>{getSceneLabel(turn.scene)}</span>
                      <span aria-hidden="true">·</span>
                      <span>Turn {turn.turnId}</span>
                      <span aria-hidden="true">·</span>
                      <span>{formatTurnTime(turnStartMs)}</span>
                    </div>
                    <p className="mt-1 text-sm font-medium text-[#1e1914]">
                      {getSpeakerShortName(transcript, turn.speakerId)}
                    </p>
                    <p className="mt-1 text-sm leading-6 text-[#342d26]">{turn.cleanText}</p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
}
