"use client";

import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";

import { useCaseFileCatalog } from "@/hooks/use-case-file-catalog";
import { useSimulationRunCatalog } from "@/hooks/use-simulation-run-catalog";
import type { StoredCaseFile } from "@/lib/case-files";
import {
  formatDuration,
  formatEvaluationScore,
  formatRunDate,
  getCaseTypeLabel,
  getStatusLabel,
  getVerdictLabel,
  type SimulationRunCatalogItem,
} from "@/lib/simulation-runs";

type ViewFilter = "all" | "draft" | "active" | "completed";
type SortOption = "updated" | "created" | "title";

const FILTER_OPTIONS: Array<{ label: string; value: ViewFilter }> = [
  { label: "All", value: "all" },
  { label: "Draft", value: "draft" },
  { label: "Active", value: "active" },
  { label: "Completed", value: "completed" },
];

const SORT_OPTIONS: Array<{ label: string; value: SortOption }> = [
  { label: "Recently updated", value: "updated" },
  { label: "Recently created", value: "created" },
  { label: "Case title", value: "title" },
];

function SearchIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 20 20" className="h-4 w-4 fill-none stroke-current">
      <circle cx="8.5" cy="8.5" r="5.5" strokeWidth="1.6" />
      <path d="M12.5 12.5 17 17" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

function CalendarIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 20 20" className="h-4 w-4 fill-none stroke-current">
      <rect x="3" y="4.5" width="14" height="12" rx="2.5" strokeWidth="1.4" />
      <path d="M6.5 3v3M13.5 3v3M3 8.5h14" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 20 20" className="h-4 w-4 fill-none stroke-current">
      <circle cx="10" cy="10" r="7" strokeWidth="1.4" />
      <path d="M10 6.4v4.2l2.8 1.8" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function TranscriptIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 20 20" className="h-4 w-4 fill-none stroke-current">
      <rect x="3" y="3.5" width="14" height="13" rx="2.2" strokeWidth="1.4" />
      <path d="M6.2 7.2h7.6M6.2 10h7.6M6.2 12.8h4.4" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function ScaleIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 20 20" className="h-4 w-4 fill-none stroke-current">
      <path d="M10 3v11.5M6 5.5h8M4.5 7.5l-2 3.7a2.8 2.8 0 0 0 2.5 1.7h1a2.8 2.8 0 0 0 2.5-1.7l-2-3.7M15.5 7.5l-2 3.7a2.8 2.8 0 0 0 2.5 1.7h1a2.8 2.8 0 0 0 2.5-1.7l-2-3.7M7 16.2h6" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ArrowIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 20 20" className="h-4 w-4 fill-none stroke-current">
      <path d="M4 10h11.5M11 5.5 16 10l-5 4.5" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function pluralize(count: number, singular: string, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`;
}

function formatRelativeTime(value: string) {
  const deltaMs = Date.now() - new Date(value).getTime();
  const deltaMinutes = Math.max(1, Math.round(deltaMs / 60000));

  if (deltaMinutes < 60) {
    return `Updated ${deltaMinutes} minute${deltaMinutes === 1 ? "" : "s"} ago`;
  }

  const deltaHours = Math.round(deltaMinutes / 60);
  if (deltaHours < 24) {
    return `Updated ${deltaHours} hour${deltaHours === 1 ? "" : "s"} ago`;
  }

  const deltaDays = Math.round(deltaHours / 24);
  return `Updated ${deltaDays} day${deltaDays === 1 ? "" : "s"} ago`;
}

function getDraftReadiness(caseFile: StoredCaseFile) {
  const checks = [
    caseFile.case_file.case_title.trim().length > 0,
    caseFile.case_file.charge_or_claim.trim().length > 0,
    caseFile.case_file.parties.plaintiff_or_prosecution.trim().length > 0,
    caseFile.case_file.parties.defendant.trim().length > 0,
    caseFile.case_file.jurisdiction.state.trim().length > 0,
    caseFile.case_file.witnesses.length > 0,
    caseFile.case_file.evidence.length > 0,
    caseFile.case_file.disputed_facts.length > 0,
  ];

  const filled = checks.filter(Boolean).length;
  const total = checks.length;
  const missing = total - filled;
  const completion = Math.round((filled / total) * 100);

  if (missing === 0) {
    return {
      completion,
      label: "Ready for simulation",
      tone: "border-[#c7d4c8] bg-[#eff6ef] text-[#1f4f39]",
    };
  }

  return {
    completion,
    label: `${missing} detail${missing === 1 ? "" : "s"} missing`,
    tone: "border-[#e2d2af] bg-[#fbf5e8] text-[#7c5b1d]",
  };
}

function matchesSearch(haystack: string, searchTerm: string) {
  return haystack.toLowerCase().includes(searchTerm.trim().toLowerCase());
}

function compareText(a: string, b: string) {
  return a.localeCompare(b, undefined, { sensitivity: "base" });
}

function sortDraftCaseFiles(caseFiles: StoredCaseFile[], sortBy: SortOption) {
  return [...caseFiles].sort((left, right) => {
    if (sortBy === "title") {
      return compareText(left.case_file.case_title, right.case_file.case_title);
    }

    const leftDate = new Date(sortBy === "created" ? left.created_at : left.updated_at).getTime();
    const rightDate = new Date(sortBy === "created" ? right.created_at : right.updated_at).getTime();
    return rightDate - leftDate;
  });
}

function sortRuns(runs: SimulationRunCatalogItem[], sortBy: SortOption) {
  return [...runs].sort((left, right) => {
    if (sortBy === "title") {
      const leftTitle = `${left.caseFile.plaintiffOrProsecution} v. ${left.caseFile.defendant}`;
      const rightTitle = `${right.caseFile.plaintiffOrProsecution} v. ${right.caseFile.defendant}`;
      return compareText(leftTitle, rightTitle);
    }

    const leftDate = new Date(sortBy === "created" ? left.createdAt : left.completedAt ?? left.createdAt).getTime();
    const rightDate = new Date(sortBy === "created" ? right.createdAt : right.completedAt ?? right.createdAt).getTime();
    return rightDate - leftDate;
  });
}

function SummaryCard({
  label,
  value,
  support,
  tone,
  cardTone,
  icon,
}: {
  label: string;
  value: number;
  support: string;
  tone: string;
  cardTone: string;
  icon: ReactNode;
}) {
  return (
    <article
      className={`rounded-[24px] border p-5 shadow-[0_18px_40px_rgba(15,23,42,0.06)] ${cardTone}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-[#526071]">{label}</p>
          <p className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-[#142033]">{value}</p>
        </div>
        <span className={`inline-flex h-10 w-10 items-center justify-center rounded-2xl border ${tone}`}>
          {icon}
        </span>
      </div>
      <p className="mt-3 text-sm leading-6 text-[#627084]">{support}</p>
    </article>
  );
}

function Header() {
  return (
    <header className="border-b border-[#d9e0ea] pb-8">
      <div className="max-w-3xl">
        <p className="text-sm font-medium text-[#5d6c7f]">Courtroom operations</p>
        <h1 className="font-display mt-2 text-[2.05rem] leading-[1.02] tracking-[-0.045em] text-[#142033] sm:text-[2.45rem]">
          Courtroom workspace
        </h1>
        <p className="mt-3 max-w-2xl text-[0.98rem] leading-7 text-[#526071]">
          Manage draft case files and review simulation activity from one workspace.
        </p>
      </div>
    </header>
  );
}

function Toolbar({
  filter,
  onFilterChange,
  onSearchChange,
  onSortChange,
  searchValue,
  sortBy,
}: {
  filter: ViewFilter;
  onFilterChange: (value: ViewFilter) => void;
  onSearchChange: (value: string) => void;
  onSortChange: (value: SortOption) => void;
  searchValue: string;
  sortBy: SortOption;
}) {
  return (
    <section className="mt-8 rounded-[24px] border border-[#d9e0ea] bg-[#fcfaf6] p-4 shadow-[0_10px_25px_rgba(15,23,42,0.04)]">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap gap-2">
          {FILTER_OPTIONS.map((option) => {
            const selected = option.value === filter;
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => onFilterChange(option.value)}
                className={`inline-flex h-10 items-center rounded-full border px-4 text-sm font-medium transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#162338] focus-visible:ring-offset-2 focus-visible:ring-offset-[#fcfaf6] ${
                  selected
                    ? "border-[#162338] bg-[#162338] text-[#f8f4ec]"
                    : "border-[#ccd5e2] bg-[#fffdf9] text-[#344255] hover:border-[#98a8bd] hover:bg-[#f8fafc]"
                }`}
                aria-pressed={selected}
              >
                {option.label}
              </button>
            );
          })}
        </div>

        <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_13rem] lg:w-[32rem]">
          <label className="flex h-11 items-center gap-3 rounded-2xl border border-[#ccd5e2] bg-[#fffdf9] px-4 text-sm text-[#526071] focus-within:border-[#6e829f] focus-within:ring-2 focus-within:ring-[#c8d5e6]">
            <SearchIcon />
            <span className="sr-only">Search case files and simulations</span>
            <input
              value={searchValue}
              onChange={(event) => onSearchChange(event.target.value)}
              placeholder="Search cases or charges"
              className="w-full bg-transparent text-[#162338] outline-none placeholder:text-[#8a98a9]"
            />
          </label>

          <label className="flex h-11 items-center rounded-2xl border border-[#ccd5e2] bg-[#fffdf9] px-4 text-sm text-[#344255] focus-within:border-[#6e829f] focus-within:ring-2 focus-within:ring-[#c8d5e6]">
            <span className="sr-only">Sort records</span>
            <select
              value={sortBy}
              onChange={(event) => onSortChange(event.target.value as SortOption)}
              className="w-full bg-transparent outline-none"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>
    </section>
  );
}

