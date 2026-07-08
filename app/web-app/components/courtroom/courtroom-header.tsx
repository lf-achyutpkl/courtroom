import type { TranscriptData } from "@/lib/courtroom";

export function CourtroomHeader({ transcript }: { transcript: TranscriptData }) {
  return (
    <header className="panel shrink-0 rounded-[28px] px-5 py-4 sm:px-7">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-4xl">
          <p className="mb-2 text-xs uppercase tracking-[0.45em] text-[var(--muted)]">
            Kokoro-first courtroom simulation
          </p>
          <h1 className="font-display text-4xl leading-none text-[var(--foreground)] sm:text-6xl">
            United States v. Ethan Caldwell
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--muted)] sm:text-base">
            A fixed-camera courtroom playback built from transcript turns, with
            Kokoro-ready speech assets, scene-led pacing, and simple witness
            choreography rather than heavyweight animation systems.
          </p>
        </div>

        <div className="grid gap-3 text-sm text-[var(--muted)] sm:grid-cols-2 lg:min-w-[22rem]">
          <div>
            <p className="text-[0.65rem] uppercase tracking-[0.35em] text-[var(--accent-soft)]">
              Case ID
            </p>
            <p className="mt-1 text-base text-[var(--foreground)]">
              {transcript.case_metadata.case_id}
            </p>
          </div>
          <div>
            <p className="text-[0.65rem] uppercase tracking-[0.35em] text-[var(--accent-soft)]">
              Charge
            </p>
            <p className="mt-1 line-clamp-2 text-base text-[var(--foreground)]">
              {transcript.case_metadata.charge}
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
