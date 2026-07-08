import type { PlaybackMode } from "@/hooks/use-courtroom-playback";

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
    <>
      <div className="shrink-0 flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-3 py-3 sm:px-4">
        <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.25em]">
          <span className="rounded-full border border-[var(--border)] bg-white/5 px-3 py-2 text-[var(--accent-soft)]">
            {mode === "audio" ? "Audio playback" : "Preview timeline"}
          </span>
          <span className="rounded-full border border-[var(--border)] bg-white/5 px-3 py-2 text-[var(--muted)]">
            {manifestSource}
          </span>
        </div>
      </div>

      <div className="mt-4 shrink-0 rounded-[28px] border border-white/10 bg-[rgba(255,255,255,0.03)] px-4 py-4">
        <div className="mb-3 flex items-center justify-between gap-3 text-xs uppercase tracking-[0.3em] text-[var(--muted)]">
          <span>Playback rail</span>
          <span>{Math.round(overallProgress * 100)}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-white/8">
          <div
            className="h-full rounded-full bg-[linear-gradient(90deg,var(--accent),#f0d7a6)] transition-[width] duration-300"
            style={{ width: `${Math.max(3, overallProgress * 100)}%` }}
          />
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button
            className="rounded-full bg-[var(--accent)] px-5 py-3 text-sm font-medium text-slate-950 transition-transform duration-200 hover:-translate-y-0.5"
            onClick={onTogglePlayback}
            type="button"
          >
            {isPlaying ? "Pause Session" : "Play Session"}
          </button>
          <button
            className="rounded-full border border-white/10 bg-white/5 px-5 py-3 text-sm font-medium text-[var(--foreground)] transition-colors duration-200 hover:bg-white/10"
            onClick={onRestart}
            type="button"
          >
            Reset Timeline
          </button>
        </div>
      </div>
    </>
  );
}