function SectionHeading({
  title,
  count,
  description,
  action,
}: {
  title: string;
  count: number;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h2 className="font-display text-[1.45rem] leading-tight tracking-[-0.035em] text-[#142033]">
          {title} <span className="text-[#607084]">· {count}</span>
        </h2>
        <p className="mt-1 text-sm leading-6 text-[#5a697d]">{description}</p>
      </div>
      {action ? <div className="pt-2 sm:pt-0">{action}</div> : null}
    </div>
  );
}

function EmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-[24px] border border-dashed border-[#cfd7e3] bg-[#fffdf9] px-5 py-7 text-sm leading-6 text-[#566577]">
      <p className="font-medium text-[#1b2940]">{title}</p>
      <p className="mt-1">{description}</p>
    </div>
  );
}

function DashboardStatus({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <main className="min-h-screen bg-[#f3f1ec] px-4 py-6 text-[#182233] sm:px-6 sm:py-8">
      <section className="mx-auto w-full max-w-[88rem]">
        <div className="rounded-[32px] border border-[#d9e0ea] bg-[#fffdf9] p-6 shadow-[0_24px_60px_rgba(15,23,42,0.08)] sm:p-8">
          <Header />
          <div className="mt-12 max-w-xl">
            <h2 className="font-display text-[1.7rem] leading-tight tracking-[-0.035em] text-[#142033]">
              {title}
            </h2>
            <p className="mt-3 text-sm leading-6 text-[#526071]">{description}</p>
            {action ? <div className="mt-6">{action}</div> : null}
          </div>
        </div>
      </section>
    </main>
  );
}

