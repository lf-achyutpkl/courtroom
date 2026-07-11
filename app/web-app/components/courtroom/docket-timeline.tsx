"use client";

import { useEffect, useRef } from "react";

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
  const containerRef = useRef<HTMLDivElement | null>(null);
  const activeTurnRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (currentTurnId === null || !containerRef.current || !activeTurnRef.current) {
      return;
    }

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const container = containerRef.current;
    const activeTurn = activeTurnRef.current;
    const containerRect = container.getBoundingClientRect();
    const activeRect = activeTurn.getBoundingClientRect();
    const isFullyVisible =
      activeRect.top >= containerRect.top && activeRect.bottom <= containerRect.bottom;

    if (!isFullyVisible) {
      const offsetTop = activeTurn.offsetTop - container.offsetTop;
      const targetScrollTop =
        offsetTop - container.clientHeight / 2 + activeTurn.clientHeight / 2;

      container.scrollTo({
        top: Math.max(0, targetScrollTop),
        behavior: prefersReducedMotion ? "auto" : "smooth",
      });
    }
  }, [currentTurnId]);

  return (
    <div className="panel overflow-hidden rounded-[28px] px-5 py-5 lg:flex lg:min-h-0 lg:flex-1 lg:flex-col">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs uppercase tracking-[0.3em] text-[var(--accent-soft)]">
          Docket Timeline
        </p>
      </div>

      <div
        ref={containerRef}
        className="mt-4 h-[24rem] space-y-3 overflow-y-auto pr-1 lg:min-h-0 lg:h-auto lg:flex-1"
      >
        {turns.map((turn) => {
          const isActive = turn.turnId === currentTurnId;

          return (
            <article
              key={turn.turnId}
              ref={isActive ? activeTurnRef : null}
              className={`rounded-[22px] border px-4 py-3.5 transition-colors duration-300 ${
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
                  <p className="mt-1.5 text-sm font-medium leading-6 text-[var(--foreground)]">
                    {getSpeakerShortName(transcript, turn.speakerId)}
                  </p>
                </div>
                <span className="rounded-full border border-white/10 px-2.5 py-1 text-[0.65rem] uppercase tracking-[0.25em] text-[var(--muted)]">
                  {turn.turnId}
                </span>
              </div>
              <p className="mt-2.5 text-sm leading-6 text-[var(--muted)]">
                {turn.cleanText}
              </p>
            </article>
          );
        })}
      </div>
    </div>
  );
}
