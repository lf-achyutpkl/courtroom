"use client";

import { useState } from "react";

import {
  getAttorneyName,
  getCaseDateLabel,
  getWitnessSpeakerIds,
  type TranscriptData,
} from "@/lib/courtroom";

function DetailRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="py-1.5">
      <dt className="inline text-sm text-[#6a6156]">{label}: </dt>
      <dd className="inline text-sm leading-6 text-[#1b1916]">{value}</dd>
    </div>
  );
}

export function CaseSummary({
  responseSource,
  simulationRunId,
  transcript,
}: {
  responseSource: string;
  simulationRunId: string;
  transcript: TranscriptData;
}) {
  const [expanded, setExpanded] = useState(false);

  const caseDate = getCaseDateLabel(transcript.case_metadata.case_id) ?? "Unavailable";
  const caseType =
    transcript.case_metadata.case_type.charAt(0).toUpperCase() +
    transcript.case_metadata.case_type.slice(1);
  const witnessCount = getWitnessSpeakerIds(transcript).length;
  const presidingSpeaker = Object.keys(transcript.voice_character_map).find((speakerId) =>
    transcript.voice_character_map[speakerId]?.role?.toLowerCase().includes("judge"),
  );
  const judgeName = presidingSpeaker
    ? getAttorneyName(transcript, presidingSpeaker)
    : "Judge";

  return (
    <section className="w-full px-0 py-1">
      <hr/>
      <h2 className="text-base font-medium text-[#1b1916]">Case details</h2>

      <dl className="mt-3">
        <DetailRow label="Charge" value={transcript.case_metadata.charge} />
        <DetailRow label="Case type" value={caseType} />
        <DetailRow label="Date" value={caseDate} />
        <DetailRow label="Presiding judge" value={judgeName} />
        <DetailRow label="Witnesses" value={String(witnessCount)} />
      </dl>

      {expanded ? (
        <dl className="mt-2 border-t border-[#ded2c2] pt-2">
          <DetailRow label="Jurisdiction" value="Unavailable" />
          <DetailRow label="Model" value="gpt-5-mini" />
          <DetailRow label="Run ID" value={simulationRunId} />
          <DetailRow label="Case ID" value={transcript.case_metadata.case_id} />
          <DetailRow label="Source" value={responseSource} />
        </dl>
      ) : null}

      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="mt-3 text-sm font-medium text-[#3c342b] underline decoration-[#b4a490] underline-offset-4 transition-colors duration-150 hover:text-[#1b1916] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f4efe7]"
      >
        {expanded ? "Show less" : "Show more"}
      </button>
    </section>
  );
}
