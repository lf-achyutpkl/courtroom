"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

import { useSimulationRunCatalog } from "@/hooks/use-simulation-run-catalog";
import {
  formatDuration,
  formatRunDate,
  getCaseTypeLabel,
  getStatusLabel,
  getVerdictLabel,
  type SimulationRunCatalogItem,
} from "@/lib/simulation-runs";

const PLACEHOLDER_THUMBNAIL = "/courtroom-placeholder.svg";

type FilterValue = "all" | "criminal" | "civil";
type VerdictFilterValue =
  | "all"
  | "guilty"
  | "not guilty"
  | "liable"
  | "not liable"
  | "pending";
type SortValue = "completed-desc" | "runtime-desc" | "score-desc" | "party-asc";

function getRunTitle(run: SimulationRunCatalogItem) {
  return `${run.caseFile.plaintiffOrProsecution} v. ${run.caseFile.defendant}`;
}

function getJurisdictionLabel(run: SimulationRunCatalogItem) {
  return run.caseFile.jurisdictionLabel ?? "Jurisdiction unavailable";
}

function getVerdictFilterValue(run: SimulationRunCatalogItem): VerdictFilterValue {
  if (!run.playback.verdictLabel) {
    return "pending";
  }

  return run.playback.verdictLabel as Exclude<VerdictFilterValue, "all" | "pending">;
}

function getSearchableText(run: SimulationRunCatalogItem) {
  return [
    getRunTitle(run),
    run.caseFile.charge,
    getCaseTypeLabel(run.caseFile.caseType),
    getJurisdictionLabel(run),
    run.playback.modelName ?? "",
    getVerdictLabel(run.playback.verdictLabel),
  ]
    .join(" ")
    .toLowerCase();
}

function sortRuns(runs: SimulationRunCatalogItem[], sortBy: SortValue) {
  const items = [...runs];

  items.sort((left, right) => {
    if (sortBy === "runtime-desc") {
      return right.playback.durationMs - left.playback.durationMs;
    }

    if (sortBy === "score-desc") {
      return (right.playback.evaluationScore ?? -1) - (left.playback.evaluationScore ?? -1);
    }

    if (sortBy === "party-asc") {
      return getRunTitle(left).localeCompare(getRunTitle(right));
    }

    return new Date(right.completedAt ?? right.createdAt).getTime() -
      new Date(left.completedAt ?? left.createdAt).getTime();
  });

  return items;
}

