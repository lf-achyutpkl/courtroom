import type { SubtitleChunk } from "@/lib/courtroom";

export function CaptionFeed({
  currentSubtitle,
}: {
  currentSubtitle: SubtitleChunk | null;
}) {
  return (
    <div className="mt-2 shrink-0 px-1 sm:px-2 lg:mt-1.5 min-h-[3.5rem] lg:min-h-[3.25rem]">
      <div className="flex items-center justify-center text-center gap-4">
        <p className="max-w-3xl text-center text-sm leading-6 text-[var(--foreground)]/88 sm:text-[0.96rem] lg:text-[0.92rem] lg:leading-[1.55]">
          {currentSubtitle?.text ??
            "Preview playback uses estimated timing until backend-generated audio is connected."}
        </p>
      </div>
    </div>
  );
}
