import type { SubtitleChunk } from "@/lib/courtroom";

export function CaptionFeed({
  currentSubtitle,
  manifestLength,
  turnId,
}: {
  currentSubtitle: SubtitleChunk | null;
  manifestLength: number;
  turnId: number | null;
}) {
  return (
    <div className="mt-4 shrink-0 rounded-[28px] border border-white/10 bg-[rgba(3,7,18,0.92)] px-4 py-4 sm:px-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-[var(--muted)]">
            Caption Feed
          </p>
          <p className="mt-2 text-lg leading-8 text-[var(--foreground)] sm:text-xl">
            {currentSubtitle?.text ??
              "Generate Kokoro audio into public/audio and the player will swap from preview pacing to real speech automatically."}
          </p>
        </div>
        <div className="text-right text-xs uppercase tracking-[0.3em] text-[var(--muted)]">
          {turnId ? `${turnId.toString().padStart(2, "0")} / ${manifestLength}` : "00 / 00"}
        </div>
      </div>
    </div>
  );
}
