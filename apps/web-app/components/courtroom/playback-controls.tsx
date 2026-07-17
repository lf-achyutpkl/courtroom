"use client";

import type { ReactNode } from "react";

function PlayIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4 fill-current" viewBox="0 0 24 24">
      <path d="M8 5.5v13l10-6.5z" />
    </svg>
  );
}

function PauseIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4 fill-none stroke-current" viewBox="0 0 24 24">
      <path d="M9 6v12M15 6v12" strokeLinecap="round" strokeWidth="2.2" />
    </svg>
  );
}

function ReplayIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4 fill-none stroke-current" viewBox="0 0 24 24">
      <path
        d="M7 7v4h4M7.8 15.7A7 7 0 1 0 5 10.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2.1"
      />
    </svg>
  );
}

function SkipBackIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4 fill-current" viewBox="0 0 24 24">
      <path d="M11 6.2 3.8 12 11 17.8v-4.8l7.2 4.8V6.2L11 11zM5.8 6.2h1.8v11.6H5.8z" />
    </svg>
  );
}

function SkipForwardIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4 fill-current" viewBox="0 0 24 24">
      <path d="m13 6.2 7.2 5.8-7.2 5.8V13l-7.2 4.8V6.2L13 11zM18.4 6.2h-1.8v11.6h1.8z" />
    </svg>
  );
}

function TranscriptIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4 fill-none stroke-current" viewBox="0 0 24 24">
      <path d="M5 7.5h14M5 12h14M5 16.5h8" strokeLinecap="round" strokeWidth="2" />
    </svg>
  );
}

function FullscreenIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4 fill-none stroke-current" viewBox="0 0 24 24">
      <path
        d="M8 4.5H4.5V8M16 4.5h3.5V8M20 16v3.5h-3.5M8 19.5H4.5V16"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.9"
      />
    </svg>
  );
}

function VolumeIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4 fill-none stroke-current" viewBox="0 0 24 24">
      <path
        d="M5.5 14.5H9l4 3V6.5l-4 3H5.5zM16.5 9.2a4 4 0 0 1 0 5.6"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.9"
      />
    </svg>
  );
}

function formatPlaybackTime(timeMs: number) {
  const totalSeconds = Math.max(0, Math.floor(timeMs / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function ControlButton({
  ariaLabel,
  children,
  onClick,
  pressed,
  tone = "default",
}: {
  ariaLabel: string;
  children: ReactNode;
  onClick: () => void;
  pressed?: boolean;
  tone?: "default" | "primary";
}) {
  return (
    <button
      type="button"
      aria-label={ariaLabel}
      aria-pressed={pressed}
      onClick={onClick}
      className={`inline-flex h-9 w-9 items-center justify-center rounded-[8px] border transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#f2eadf] focus-visible:ring-offset-2 focus-visible:ring-offset-[#1e1814] ${
        tone === "primary"
          ? "border-[#f2eadf] bg-[#f2eadf] text-[#1f1915] hover:bg-[#e8ddce]"
          : pressed
            ? "border-[#9e8a73] bg-[#5e4f42] text-[#f6eee2]"
            : "border-[#4a4036] bg-[#2a231d] text-[#f2eadf] hover:bg-[#362e27]"
      }`}
    >
      {children}
    </button>
  );
}

export function PlaybackControls({
  currentTimeMs,
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
  totalDurationMs,
  volume,
}: {
  currentTimeMs: number;
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
  totalDurationMs: number;
  volume: number;
}) {
  const progressValue = Math.max(0, Math.min(totalDurationMs, currentTimeMs));
  const progressPercent = `${Math.max(0, Math.min(100, overallProgress * 100))}%`;

  return (
    <div className="border-t border-[#3f362f] bg-[#1e1814] px-4 py-3 text-[#f2eadf]">
      <label className="block">
        <span className="sr-only">Seek through playback timeline</span>
        <input
          type="range"
          min={0}
          max={Math.max(totalDurationMs, 1)}
          step={100}
          value={progressValue}
          onChange={(event) => onSeek(Number(event.target.value))}
          className="watch-progress h-5 w-full cursor-pointer bg-transparent accent-[#e8ddce]"
          style={{
            backgroundImage: `linear-gradient(to right, #e8ddce 0%, #e8ddce ${progressPercent}, #594d41 ${progressPercent}, #594d41 100%)`,
          }}
        />
      </label>

      <div className="mt-3 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <ControlButton
            ariaLabel={isPlaying ? "Pause playback" : "Play playback"}
            onClick={onTogglePlayback}
            tone="primary"
          >
            {isPlaying ? <PauseIcon /> : <PlayIcon />}
          </ControlButton>
          <ControlButton ariaLabel="Restart playback" onClick={onRestart}>
            <ReplayIcon />
          </ControlButton>
          <ControlButton ariaLabel="Previous turn" onClick={onPreviousTurn}>
            <SkipBackIcon />
          </ControlButton>
          <ControlButton ariaLabel="Next turn" onClick={onNextTurn}>
            <SkipForwardIcon />
          </ControlButton>

          <div className="ml-1 flex items-center gap-2 text-sm text-[#d7ccbd]">
            <span className="font-medium text-[#f5eee4]">{formatPlaybackTime(currentTimeMs)}</span>
            <span className="text-[#8e7f6c]">/</span>
            <span>{formatPlaybackTime(totalDurationMs)}</span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:justify-end">
          <label className="flex h-9 items-center gap-2 rounded-[8px] border border-[#4a4036] bg-[#2a231d] px-3 text-sm text-[#f2eadf]">
            <VolumeIcon />
            <span className="sr-only">Adjust volume</span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={volume}
              onChange={(event) => onVolumeChange(Number(event.target.value))}
              className="volume-slider h-4 w-16 cursor-pointer bg-transparent sm:w-20"
            />
          </label>

          <label className="flex h-9 items-center gap-2 rounded-[8px] border border-[#4a4036] bg-[#2a231d] px-3 text-sm text-[#f2eadf]">
            <span>Speed</span>
            <select
              value={String(playbackRate)}
              onChange={(event) => setPlaybackRate(Number(event.target.value))}
              className="bg-transparent text-sm text-[#f2eadf] outline-none"
              aria-label="Playback speed"
            >
              <option value="0.75">0.75x</option>
              <option value="1">1x</option>
              <option value="1.25">1.25x</option>
              <option value="1.5">1.5x</option>
            </select>
          </label>

          <ControlButton
            ariaLabel={isTranscriptVisible ? "Hide transcript panel" : "Show transcript panel"}
            onClick={onToggleTranscript}
            pressed={isTranscriptVisible}
          >
            <TranscriptIcon />
          </ControlButton>
          <ControlButton
            ariaLabel={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
            onClick={onToggleFullscreen}
            pressed={isFullscreen}
          >
            <FullscreenIcon />
          </ControlButton>
        </div>
      </div>
    </div>
  );
}
