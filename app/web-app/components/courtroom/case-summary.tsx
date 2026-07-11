import {
  getAttorneyName,
  getCaseDateLabel,
  type TranscriptData,
} from "@/lib/courtroom";

function SummaryRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="grid gap-1 border-b border-white/8 py-3 last:border-b-0">
      <dt className="text-[0.65rem] uppercase tracking-[0.32em] text-[var(--muted)]">
        {label}
      </dt>
      <dd className="text-sm leading-6 text-[var(--foreground)]">
        {value}
      </dd>
    </div>
  );
}

export function CaseSummary({ transcript }: { transcript: TranscriptData }) {
  const caseDate = new Date().toDateString();
  const caseType =
    transcript.case_metadata.case_type.charAt(0).toUpperCase() +
    transcript.case_metadata.case_type.slice(1);

  return (
    <section className="panel rounded-[28px] px-5 py-4 lg:px-[1.125rem] lg:py-[0.875rem]">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs uppercase tracking-[0.3em] text-[var(--accent-soft)]">
          Case Details
        </p>
      </div>

      <dl className="mt-3">
        <SummaryRow label="Case Number" value={transcript.case_metadata.case_id} />
        <SummaryRow label="Date" value={caseDate} />
        <SummaryRow label="Case Type" value={caseType} />
      </dl>
    </section>
  );
}
