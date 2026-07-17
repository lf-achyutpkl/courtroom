"use client";

import Link from "next/link";

import { useSimulationRunCatalog } from "@/hooks/use-simulation-run-catalog";
import {
  formatDuration,
  formatRunDate,
  getCaseTypeLabel,
  getVerdictTone,
} from "@/lib/simulation-runs";

function LibraryStatus({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <main className="relative flex min-h-screen flex-col px-3 pt-3 pb-8 sm:px-5 sm:pt-4 sm:pb-10 lg:min-h-dvh lg:px-6 lg:pt-3 lg:pb-6">
      <section className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-4">
        <section className="panel flex flex-1 items-center justify-center rounded-[32px] px-6 py-10 sm:px-8">
          <div className="max-w-2xl text-center">
            <p className="text-xs uppercase tracking-[0.42em] text-[var(--accent-soft)]">
              Simulation library
            </p>
            <h1 className="mt-4 font-display text-3xl leading-[0.92] text-[var(--foreground)] sm:text-[3rem]">
              {title}
            </h1>
            <p className="mt-4 text-sm leading-7 text-[var(--muted)] sm:text-[0.98rem]">
              {description}
            </p>
          </div>
        </section>
      </section>
    </main>
  );
}

function SimulationThumbnail({
  caseType,
  verdictLabel,
}: {
  caseType: string;
  verdictLabel: string | null;
}) {
  return (
    <div className="relative overflow-hidden rounded-[28px] border border-[rgba(242,217,172,0.18)] bg-[linear-gradient(135deg,rgba(212,168,103,0.12),rgba(143,165,198,0.08)_55%,rgba(6,10,23,0.96))] p-5">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(242,217,172,0.22),transparent_34%),linear-gradient(180deg,transparent,rgba(0,0,0,0.24))]" />
      <div className="absolute inset-x-5 top-5 h-px bg-gradient-to-r from-[rgba(242,217,172,0.6)] via-white/20 to-transparent" />
      <div className="relative flex h-full min-h-40 flex-col justify-between">
        <div className="flex items-center justify-between gap-3">
          <span className="rounded-full border border-white/10 bg-black/10 px-3 py-1 text-[0.62rem] uppercase tracking-[0.28em] text-[var(--accent-soft)]">
            {getCaseTypeLabel(caseType)}
          </span>
          <span className={`text-[0.62rem] uppercase tracking-[0.24em] ${getVerdictTone(verdictLabel)}`}>
            {verdictLabel ?? "Ready for playback"}
          </span>
        </div>
        <div>
          <p className="text-[0.68rem] uppercase tracking-[0.34em] text-[var(--muted)]">
            Trial record
          </p>
          <p className="mt-3 font-display text-4xl leading-none text-[var(--foreground)] sm:text-[4.25rem]">
            {caseType === "criminal" ? "01" : "02"}
          </p>
          <p className="mt-3 max-w-[14rem] text-sm leading-6 text-[var(--muted)]">
            Full audio, transcript, and witness chronology packaged for front-end playback.
          </p>
        </div>
      </div>
    </div>
  );
}

