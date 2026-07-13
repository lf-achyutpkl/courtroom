import { getCaseTitle, type TranscriptData } from "@/lib/courtroom";

export function CourtroomHeader({ transcript }: { transcript: TranscriptData }) {
  const caseTitle = getCaseTitle(transcript);

  return (
    <header className="panel shrink-0 rounded-[28px] px-5 py-4 sm:px-7 sm:py-5 lg:px-6 lg:py-3.5">
      <div className="flex flex-col gap-4 lg:gap-3">
        <div className="max-w-5xl">
          <div className="flex flex-wrap items-center gap-2.5">
            <p className="text-xs uppercase tracking-[0.45em] text-[var(--muted)]">
              Courtroom simulation
            </p>
            <span
              aria-hidden="true"
              className="h-px w-12 bg-gradient-to-r from-[var(--accent-soft)]/80 to-transparent"
            />
          </div>
        </div>

        <div className="border-t border-[var(--border)] pt-4 lg:pt-3">
          <p className="text-xs uppercase tracking-[0.45em] text-[var(--accent-soft)]">
            Case file
          </p>
          <h1 className="mt-2 max-w-5xl font-display text-3xl leading-[0.9] text-[var(--foreground)] sm:text-[3.25rem] lg:text-[2.05rem]">
            {caseTitle}
          </h1>
          <p className="mt-1 text-sm leading-6 text-[var(--foreground)] sm:text-[0.98rem] lg:text-[0.94rem] italic">
                {transcript.case_metadata.charge}
          </p>
        </div>
      </div>
    </header>
  );
}
