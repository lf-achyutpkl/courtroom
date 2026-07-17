import {
  getCaseDateLabel,
  getCaseTitle,
  getWitnessSpeakerIds,
  type TranscriptData,
} from "@/lib/courtroom";

export function CourtroomHeader({ transcript }: { transcript: TranscriptData }) {
  const caseTitle = getCaseTitle(transcript);
  const caseType =
    transcript.case_metadata.case_type.charAt(0).toUpperCase() +
    transcript.case_metadata.case_type.slice(1);
  const caseDate = getCaseDateLabel(transcript.case_metadata.case_id);
  const witnessCount = getWitnessSpeakerIds(transcript).length;
  const turnCount = transcript.audio_script_timeline.length;

  return (
    <header className="rounded-[12px] border border-[#c8bcaa] bg-[#f2ebdf] px-6 py-5 sm:px-7">
      <div className="flex flex-col gap-5">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-sm text-[#554d43]">
          <span>{caseType}</span>
          <span className="text-[#9e917c]" aria-hidden="true">/</span>
          <span>{caseDate ?? "Date unavailable"}</span>
          <span className="text-[#9e917c]" aria-hidden="true">/</span>
          <span>{witnessCount} witnesses</span>
          <span className="text-[#9e917c]" aria-hidden="true">/</span>
          <span>{turnCount} transcript turns</span>
        </div>

        <div className="grid gap-3 border-t border-[#d7ccbb] pt-4 lg:grid-cols-[minmax(0,1fr)_14rem] lg:items-start">
          <div>
            <h1 className="max-w-4xl text-[2rem] font-medium leading-[1.02] tracking-[-0.035em] text-[#1b1916] sm:text-[2.75rem]">
              {caseTitle}
            </h1>
            <p className="mt-2 text-base leading-7 text-[#554d43]">
              {transcript.case_metadata.charge}
            </p>
          </div>

          <dl className="grid grid-cols-2 gap-x-4 gap-y-3 border-t border-[#d7ccbb] pt-4 text-sm lg:border-t-0 lg:border-l lg:pl-5 lg:pt-0">
            <div>
              <dt className="text-[0.72rem] text-[#6a6156]">Prosecution</dt>
              <dd className="mt-1 text-[#1b1916]">{transcript.case_metadata.prosecution}</dd>
            </div>
            <div>
              <dt className="text-[0.72rem] text-[#6a6156]">Defendant</dt>
              <dd className="mt-1 text-[#1b1916]">{transcript.case_metadata.defendant}</dd>
            </div>
          </dl>
        </div>
      </div>
    </header>
  );
}