export function SimulationLibraryPage() {
  const { catalog, errorMessage, requestState } = useSimulationRunCatalog();

  if (requestState === "loading" || requestState === "idle") {
    return (
      <LibraryStatus
        title="Collecting completed simulations"
        description="Fetching trial runs that are fully rendered and ready for courtroom playback."
      />
    );
  }

  if (requestState === "error") {
    return (
      <LibraryStatus
        title="Simulation library unavailable"
        description={
          errorMessage ??
          "The completed simulation catalog could not be loaded from the backend."
        }
      />
    );
  }

  if (catalog.length === 0) {
    return (
      <LibraryStatus
        title="No completed simulations yet"
        description="Completed runs with generated audio will appear here once the backend finishes a full simulation pipeline."
      />
    );
  }

  const featuredRun = catalog[0];

  return (
    <main className="relative flex min-h-screen flex-col px-3 pt-3 pb-8 sm:px-5 sm:pt-4 sm:pb-10 lg:min-h-dvh lg:px-6 lg:pt-3 lg:pb-6">
      <section className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-4">
        <section className="panel relative overflow-hidden rounded-[34px] px-5 py-6 sm:px-7 sm:py-7">
          <div className="absolute inset-x-0 top-0 h-32 bg-[radial-gradient(circle_at_top,rgba(212,168,103,0.2),transparent_60%)]" />
          <div className="relative grid gap-6 lg:grid-cols-[minmax(0,1.08fr)_minmax(20rem,0.92fr)] lg:items-stretch">
            <div className="max-w-2xl">
              <p className="text-xs uppercase tracking-[0.45em] text-[var(--accent-soft)]">
                Courtroom simulation archive
              </p>
              <h1 className="mt-4 font-display text-4xl leading-[0.9] text-[var(--foreground)] sm:text-[4.4rem]">
                Select a finished trial run and move straight into playback.
              </h1>
              <p className="mt-5 max-w-xl text-sm leading-7 text-[var(--muted)] sm:text-[1rem]">
                Every entry below is fully completed, includes generated audio, and opens directly into the live courtroom experience without local bootstrap data.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <div className="rounded-[22px] border border-white/10 bg-white/[0.04] px-4 py-3">
                  <p className="text-[0.62rem] uppercase tracking-[0.3em] text-[var(--muted)]">
                    Available runs
                  </p>
                  <p className="mt-2 font-display text-3xl text-[var(--foreground)]">
                    {catalog.length}
                  </p>
                </div>
                <div className="rounded-[22px] border border-white/10 bg-white/[0.04] px-4 py-3">
                  <p className="text-[0.62rem] uppercase tracking-[0.3em] text-[var(--muted)]">
                    Featured runtime
                  </p>
                  <p className="mt-2 font-display text-3xl text-[var(--foreground)]">
                    {formatDuration(featuredRun.playback.durationMs)}
                  </p>
                </div>
              </div>
            </div>

            <div className="panel rounded-[30px] border border-[rgba(242,217,172,0.14)] bg-[rgba(255,255,255,0.03)] p-4">
              <SimulationThumbnail
                caseType={featuredRun.caseFile.caseType}
                verdictLabel={featuredRun.playback.verdictLabel}
              />
              <div className="mt-4 px-1">
                <p className="text-[0.68rem] uppercase tracking-[0.28em] text-[var(--accent-soft)]">
                  Featured case file
                </p>
                <h2 className="mt-2 font-display text-2xl leading-tight text-[var(--foreground)]">
                  {featuredRun.caseFile.plaintiffOrProsecution} v. {featuredRun.caseFile.defendant}
                </h2>
                <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                  {featuredRun.caseFile.charge}
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          {catalog.map((run) => (
            <Link
              key={run.simulationRunId}
              href={`/simulations/${run.simulationRunId}`}
              className="group panel rounded-[30px] p-4 transition duration-300 hover:-translate-y-0.5 hover:border-[rgba(212,168,103,0.34)] hover:bg-white/[0.04]"
            >
              <div className="grid gap-4 md:grid-cols-[15rem_minmax(0,1fr)]">
                <SimulationThumbnail
                  caseType={run.caseFile.caseType}
                  verdictLabel={run.playback.verdictLabel}
                />

                <div className="flex flex-col">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full border border-[rgba(242,217,172,0.14)] px-3 py-1 text-[0.62rem] uppercase tracking-[0.28em] text-[var(--accent-soft)]">
                      {getCaseTypeLabel(run.caseFile.caseType)}
                    </span>
                    <span className="rounded-full border border-white/10 px-3 py-1 text-[0.62rem] uppercase tracking-[0.28em] text-[var(--muted)]">
                      {run.playback.turnCount} turns
                    </span>
                    <span className="rounded-full border border-white/10 px-3 py-1 text-[0.62rem] uppercase tracking-[0.28em] text-[var(--muted)]">
                      {formatDuration(run.playback.durationMs)}
                    </span>
                  </div>

                  <h2 className="mt-4 font-display text-[2rem] leading-[0.94] text-[var(--foreground)]">
                    {run.caseFile.plaintiffOrProsecution} v. {run.caseFile.defendant}
                  </h2>
                  <p className="mt-2 text-sm leading-6 text-[var(--foreground)]/88">
                    {run.caseFile.charge}
                  </p>

                  <dl className="mt-5 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-[20px] border border-white/10 bg-black/10 px-4 py-3">
                      <dt className="text-[0.62rem] uppercase tracking-[0.28em] text-[var(--muted)]">
                        Completed
                      </dt>
                      <dd className="mt-2 text-sm leading-6 text-[var(--foreground)]">
                        {formatRunDate(run.completedAt)}
                      </dd>
                    </div>
                    <div className="rounded-[20px] border border-white/10 bg-black/10 px-4 py-3">
                      <dt className="text-[0.62rem] uppercase tracking-[0.28em] text-[var(--muted)]">
                        Case file ID
                      </dt>
                      <dd className="mt-2 font-mono text-xs leading-6 text-[var(--foreground)]/82">
                        {run.caseFile.caseId}
                      </dd>
                    </div>
                    <div className="rounded-[20px] border border-white/10 bg-black/10 px-4 py-3">
                      <dt className="text-[0.62rem] uppercase tracking-[0.28em] text-[var(--muted)]">
                        Witnesses
                      </dt>
                      <dd className="mt-2 text-sm leading-6 text-[var(--foreground)]">
                        {run.caseFile.witnessCount}
                      </dd>
                    </div>
                    <div className="rounded-[20px] border border-white/10 bg-black/10 px-4 py-3">
                      <dt className="text-[0.62rem] uppercase tracking-[0.28em] text-[var(--muted)]">
                        Evidence items
                      </dt>
                      <dd className="mt-2 text-sm leading-6 text-[var(--foreground)]">
                        {run.caseFile.evidenceCount}
                      </dd>
                    </div>
                  </dl>

                  <div className="mt-5 flex items-center justify-between gap-3 border-t border-white/10 pt-4">
                    <div>
                      <p className="text-[0.62rem] uppercase tracking-[0.28em] text-[var(--muted)]">
                        Dominant scene
                      </p>
                      <p className="mt-1 text-sm leading-6 text-[var(--foreground)]">
                        {run.playback.dominantScene ?? "Mixed trial flow"}
                      </p>
                    </div>
                    <span className="rounded-full border border-[rgba(212,168,103,0.24)] px-4 py-2 text-[0.65rem] uppercase tracking-[0.28em] text-[var(--accent-soft)] transition group-hover:border-[rgba(212,168,103,0.4)] group-hover:bg-white/[0.04]">
                      Open simulation
                    </span>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </section>
      </section>
    </main>
  );
}