function LibraryStatus({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <main className="min-h-screen bg-[#e3ddd2] px-4 py-6 text-[#1b1916] sm:px-6 sm:py-8">
      <section className="mx-auto flex min-h-[calc(100vh-3rem)] w-full max-w-6xl items-center">
        <div className="w-full">
          <header className="flex flex-col gap-4 border-b border-[#b5aa99] pb-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="text-[1.4rem] font-medium tracking-[-0.02em] text-[#1b1916]">
                Simulation library
              </h1>
              <p className="mt-1 text-sm leading-6 text-[#554d43]">
                Review trial runs with the discipline of a courtroom analysis desk.
              </p>
            </div>
            <button
              type="button"
              disabled
              className="inline-flex h-10 items-center justify-center rounded-[8px] border border-[#26231f] bg-[#26231f] px-4 text-sm font-medium text-[#f4efe6] disabled:cursor-not-allowed disabled:opacity-100"
            >
              New simulation
            </button>
          </header>

          <div className="py-12 sm:py-16">
            <div className="max-w-xl">
              <p className="text-base text-[#1b1916]">{title}</p>
              <p className="mt-2 text-sm leading-6 text-[#554d43]">{description}</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

function Thumbnail({
  title,
  priority = false,
}: {
  title: string;
  priority?: boolean;
}) {
  return (
    <div className="overflow-hidden rounded-[8px] border border-[#d1c5b3] bg-[#e7dece]">
      <Image
        src={PLACEHOLDER_THUMBNAIL}
        alt={`${title} placeholder courtroom thumbnail`}
        width={1200}
        height={800}
        priority={priority}
        className="h-full w-full object-cover"
      />
    </div>
  );
}

function MetaItem({
  label,
  value,
}: {
  label: string;
  value: string | number | null | undefined;
}) {
  return (
    <div>
      <dt className="text-[0.72rem] text-[#6a6156]">{label}</dt>
      <dd className="mt-1 text-sm text-[#1b1916]">{value ?? "Unavailable"}</dd>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const isCompleted = status === "completed";

  return (
    <span
      className={`inline-flex h-7 items-center rounded-[7px] border px-2.5 text-[0.78rem] font-medium ${
        isCompleted
          ? "border-[#8a7e6c] bg-[#ddd2c1] text-[#1f1b17]"
          : "border-[#9c7f54] bg-[#e8d8c2] text-[#4d3515]"
      }`}
    >
      {getStatusLabel(status)}
    </span>
  );
}

function CompareToggle({
  selected,
  onToggle,
}: {
  selected: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onToggle}
      className={`inline-flex h-9 items-center rounded-[8px] border px-3 text-sm transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#efe8dc] ${
        selected
          ? "border-[#26231f] bg-[#26231f] text-[#f4efe6]"
          : "border-[#b5aa99] bg-[#f7f1e8] text-[#26231f] hover:bg-[#ece4d7]"
      }`}
    >
      {selected ? "Selected" : "Compare"}
    </button>
  );
}

export function SimulationLibraryPage() {
  const { catalog, errorMessage, requestState } = useSimulationRunCatalog();
  const [searchQuery, setSearchQuery] = useState("");
  const [caseTypeFilter, setCaseTypeFilter] = useState<FilterValue>("all");
  const [verdictFilter, setVerdictFilter] = useState<VerdictFilterValue>("all");
  const [sortBy, setSortBy] = useState<SortValue>("completed-desc");
  const [comparisonIds, setComparisonIds] = useState<string[]>([]);

  if (requestState === "loading" || requestState === "idle") {
    return (
      <LibraryStatus
        title="Loading completed simulations"
        description="Pulling finished courtroom runs that are ready to open in playback."
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
        description="Completed runs will appear here once the backend finishes generating playback assets."
      />
    );
  }

  const filteredRuns = sortRuns(
    catalog.filter((run) => {
      const matchesSearch =
        searchQuery.trim().length === 0 ||
        getSearchableText(run).includes(searchQuery.trim().toLowerCase());
      const matchesCaseType =
        caseTypeFilter === "all" || run.caseFile.caseType === caseTypeFilter;
      const matchesVerdict =
        verdictFilter === "all" || getVerdictFilterValue(run) === verdictFilter;

      return matchesSearch && matchesCaseType && matchesVerdict;
    }),
    sortBy,
  );

  const hasSingleSimulation = catalog.length === 1;
  const primaryRun = filteredRuns[0] ?? catalog[0];
  const selectedComparisonCount = filteredRuns.filter((run) =>
    comparisonIds.includes(run.simulationRunId),
  ).length;

  function toggleComparison(runId: string) {
    setComparisonIds((current) => {
      if (current.includes(runId)) {
        return current.filter((value) => value !== runId);
      }

      if (current.length === 2) {
        return [current[1], runId];
      }

      return [...current, runId];
    });
  }

  return (
    <main className="min-h-screen bg-[#e3ddd2] px-4 py-6 text-[#1b1916] sm:px-6 sm:py-8">
      <section className="mx-auto w-full max-w-6xl">
        <div className="space-y-6">
          <header className="border-b border-[#b5aa99] pb-4">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div className="max-w-3xl">
                <h1 className="text-[1.5rem] font-medium tracking-[-0.025em] text-[#1b1916]">
                  Simulation library
                </h1>
                <p className="mt-1 text-sm leading-6 text-[#554d43]">
                  Review finished trial runs, compare outcomes, and open the right matter without
                  scanning unnecessary detail.
                </p>
              </div>

              <button
                type="button"
                disabled
                className="inline-flex h-10 items-center justify-center rounded-[8px] border border-[#26231f] bg-[#26231f] px-4 text-sm font-medium text-[#f4efe6] disabled:cursor-not-allowed disabled:opacity-100"
              >
                New simulation
              </button>
            </div>
          </header>

          <section className="rounded-[10px] bg-[#f1ebe0] px-5 py-5 shadow-[inset_0_0_0_1px_rgba(109,98,82,0.2)] sm:px-6 sm:py-6">
            <div className="space-y-4">
              <Link
                href={`/simulations/${primaryRun.simulationRunId}`}
                className="group block rounded-[8px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f1ebe0]"
              >
                <div className="grid items-start gap-5 rounded-[8px] transition-colors duration-150 group-hover:bg-[#ebe2d3] group-focus-visible:bg-[#ebe2d3] lg:grid-cols-[minmax(0,1.25fr)_248px] lg:p-2">
                  <div className="space-y-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge status={primaryRun.status} />
                      <span className="text-sm text-[#554d43]">
                        {getCaseTypeLabel(primaryRun.caseFile.caseType)}
                      </span>
                      <span className="text-[#9e917c]" aria-hidden="true">
                        /
                      </span>
                      <span className="text-sm text-[#554d43]">
                        {getJurisdictionLabel(primaryRun)}
                      </span>
                    </div>

                    <div>
                      <h2 className="max-w-3xl text-[1.5rem] leading-tight font-medium tracking-[-0.03em] text-[#1b1916] sm:text-[1.85rem]">
                        {getRunTitle(primaryRun)}
                      </h2>
                      <p className="mt-2 max-w-2xl text-sm leading-6 text-[#423c34]">
                        {primaryRun.caseFile.charge}
                      </p>
                    </div>

                    <dl className="grid gap-x-6 gap-y-4 sm:grid-cols-2 xl:grid-cols-3">
                      <MetaItem label="Simulation completed" value={formatRunDate(primaryRun.completedAt)} />
                      <MetaItem label="Witnesses" value={primaryRun.caseFile.witnessCount} />
                      <MetaItem label="Evidence items" value={primaryRun.caseFile.evidenceCount} />
                      <MetaItem label="Runtime" value={formatDuration(primaryRun.playback.durationMs)} />
                      <MetaItem label="Model" value={primaryRun.playback.modelName} />
                    </dl>
                  </div>

                  <div className="max-w-[248px] rounded-[8px] bg-[#e7dece] p-3 shadow-[inset_0_0_0_1px_rgba(109,98,82,0.14)]">
                    <Thumbnail title={getRunTitle(primaryRun)} priority />
                  </div>
                </div>
              </Link>

              <div className="flex flex-wrap items-center gap-3">
                <Link
                  href={`/simulations/${primaryRun.simulationRunId}`}
                  className="inline-flex h-10 items-center rounded-[8px] bg-[#26231f] px-4 text-sm font-medium text-[#f4efe6] transition-colors duration-150 hover:bg-[#36312b] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f1ebe0]"
                >
                  Open simulation
                </Link>
              </div>
            </div>
          </section>

          {hasSingleSimulation ? null : (
            <>
              <section className="border-b border-[#b5aa99] pb-4">
                <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_180px_180px_180px_auto]">
                  <label className="flex flex-col gap-2">
                    <span className="text-sm text-[#4f483f]">Search</span>
                    <input
                      type="search"
                      value={searchQuery}
                      onChange={(event) => setSearchQuery(event.target.value)}
                      placeholder="Search party, charge, jurisdiction, model"
                      className="h-10 rounded-[8px] border border-[#b5aa99] bg-[#f8f3ea] px-3 text-sm text-[#1b1916] outline-none transition-colors duration-150 placeholder:text-[#857968] focus:border-[#26231f]"
                    />
                  </label>

                  <label className="flex flex-col gap-2">
                    <span className="text-sm text-[#4f483f]">Case type</span>
                    <select
                      value={caseTypeFilter}
                      onChange={(event) => setCaseTypeFilter(event.target.value as FilterValue)}
                      className="h-10 rounded-[8px] border border-[#b5aa99] bg-[#f8f3ea] px-3 text-sm text-[#1b1916] outline-none transition-colors duration-150 focus:border-[#26231f]"
                    >
                      <option value="all">All matters</option>
                      <option value="criminal">Criminal</option>
                      <option value="civil">Civil</option>
                    </select>
                  </label>

                  <label className="flex flex-col gap-2">
                    <span className="text-sm text-[#4f483f]">Verdict</span>
                    <select
                      value={verdictFilter}
                      onChange={(event) =>
                        setVerdictFilter(event.target.value as VerdictFilterValue)
                      }
                      className="h-10 rounded-[8px] border border-[#b5aa99] bg-[#f8f3ea] px-3 text-sm text-[#1b1916] outline-none transition-colors duration-150 focus:border-[#26231f]"
                    >
                      <option value="all">All verdicts</option>
                      <option value="guilty">Guilty</option>
                      <option value="not guilty">Not guilty</option>
                      <option value="liable">Liable</option>
                      <option value="not liable">Not liable</option>
                      <option value="pending">Verdict pending</option>
                    </select>
                  </label>

                  <label className="flex flex-col gap-2">
                    <span className="text-sm text-[#4f483f]">Sort</span>
                    <select
                      value={sortBy}
                      onChange={(event) => setSortBy(event.target.value as SortValue)}
                      className="h-10 rounded-[8px] border border-[#b5aa99] bg-[#f8f3ea] px-3 text-sm text-[#1b1916] outline-none transition-colors duration-150 focus:border-[#26231f]"
                    >
                      <option value="completed-desc">Newest completed</option>
                      <option value="runtime-desc">Longest runtime</option>
                      <option value="score-desc">Highest score</option>
                      <option value="party-asc">Party name</option>
                    </select>
                  </label>

                  <div className="flex items-end">
                    <button
                      type="button"
                      disabled={selectedComparisonCount < 2}
                      className="inline-flex h-10 w-full items-center justify-center rounded-[8px] border border-[#26231f] bg-[#26231f] px-4 text-sm font-medium text-[#f4efe6] transition-colors duration-150 disabled:cursor-not-allowed disabled:border-[#b5aa99] disabled:bg-[#d8cfbf] disabled:text-[#72685b]"
                    >
                      Compare {selectedComparisonCount === 0 ? "runs" : selectedComparisonCount}
                    </button>
                  </div>
                </div>
              </section>

              <section aria-labelledby="all-simulations-heading">
                <div className="flex items-center justify-between border-b border-[#b5aa99] pb-3">
                  <h2 id="all-simulations-heading" className="text-base font-medium text-[#1b1916]">
                    All simulations
                  </h2>
                  <p className="text-sm text-[#554d43]">
                    {filteredRuns.length} of {catalog.length} shown
                  </p>
                </div>

                {filteredRuns.length === 0 ? (
                  <div className="mt-3 rounded-[10px] bg-[#efe8dc] px-5 py-8 shadow-[inset_0_0_0_1px_rgba(109,98,82,0.16)]">
                    <p className="text-base text-[#1b1916]">No simulations match the current filters.</p>
                    <p className="mt-2 text-sm leading-6 text-[#554d43]">
                      Adjust the search, verdict, or case-type filters to restore matching matters.
                    </p>
                  </div>
                ) : (
                  <div className="mt-3 rounded-[10px] bg-[#efe8dc] shadow-[inset_0_0_0_1px_rgba(109,98,82,0.16)]">
                    {filteredRuns.map((run) => {
                      const isSelected = comparisonIds.includes(run.simulationRunId);

                      return (
                        <article
                          key={run.simulationRunId}
                          className="grid gap-3 border-b border-[#cdc0ad] px-4 py-4 last:border-b-0 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center sm:px-5"
                        >
                          <Link
                            href={`/simulations/${run.simulationRunId}`}
                            className="group block rounded-[8px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#efe8dc]"
                          >
                            <div className="grid gap-4 rounded-[8px] p-1 transition-colors duration-150 group-hover:bg-[#e7dece] group-focus-visible:bg-[#e7dece] md:grid-cols-[88px_minmax(0,1.4fr)_minmax(240px,0.9fr)] md:items-center">
                              <div className="max-w-[88px]">
                                <Thumbnail title={getRunTitle(run)} />
                              </div>

                              <div className="min-w-0">
                                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-[#6a6156]">
                                  <StatusBadge status={run.status} />
                                  <span>{getCaseTypeLabel(run.caseFile.caseType)}</span>
                                  <span className="text-[#9e917c]" aria-hidden="true">
                                    /
                                  </span>
                                  <span>{getJurisdictionLabel(run)}</span>
                                  <span className="text-[#9e917c]" aria-hidden="true">
                                    /
                                  </span>
                                  <span>{formatRunDate(run.completedAt)}</span>
                                </div>

                                <h3 className="mt-2 text-[1.02rem] leading-6 font-medium tracking-[-0.02em] text-[#1b1916]">
                                  {getRunTitle(run)}
                                </h3>
                                <p className="mt-1 line-clamp-1 text-sm leading-6 text-[#423c34]">
                                  {run.caseFile.charge}
                                </p>
                              </div>

                              <dl className="grid grid-cols-2 gap-x-5 gap-y-2 text-sm text-[#2d2923] md:justify-self-end">
                                <div>
                                  <dt className="text-[0.72rem] text-[#6a6156]">Verdict</dt>
                                  <dd className="mt-1">{getVerdictLabel(run.playback.verdictLabel)}</dd>
                                </div>
                                <div>
                                  <dt className="text-[0.72rem] text-[#6a6156]">Model</dt>
                                  <dd className="mt-1">{run.playback.modelName ?? "Unavailable"}</dd>
                                </div>
                                <div>
                                  <dt className="text-[0.72rem] text-[#6a6156]">Witnesses</dt>
                                  <dd className="mt-1">{run.caseFile.witnessCount}</dd>
                                </div>
                                <div>
                                  <dt className="text-[0.72rem] text-[#6a6156]">Evidence items</dt>
                                  <dd className="mt-1">{run.caseFile.evidenceCount}</dd>
                                </div>
                                <div>
                                  <dt className="text-[0.72rem] text-[#6a6156]">Runtime</dt>
                                  <dd className="mt-1">{formatDuration(run.playback.durationMs)}</dd>
                                </div>
                                <div>
                                  <dt className="text-[0.72rem] text-[#6a6156]">Score</dt>
                                  <dd className="mt-1">{formatEvaluationScore(run.playback.evaluationScore)}</dd>
                                </div>
                              </dl>
                            </div>
                          </Link>

                          <div className="flex flex-wrap items-center justify-end gap-2">
                            <CompareToggle
                              selected={isSelected}
                              onToggle={() => toggleComparison(run.simulationRunId)}
                            />
                          </div>
                        </article>
                      );
                    })}
                  </div>
                )}
              </section>
            </>
          )}
        </div>
      </section>
    </main>
  );
}
