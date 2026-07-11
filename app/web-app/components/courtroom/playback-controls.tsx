import type { PlaybackMode } from "@/hooks/use-courtroom-playback";

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

export function PlaybackControls({
  isPlaying,
  mode,
  manifestSource,
  overallProgress,
  onRestart,
  onTogglePlayback,
}: {
  isPlaying: boolean;
  mode: PlaybackMode;
  manifestSource: string;
  overallProgress: number;
  onRestart: () => void;
  onTogglePlayback: () => void;
}) {
  return (
    <div className="flex w-full items-center gap-3 rounded-full bg-[linear-gradient(180deg,rgba(7,11,22,0.5),rgba(7,11,22,0.82))] px-3 py-2.5 backdrop-blur-xl">
        <button
          aria-label={isPlaying ? "Pause playback" : "Play playback"}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[var(--accent)] text-slate-950 transition-transform duration-200 hover:scale-[1.03] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent-soft)]"
          onClick={onTogglePlayback}
          type="button"
        >
          {isPlaying ? <PauseIcon /> : <PlayIcon />}
        </button>

        <div
          aria-hidden="true"
          className="relative h-1.5 min-w-0 flex-1 overflow-hidden rounded-full bg-white/12"
        >
          <div
            className="absolute inset-y-0 left-0 rounded-full bg-[linear-gradient(90deg,var(--accent),#f0d7a6)] transition-[width] duration-300"
            style={{ width: `${Math.max(3, overallProgress * 100)}%` }}
          />
        </div>

        <button
          aria-label="Replay from start"
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-white/7 text-[var(--foreground)] transition-colors duration-200 hover:bg-white/12 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent-soft)]"
          onClick={onRestart}
          type="button"
        >
          <ReplayIcon />
        </button>

        <div className="sr-only">
          {mode === "audio" ? "Audio playback" : "Preview timeline"} via {manifestSource},
          {` ${Math.round(overallProgress * 100)} percent complete`}
        </div>
    </div>
  );
}