function LoadingSkeleton() {
  return (
    <main className="min-h-screen bg-[#f3f1ec] px-4 py-6 sm:px-6 sm:py-8">
      <section className="mx-auto w-full max-w-[88rem] rounded-[32px] border border-[#d9e0ea] bg-[#fffdf9] p-6 shadow-[0_24px_60px_rgba(15,23,42,0.08)] sm:p-8">
        <Header />

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <div
              key={index}
              className="h-[9.5rem] animate-pulse rounded-[24px] border border-[#dfe5ed] bg-[#f6f8fb]"
            />
          ))}
        </div>

        <div className="mt-8 h-[5.5rem] animate-pulse rounded-[24px] border border-[#dfe5ed] bg-[#f6f8fb]" />

        <section className="mt-10">
          <div className="h-12 w-72 animate-pulse rounded-2xl bg-[#eef2f7]" />
          <div className="mt-5 grid gap-4 lg:grid-cols-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <div
                key={index}
                className="h-[15rem] animate-pulse rounded-[24px] border border-[#dfe5ed] bg-[#f6f8fb]"
              />
            ))}
          </div>
        </section>

        <section className="mt-12">
          <div className="h-12 w-80 animate-pulse rounded-2xl bg-[#eef2f7]" />
          <div className="mt-5 grid gap-4">
            {Array.from({ length: 2 }).map((_, index) => (
              <div
                key={index}
                className="h-[15.5rem] animate-pulse rounded-[24px] border border-[#dfe5ed] bg-[#f6f8fb]"
              />
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}

function DraftCaseCard({ caseFile }: { caseFile: StoredCaseFile }) {
  const witnessCount = caseFile.case_file.witnesses.length;
  const evidenceCount = caseFile.case_file.evidence.length;
  const factCount = caseFile.case_file.disputed_facts.length;
  const readiness = getDraftReadiness(caseFile);
  const metadata = [
    pluralize(witnessCount, "witness"),
    pluralize(evidenceCount, "evidence item"),
    pluralize(factCount, "disputed fact"),
  ].join(" · ");
  const title = caseFile.case_file.case_title.trim() || "Untitled case";
  const jurisdiction = caseFile.case_file.jurisdiction.state.trim();

  return (
    <Link
      href={`/case-files/${caseFile.id}`}
      className="group flex h-full flex-col rounded-[24px] border border-[#e3ddd1] bg-[linear-gradient(180deg,#fffefb_0%,#fbf4e9_100%)] p-5 shadow-[0_14px_30px_rgba(15,23,42,0.05)] transition-all duration-150 hover:-translate-y-0.5 hover:border-[#c8b78e] hover:shadow-[0_18px_36px_rgba(124,91,29,0.12)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#162338] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f3f1ec]"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center rounded-full border border-[#e2d2af] bg-[#fbf5e8] px-3 py-1 text-[0.75rem] font-semibold text-[#7c5b1d]">
            Draft
          </span>
          <span className="text-sm font-medium text-[#5d6c7f]">
            {getCaseTypeLabel(caseFile.case_file.case_type)}
          </span>
        </div>
        <span className={`inline-flex rounded-full border px-3 py-1 text-[0.75rem] font-semibold ${readiness.tone}`}>
          {readiness.completion}% complete
        </span>
      </div>

      <div className="mt-4 rounded-[20px] bg-[linear-gradient(135deg,rgba(251,245,232,0.95),rgba(255,253,249,0.65))] p-4">
        <h3 className="text-[1.24rem] leading-tight font-semibold tracking-[-0.03em] text-[#142033]">
          {title}
        </h3>
        <p className="mt-2 line-clamp-2 text-sm leading-6 text-[#324255]">
          {caseFile.case_file.charge_or_claim || "Charge or matter summary pending."}
        </p>
      </div>

      <div className="mt-4 space-y-2 text-sm text-[#526071]">
        <p>{metadata}</p>
        <p>
          {jurisdiction ? `${jurisdiction} jurisdiction` : "Jurisdiction pending"} ·{" "}
          {readiness.label}
        </p>
        <p>{formatRelativeTime(caseFile.updated_at)}</p>
      </div>

      <div className="mt-auto flex items-center justify-between pt-5 text-sm font-semibold text-[#162338]">
        <span>Continue editing</span>
        <span className="inline-flex items-center gap-1 transition-transform duration-150 group-hover:translate-x-0.5">
          <span className="sr-only">Open case file</span>
          <ArrowIcon />
        </span>
      </div>
    </Link>
  );
}

function SimulationStatusBadge({ status }: { status: string }) {
  const tone =
    status === "completed"
      ? "border-[#c7d4c8] bg-[#eff6ef] text-[#1f4f39]"
      : "border-[#bfd1e7] bg-[#edf4fb] text-[#194a7a]";

  return (
    <span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[0.75rem] font-semibold ${tone}`}>
      <span
        aria-hidden="true"
        className={`h-2 w-2 rounded-full ${status === "completed" ? "bg-[#2d6a4f]" : "bg-[#2563a6]"}`}
      />
      {getStatusLabel(status)}
    </span>
  );
}

function RunMetadataItem({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-[#e0e6ee] bg-[#fbfcfe] px-3.5 py-3">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.08em] text-[#758398]">
        {icon}
        <span>{label}</span>
      </div>
      <p className="mt-2 text-sm font-medium leading-6 text-[#1c2a3f]">{value}</p>
    </div>
  );
}

function SimulationRunCard({ run }: { run: SimulationRunCatalogItem }) {
  const isCompleted = run.status === "completed";
  const cardTone = isCompleted
    ? "border-[#d7e2d7] bg-[linear-gradient(180deg,#fffefb_0%,#f2f8f0_100%)] shadow-[0_18px_36px_rgba(45,106,79,0.09)]"
    : "border-[#d8dee8] bg-[linear-gradient(180deg,#f8fafc_0%,#eff3f8_100%)] opacity-75";
  const title = `${run.caseFile.plaintiffOrProsecution} v. ${run.caseFile.defendant}`;
  const secondaryStats = [
    pluralize(run.playback.turnCount, "turn"),
    isCompleted ? formatDuration(run.playback.durationMs) : "In progress",
    isCompleted ? `Completed ${formatRunDate(run.completedAt)}` : `Opened ${formatRunDate(run.createdAt)}`,
  ];

  if (run.playback.modelName) {
    secondaryStats.splice(2, 0, run.playback.modelName);
  }

  return (
    <article className={`rounded-[24px] border p-5 ${cardTone}`}>
      <div className="flex flex-wrap items-center gap-2">
        <SimulationStatusBadge status={run.status} />
        <span className="text-sm font-medium text-[#5d6c7f]">
          {getCaseTypeLabel(run.caseFile.caseType)}
        </span>
      </div>

      <div
        className={`mt-4 rounded-[20px] p-4 ${
          isCompleted
            ? "bg-[linear-gradient(135deg,rgba(239,246,239,0.95),rgba(255,253,249,0.7))]"
            : "bg-[linear-gradient(135deg,rgba(237,244,251,0.9),rgba(248,250,252,0.75))]"
        }`}
      >
        <h3 className="text-[1.24rem] leading-tight font-semibold tracking-[-0.03em] text-[#142033]">
          {title}
        </h3>
        <p className="mt-2 line-clamp-2 text-sm leading-6 text-[#324255]">
          {run.caseFile.charge}
        </p>
      </div>
      <p className="mt-3 text-sm leading-6 text-[#5a697d]">{secondaryStats.join(" · ")}</p>

      <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <RunMetadataItem icon={<CalendarIcon />} label="Opened" value={formatRunDate(run.createdAt)} />
        <RunMetadataItem
          icon={<ClockIcon />}
          label={isCompleted ? "Duration" : "Status"}
          value={isCompleted ? formatDuration(run.playback.durationMs) : "Simulation running"}
        />
        <RunMetadataItem
          icon={<TranscriptIcon />}
          label="Transcript"
          value={pluralize(run.playback.turnCount, "turn")}
        />
        <RunMetadataItem
          icon={<ScaleIcon />}
          label={isCompleted ? "Evaluation" : "Verdict"}
          value={
            isCompleted
              ? formatEvaluationScore(run.playback.evaluationScore)
              : getVerdictLabel(run.playback.verdictLabel)
          }
        />
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-3">
        {isCompleted ? (
          <Link
            href={`/simulations/${run.simulationRunId}`}
            className="inline-flex h-11 items-center justify-center gap-2 rounded-2xl border border-[#162338] bg-[#162338] px-4 text-sm font-semibold text-[#f8f4ec] transition-colors duration-150 hover:bg-[#1e2f49] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#162338] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f3f1ec]"
          >
            Review playback
            <ArrowIcon />
          </Link>
        ) : (
          <div
            aria-disabled="true"
            className="inline-flex items-center rounded-2xl border border-[#c9d3e2] bg-[#edf1f6] px-4 py-2.5 text-sm font-medium text-[#5d6c7f]"
          >
            Playback will appear here when processing completes.
          </div>
        )}
      </div>
    </article>
  );
}

export function SimulationLibraryPage() {
  const {
    caseFiles,
    errorMessage: caseFileError,
    reload: reloadCaseFiles,
    requestState: caseFileRequestState,
  } = useCaseFileCatalog();
  const {
    catalog,
    errorMessage: runError,
    reload: reloadRuns,
    requestState: runRequestState,
  } = useSimulationRunCatalog();
  const [filter, setFilter] = useState<ViewFilter>("all");
  const [sortBy, setSortBy] = useState<SortOption>("updated");
  const [searchValue, setSearchValue] = useState("");

  useEffect(() => {
    document.body.classList.add("body-light-surface");

    return () => {
      document.body.classList.remove("body-light-surface");
    };
  }, []);

  const retry = () => {
    reloadCaseFiles();
    reloadRuns();
  };

  const filteredDraftCaseFiles = useMemo(() => {
    const drafts = caseFiles.filter((caseFile) => caseFile.status === "draft");
    const matchingDrafts = drafts.filter((caseFile) =>
      matchesSearch(
        [
          caseFile.case_file.case_title,
          caseFile.case_file.charge_or_claim,
          caseFile.case_file.parties.plaintiff_or_prosecution,
          caseFile.case_file.parties.defendant,
        ].join(" "),
        searchValue,
      ),
    );

    return sortDraftCaseFiles(matchingDrafts, sortBy);
  }, [caseFiles, searchValue, sortBy]);

  const { activeRuns, completedRuns, visibleRuns } = useMemo(() => {
    const matchingRuns = catalog.filter((run) =>
      matchesSearch(
        [
          run.caseFile.plaintiffOrProsecution,
          run.caseFile.defendant,
          run.caseFile.charge,
          run.caseFile.jurisdictionLabel ?? "",
        ].join(" "),
        searchValue,
      ),
    );

    const active = matchingRuns.filter((run) => run.status !== "completed");
    const completed = matchingRuns.filter((run) => run.status === "completed");

    return {
      activeRuns: sortRuns(active, sortBy),
      completedRuns: sortRuns(completed, sortBy),
      visibleRuns:
        filter === "active"
          ? sortRuns(active, sortBy)
          : filter === "completed"
            ? sortRuns(completed, sortBy)
            : [...sortRuns(completed, sortBy), ...sortRuns(active, sortBy)],
    };
  }, [catalog, filter, searchValue, sortBy]);

  const draftCount = caseFiles.filter((caseFile) => caseFile.status === "draft").length;
  const activeCount = catalog.filter((run) => run.status !== "completed").length;
  const completedCount = catalog.filter((run) => run.status === "completed").length;

  const showDraftSection = filter === "all" || filter === "draft";
  const showSimulationSection = filter === "all" || filter === "active" || filter === "completed";

  if (
    caseFileRequestState === "loading" ||
    caseFileRequestState === "idle" ||
    runRequestState === "loading" ||
    runRequestState === "idle"
  ) {
    return <LoadingSkeleton />;
  }

  if (caseFileRequestState === "error" || runRequestState === "error") {
    return (
      <DashboardStatus
        title="Workspace unavailable"
        description={
          caseFileError ??
          runError ??
          "The home dashboard could not be loaded from the backend."
        }
        action={
          <button
            type="button"
            onClick={retry}
            className="inline-flex h-11 items-center justify-center rounded-2xl border border-[#162338] bg-[#162338] px-4 text-sm font-semibold text-[#f8f4ec] transition-colors duration-150 hover:bg-[#1e2f49] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#162338] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f3f1ec]"
          >
            Retry
          </button>
        }
      />
    );
  }

  return (
    <main className="min-h-screen bg-[#f3f1ec] px-4 py-6 text-[#182233] sm:px-6 sm:py-8">
      <section className="mx-auto w-full max-w-[88rem] rounded-[32px] border border-[#d9e0ea] bg-[#fffdf9] p-6 shadow-[0_24px_60px_rgba(15,23,42,0.08)] sm:p-8">
        <Header />

        <section className="mt-8 grid gap-4 md:grid-cols-3">
          <SummaryCard
            label="Draft cases"
            value={draftCount}
            support="Editable matters waiting for final review or launch."
            tone="border-[#ead9b6] bg-[#fbf4e6] text-[#7b5b20]"
            cardTone="border-[#e6dac0] bg-[linear-gradient(180deg,#fffdf8_0%,#fbf2e2_100%)]"
            icon={<span className="text-lg">D</span>}
          />
          <SummaryCard
            label="Active simulations"
            value={activeCount}
            support="Runs currently processing or awaiting playback readiness."
            tone="border-[#c7d9ee] bg-[#edf4fb] text-[#1f4f7f]"
            cardTone="border-[#d4dfef] bg-[linear-gradient(180deg,#fffefe_0%,#eef4fb_100%)]"
            icon={<span className="text-lg">A</span>}
          />
          <SummaryCard
            label="Completed simulations"
            value={completedCount}
            support="Finished runs ready for playback review and evaluation."
            tone="border-[#cfe1d1] bg-[#eff6ef] text-[#29563e]"
            cardTone="border-[#d8e4d8] bg-[linear-gradient(180deg,#fffefb_0%,#eef6ef_100%)]"
            icon={<span className="text-lg">C</span>}
          />
        </section>

        <Toolbar
          filter={filter}
          onFilterChange={setFilter}
          onSearchChange={setSearchValue}
          onSortChange={setSortBy}
          searchValue={searchValue}
          sortBy={sortBy}
        />

        {showSimulationSection ? (
          <section className="mt-10">
            <SectionHeading
              title="Simulations"
              count={visibleRuns.length}
              description="Completed playback stays first. In-progress runs remain visible here until assets are ready."
            />

            <div className="mt-5">
              {visibleRuns.length === 0 ? (
                <EmptyState
                  title="No simulations yet."
                  description="Launch a draft case file to start a new simulation run."
                />
              ) : (
                <div className="grid gap-4">
                  {visibleRuns.map((run) => (
                    <SimulationRunCard key={run.simulationRunId} run={run} />
                  ))}
                </div>
              )}
            </div>
          </section>
        ) : null}

        {showDraftSection ? (
          <section className="mt-12">
            <SectionHeading
              title="Case files"
              count={filteredDraftCaseFiles.length}
              description="Editable matters stay compact here until they are ready to launch."
              action={
                <Link
                  href="/case-files/new"
                  className="inline-flex h-11 items-center justify-center rounded-2xl border border-[#162338] bg-[#162338] px-4 text-sm font-semibold text-[#f8f4ec] shadow-[0_14px_26px_rgba(22,35,56,0.18)] transition-all duration-150 hover:-translate-y-0.5 hover:bg-[#1e2f49] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#162338] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f3f1ec]"
                >
                  New case file
                </Link>
              }
            />

            <div className="mt-5">
              {filteredDraftCaseFiles.length === 0 ? (
                <EmptyState
                  title="No draft case files."
                  description="Create a new matter to begin drafting, or adjust the current filters."
                />
              ) : (
                <div className="grid gap-4 lg:grid-cols-2">
                  {filteredDraftCaseFiles.map((caseFile) => (
                    <DraftCaseCard key={caseFile.id} caseFile={caseFile} />
                  ))}
                </div>
              )}
            </div>
          </section>
        ) : null}
      </section>
    </main>
  );
}
