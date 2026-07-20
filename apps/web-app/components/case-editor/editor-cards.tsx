"use client";

import type { Dispatch, ReactNode, SetStateAction } from "react";
import { useState } from "react";

import type { CardType, CaseFile, DisputedFact, Evidence, SelectedCard, WitnessProfile } from "@/lib/case-files";

import { EditableField, SelectField } from "@/components/case-editor/editor-fields";
import {
  CheckIcon,
  ChevronDownIcon,
  CloseIcon,
  EyeIcon,
  TextButton,
  TrashIcon,
  WarningIcon,
} from "@/components/case-editor/editor-primitives";
import type {
  CompletionSummary,
  EditorTarget,
  RecentCardChange,
} from "@/components/case-editor/editor-workspace-utils";
import {
  formatDisplayValue,
  formatKnowledgeValue,
  getDisputedFactCompletion,
  getEvidenceCompletion,
  getOverviewCompletion,
  getWitnessCompletion,
} from "@/components/case-editor/editor-workspace-utils";

type SavePayload = Partial<CaseFile> | Partial<WitnessProfile> | Partial<Evidence> | Partial<DisputedFact>;

function SummaryStateBadge({
  changed = false,
  summary,
}: {
  changed?: boolean;
  summary: CompletionSummary;
}) {
  if (changed) {
    return (
      <span className="inline-flex items-center rounded-full border border-[#d7b77d] bg-[#fff4de] px-2.5 py-1 text-[0.68rem] font-medium text-[#6f4d19]">
        Changed
      </span>
    );
  }

  if (summary.status === "complete") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-[#d7ded4] bg-[#f6faf4] px-2.5 py-1 text-[0.68rem] font-medium text-[#35523a]">
        <CheckIcon />
        Complete
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-[#e0c7b3] bg-[#fff3ea] px-2.5 py-1 text-[0.68rem] font-medium text-[#8b4f2c]">
      <WarningIcon />
      Needs details
    </span>
  );
}

function SummaryCard({
  body,
  changed = false,
  heading,
  isSelected,
  meta,
  onSelect,
  onView,
  summary,
}: {
  body: string;
  changed?: boolean;
  heading: string;
  isSelected: boolean;
  meta?: string;
  onSelect: () => void;
  onView: () => void;
  summary: CompletionSummary;
}) {
  return (
    <div
      className={`group w-full rounded-[18px] border px-4 py-3.5 text-left transition-all duration-150 sm:px-4 ${
        isSelected
          ? "border-[#cbbca8] bg-[linear-gradient(180deg,#fffdf8_0%,#f6efe3_100%)] shadow-[0_18px_32px_rgba(54,42,23,0.1)] ring-1 ring-[#e3d7c7]"
          : changed
            ? "border-[#d9b67b] bg-[#fffaf0] shadow-[0_16px_28px_rgba(84,61,30,0.08)]"
            : "border-[#ddd2c4] bg-[#fffdfa] shadow-[0_12px_24px_rgba(54,42,23,0.05)] hover:border-[#c6b49a] hover:bg-[#fffaf4]"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <button
          type="button"
          onClick={onSelect}
          className="min-w-0 flex-1 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f0e7]"
        >
          <h3 className="text-[0.98rem] font-medium tracking-[-0.02em] text-[#1c1916]">
            {heading}
          </h3>
          {meta ? <p className="mt-1 text-xs tracking-[0.14em] text-[#7a6b58] uppercase">{meta}</p> : null}
        </button>
        <div className="flex items-start gap-2">
          <SummaryStateBadge changed={changed} summary={summary} />
          <button
            type="button"
            onClick={onView}
            aria-label={`View ${heading}`}
            title="View details"
            className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-[#d8ccbb] bg-[#fffdf8] text-[#2b251f] shadow-[0_8px_18px_rgba(54,42,23,0.08)] transition-all duration-150 hover:-translate-y-0.5 hover:bg-[#f8f0e4] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f0e7]"
          >
            <EyeIcon />
          </button>
        </div>
      </div>
      <button
        type="button"
        onClick={onSelect}
        className="mt-3 block w-full text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f0e7]"
      >
        <p className="line-clamp-3 text-sm leading-6 text-[#4e463d]">{body}</p>
      </button>
      {isSelected ? (
        <p className="mt-3 text-xs font-medium text-[#5d4d3b]">Selected for chat and editing</p>
      ) : null}
    </div>
  );
}

export function OverviewSummaryCard({
  caseFile,
  changed,
  isSelected,
  onSelect,
  onView,
}: {
  caseFile: CaseFile;
  changed: boolean;
  isSelected: boolean;
  onSelect: () => void;
  onView: () => void;
}) {
  const summary = getOverviewCompletion(caseFile);
  const parties = [caseFile.parties.plaintiff_or_prosecution, caseFile.parties.defendant]
    .filter(Boolean)
    .join(" v. ");
  const body = [
    formatDisplayValue(caseFile.charge_or_claim),
    parties ? `Parties: ${parties}` : "Parties not provided",
    caseFile.jurisdiction.court.trim()
      ? `${formatDisplayValue(caseFile.jurisdiction.court)}, ${formatDisplayValue(caseFile.jurisdiction.state)}`
      : `Jurisdiction: ${formatDisplayValue(caseFile.jurisdiction.state)}`,
  ].join(" ");

  return (
    <SummaryCard
      body={body}
      changed={changed}
      heading={caseFile.case_title.trim() || "Untitled case"}
      isSelected={isSelected}
      meta="Case overview"
      onSelect={onSelect}
      onView={onView}
      summary={summary}
    />
  );
}

export function WitnessSummaryCard({
  changed,
  isSelected,
  onSelect,
  onView,
  witness,
}: {
  changed: boolean;
  isSelected: boolean;
  onSelect: () => void;
  onView: () => void;
  witness: WitnessProfile;
}) {
  return (
    <SummaryCard
      body={formatKnowledgeValue(witness.knowledge_scope)}
      changed={changed}
      heading={witness.witness_id.trim() || "Untitled witness"}
      isSelected={isSelected}
      meta={`${witness.persona.trim() || "Role not provided"} • ${witness.called_by}`}
      onSelect={onSelect}
      onView={onView}
      summary={getWitnessCompletion(witness)}
    />
  );
}

export function EvidenceSummaryCard({
  changed,
  evidence,
  isSelected,
  onSelect,
  onView,
}: {
  changed: boolean;
  evidence: Evidence;
  isSelected: boolean;
  onSelect: () => void;
  onView: () => void;
}) {
  return (
    <SummaryCard
      body={formatKnowledgeValue(evidence.description)}
      changed={changed}
      heading={evidence.evidence_id.trim() || "Untitled evidence"}
      isSelected={isSelected}
      meta={`Submitted by ${evidence.submitted_by}`}
      onSelect={onSelect}
      onView={onView}
      summary={getEvidenceCompletion(evidence)}
    />
  );
}

export function DisputedFactSummaryCard({
  changed,
  fact,
  isSelected,
  onSelect,
  onView,
}: {
  changed: boolean;
  fact: DisputedFact;
  isSelected: boolean;
  onSelect: () => void;
  onView: () => void;
}) {
  return (
    <SummaryCard
      body={`${formatKnowledgeValue(fact.text)} Related evidence: Not provided`}
      changed={changed}
      heading={fact.fact_id.trim() || "Untitled disputed fact"}
      isSelected={isSelected}
      meta="Disputed fact"
      onSelect={onSelect}
      onView={onView}
      summary={getDisputedFactCompletion(fact)}
    />
  );
}

export function EmptySectionCard({
  actionLabel,
  message,
  onAction,
}: {
  actionLabel: string;
  message: string;
  onAction: () => void;
}) {
  return (
    <div className="rounded-[18px] border border-dashed border-[#d8ccbe] bg-[#fffdfa] px-4 py-5">
      <p className="text-sm leading-6 text-[#51483f]">{message}</p>
      <TextButton
        className="mt-4 border-[#d7cab8] bg-[#fbf5eb] text-[#2a251f] hover:bg-[#f4ebdd] focus-visible:ring-offset-[#fffdfa]"
        onClick={onAction}
      >
        {actionLabel}
      </TextButton>
    </div>
  );
}

function DrawerShell({
  children,
  title,
  onClose,
}: {
  children: ReactNode;
  title: string;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-40">
      <button
        type="button"
        aria-label="Close editor"
        className="absolute inset-0 bg-[#201910]/30 backdrop-blur-[2px]"
        onClick={onClose}
      />
      <section
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="absolute inset-x-0 bottom-0 top-14 overflow-hidden rounded-t-[26px] border border-[#d6cabd] bg-[#fbf7f1] shadow-[0_-18px_60px_rgba(24,19,12,0.2)] sm:inset-y-5 sm:right-5 sm:left-auto sm:w-[min(42rem,calc(100vw-2.5rem))] sm:rounded-[26px]"
      >
        {children}
      </section>
    </div>
  );
}

function ReviewBlock({ change }: { change: RecentCardChange }) {
  return (
    <div className="rounded-[18px] border border-[#dec391] bg-[#fff7e6] p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[0.68rem] tracking-[0.18em] text-[#7a673f] uppercase">Recent change</p>
          <h3 className="mt-1 text-sm font-medium text-[#322715]">{change.cardLabel}</h3>
        </div>
        <span className="rounded-full border border-[#d8bf8a] bg-[#fff0ce] px-2.5 py-1 text-[0.68rem] font-medium text-[#70511f]">
          Changed
        </span>
      </div>

      {change.details.length > 0 ? (
        <div className="mt-4 space-y-3">
          {change.details.map((detail) => (
            <div key={detail.label} className="grid gap-2 rounded-[14px] border border-[#ead7ae] bg-[#fffdfa] p-3 sm:grid-cols-2">
              <div>
                <p className="text-[0.68rem] tracking-[0.16em] text-[#7a6b58] uppercase">
                  Previous {detail.label}
                </p>
                <p className="mt-2 text-sm leading-6 text-[#625747]">{detail.previousValue}</p>
              </div>
              <div>
                <p className="text-[0.68rem] tracking-[0.16em] text-[#7a6b58] uppercase">
                  New {detail.label}
                </p>
                <p className="mt-2 text-sm leading-6 text-[#1d1914]">{detail.newValue}</p>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function DraftField({
  label,
  multiline = false,
  onChange,
  value,
}: {
  label: string;
  multiline?: boolean;
  onChange: (value: string) => void;
  value: string;
}) {
  const className =
    "mt-2 w-full rounded-[14px] border border-[#dfd5c8] bg-[#fffdfa] px-3.5 py-3 text-sm leading-6 text-[#1b1916] outline-none transition-colors duration-150 placeholder:text-[#918473] focus:border-[#8a7757] focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#fbf7f1]";

  return (
    <label className="block">
      <span className="text-[0.68rem] tracking-[0.18em] text-[#7c6d58] uppercase">{label}</span>
      {multiline ? (
        <textarea className={className} rows={4} value={value} onChange={(event) => onChange(event.currentTarget.value)} />
      ) : (
        <input className={className} value={value} onChange={(event) => onChange(event.currentTarget.value)} />
      )}
    </label>
  );
}

function DraftSelect({
  label,
  onChange,
  options,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  options: Array<{ label: string; value: string }>;
  value: string;
}) {
  return (
    <label className="block">
      <span className="text-[0.68rem] tracking-[0.18em] text-[#7c6d58] uppercase">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.currentTarget.value)}
        className="mt-2 w-full rounded-[14px] border border-[#dfd5c8] bg-[#fffdfa] px-3.5 py-3 text-sm leading-6 text-[#1b1916] outline-none transition-colors duration-150 focus:border-[#8a7757] focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#fbf7f1]"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function CaseCardEditorDrawer({
  caseFile,
  isPending,
  onClose,
  onCreate,
  onDelete,
  onSave,
  reviewChange,
  target,
}: {
  caseFile: CaseFile;
  isPending: boolean;
  onClose: () => void;
  onCreate: (cardType: Exclude<CardType, "case_metadata">, content: Record<string, unknown>) => void;
  onDelete: (card: SelectedCard) => void;
  onSave: (card: SelectedCard, content: SavePayload) => void;
  reviewChange: RecentCardChange | null;
  target: EditorTarget;
}) {
  const [draftWitness, setDraftWitness] = useState({
    name: "",
    persona: "",
    called_by: "prosecution",
    knowledge_scope: "",
    contradicts: "",
  });
  const [draftEvidence, setDraftEvidence] = useState({
    evidence_id: "",
    submitted_by: "prosecution",
    description: "",
  });
  const [draftFact, setDraftFact] = useState({
    fact_id: "",
    text: "",
  });

  const isExisting = target.kind === "existing";
  const drawerTitle = isExisting ? "Case editor" : `Add ${target.cardType.replace("_", " ")}`;
  const activeReviewChange: RecentCardChange | null =
    reviewChange &&
    target.kind === "existing" &&
    reviewChange.selectedCard &&
    reviewChange.selectedCard.card_type === target.card.card_type &&
    reviewChange.selectedCard.card_id === target.card.card_id
      ? reviewChange
      : null;

  return (
    <DrawerShell onClose={onClose} title={drawerTitle}>
      <div className="flex h-full flex-col">
        <header className="flex items-center justify-between gap-3 border-b border-[#e7ddd1] px-5 py-4 sm:px-6">
          <div>
            <p className="text-[0.68rem] tracking-[0.2em] text-[#6c7484] uppercase">
              {isExisting ? "Case editor" : "New card"}
            </p>
            <h2 className="mt-1 text-lg font-medium tracking-[-0.02em] text-[#191613]">
              {isExisting ? getDrawerHeading(caseFile, target.card) : getNewCardHeading(target.cardType)}
            </h2>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              aria-label="Close editor"
              className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-[#d8ccbb] bg-[#fffdf8] text-[#2b251f] transition-colors duration-150 hover:bg-[#f4ebdd] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#fbf7f1]"
            >
              <CloseIcon />
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-5 sm:px-6">
          {activeReviewChange ? <ReviewBlock change={activeReviewChange} /> : null}

          <div className={`space-y-4 ${activeReviewChange ? "mt-5" : ""}`}>
            {isExisting
              ? renderExistingEditor(caseFile, target.card, onSave)
              : renderNewEditor(
                  target.cardType,
                  draftWitness,
                  setDraftWitness,
                  draftEvidence,
                  setDraftEvidence,
                  draftFact,
                  setDraftFact,
                  onCreate,
                )}
          </div>

        </div>

        <footer className="border-t border-[#e7ddd1] px-5 py-4 sm:px-6">
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs text-[#6f6558]">
              {isPending ? "Saving changes..." : "Changes save directly to this draft."}
            </p>
            <div className="flex items-center gap-2">
              {isExisting && target.card.card_type !== "case_metadata" ? (
                <TextButton
                  className="border-[#d6a996] bg-[#fff7f3] text-[#8c472b] hover:bg-[#ffece3] focus-visible:ring-offset-[#fbf7f1]"
                  onClick={() => onDelete(target.card)}
                >
                  <TrashIcon />
                  Delete
                </TextButton>
              ) : null}
              <TextButton
                className="border-[#d8ccbb] bg-[#fffdfa] text-[#2d2620] hover:bg-[#f4ebdd] focus-visible:ring-offset-[#fbf7f1]"
                onClick={onClose}
              >
                Close
              </TextButton>
            </div>
          </div>
        </footer>
      </div>
    </DrawerShell>
  );
}

function renderExistingEditor(
  caseFile: CaseFile,
  card: SelectedCard,
  onSave: (card: SelectedCard, content: SavePayload) => void,
) {
  if (card.card_type === "case_metadata") {
    return (
      <>
        <EditableField label="Case title" value={caseFile.case_title} onSave={(value) => onSave(card, { case_title: value })} />
        <EditableField
          label="Charge or claim"
          multiline
          value={caseFile.charge_or_claim}
          onSave={(value) => onSave(card, { charge_or_claim: value })}
        />
        <EditableField
          label="Plaintiff or prosecution"
          value={caseFile.parties.plaintiff_or_prosecution}
          onSave={(value) => onSave(card, { parties: { ...caseFile.parties, plaintiff_or_prosecution: value } })}
        />
        <EditableField
          label="Defendant"
          value={caseFile.parties.defendant}
          onSave={(value) => onSave(card, { parties: { ...caseFile.parties, defendant: value } })}
        />
        <EditableField
          label="State"
          value={caseFile.jurisdiction.state}
          onSave={(value) => onSave(card, { jurisdiction: { ...caseFile.jurisdiction, state: value } })}
        />
        <EditableField
          label="Court"
          value={caseFile.jurisdiction.court}
          onSave={(value) => onSave(card, { jurisdiction: { ...caseFile.jurisdiction, court: value } })}
        />
      </>
    );
  }

  if (card.card_type === "witness") {
    const witness = caseFile.witnesses.find((item) => item.witness_id === card.card_id);
    if (!witness) {
      return null;
    }

    return (
      <>
        <EditableField label="Witness ID" value={witness.witness_id} onSave={(value) => onSave(card, { witness_id: value })} />
        <EditableField label="Name" value={witness.name} onSave={(value) => onSave(card, { name: value })} />
        <EditableField label="Role" value={witness.persona} onSave={(value) => onSave(card, { persona: value })} />
        <SelectField
          label="Side"
          options={[
            { label: "Prosecution", value: "prosecution" },
            { label: "Defense", value: "defense" },
          ]}
          value={witness.called_by}
          onSave={(value) => onSave(card, { called_by: value as WitnessProfile["called_by"] })}
        />
        <EditableField
          label="Knowledge summary"
          multiline
          value={witness.knowledge_scope}
          onSave={(value) => onSave(card, { knowledge_scope: value })}
        />
        <EditableField
          label="Contradicts"
          value={witness.contradicts ?? ""}
          onSave={(value) => onSave(card, { contradicts: value || null })}
        />
      </>
    );
  }

  if (card.card_type === "evidence") {
    const evidence = caseFile.evidence.find((item) => item.evidence_id === card.card_id);
    if (!evidence) {
      return null;
    }

    return (
      <>
        <EditableField label="Evidence ID" value={evidence.evidence_id} onSave={(value) => onSave(card, { evidence_id: value })} />
        <SelectField
          label="Submitted by"
          options={[
            { label: "Prosecution", value: "prosecution" },
            { label: "Defense", value: "defense" },
          ]}
          value={evidence.submitted_by}
          onSave={(value) => onSave(card, { submitted_by: value as Evidence["submitted_by"] })}
        />
        <EditableField
          label="Description"
          multiline
          value={evidence.description}
          onSave={(value) => onSave(card, { description: value })}
        />
      </>
    );
  }

  const fact = caseFile.disputed_facts.find((item) => item.fact_id === card.card_id);
  if (!fact) {
    return null;
  }

  return (
    <>
      <EditableField label="Disputed Fact ID" value={fact.fact_id} onSave={(value) => onSave(card, { fact_id: value })} />
      <EditableField
        label="Factual issue"
        multiline
        value={fact.text}
        onSave={(value) => onSave(card, { text: value })}
      />
    </>
  );
}

function renderNewEditor(
  cardType: Exclude<CardType, "case_metadata">,
  draftWitness: {
    name: string;
    persona: string;
    called_by: string;
    knowledge_scope: string;
    contradicts: string;
  },
  setDraftWitness: Dispatch<SetStateAction<{
    name: string;
    persona: string;
    called_by: string;
    knowledge_scope: string;
    contradicts: string;
  }>>,
  draftEvidence: {
    evidence_id: string;
    submitted_by: string;
    description: string;
  },
  setDraftEvidence: Dispatch<SetStateAction<{
    evidence_id: string;
    submitted_by: string;
    description: string;
  }>>,
  draftFact: {
    fact_id: string;
    text: string;
  },
  setDraftFact: Dispatch<SetStateAction<{
    fact_id: string;
    text: string;
  }>>,
  onCreate: (cardType: Exclude<CardType, "case_metadata">, content: Record<string, unknown>) => void,
) {
  if (cardType === "witness") {
    return (
      <>
        <DraftField label="Name" value={draftWitness.name} onChange={(value) => setDraftWitness((current) => ({ ...current, name: value }))} />
        <DraftField label="Role" value={draftWitness.persona} onChange={(value) => setDraftWitness((current) => ({ ...current, persona: value }))} />
        <DraftSelect
          label="Side"
          value={draftWitness.called_by}
          options={[
            { label: "Prosecution", value: "prosecution" },
            { label: "Defense", value: "defense" },
          ]}
          onChange={(value) => setDraftWitness((current) => ({ ...current, called_by: value }))}
        />
        <DraftField
          label="Knowledge summary"
          multiline
          value={draftWitness.knowledge_scope}
          onChange={(value) => setDraftWitness((current) => ({ ...current, knowledge_scope: value }))}
        />
        <DraftField
          label="Contradicts"
          value={draftWitness.contradicts}
          onChange={(value) => setDraftWitness((current) => ({ ...current, contradicts: value }))}
        />
        <TextButton
          className="border-[#26231f] bg-[#26231f] text-[#f7f1e6] hover:bg-[#38312a] focus-visible:ring-offset-[#fbf7f1]"
          disabled={!draftWitness.name.trim() || !draftWitness.knowledge_scope.trim()}
          onClick={() =>
            onCreate("witness", {
              name: draftWitness.name,
              persona: draftWitness.persona,
              called_by: draftWitness.called_by,
              knowledge_scope: draftWitness.knowledge_scope,
              contradicts: draftWitness.contradicts || null,
            })
          }
        >
          Add witness
        </TextButton>
      </>
    );
  }

  if (cardType === "evidence") {
    return (
      <>
        <DraftField label="Evidence ID" value={draftEvidence.evidence_id} onChange={(value) => setDraftEvidence((current) => ({ ...current, evidence_id: value }))} />
        <DraftSelect
          label="Submitted by"
          value={draftEvidence.submitted_by}
          options={[
            { label: "Prosecution", value: "prosecution" },
            { label: "Defense", value: "defense" },
          ]}
          onChange={(value) => setDraftEvidence((current) => ({ ...current, submitted_by: value }))}
        />
        <DraftField
          label="Description"
          multiline
          value={draftEvidence.description}
          onChange={(value) => setDraftEvidence((current) => ({ ...current, description: value }))}
        />
        <TextButton
          className="border-[#26231f] bg-[#26231f] text-[#f7f1e6] hover:bg-[#38312a] focus-visible:ring-offset-[#fbf7f1]"
          disabled={!draftEvidence.evidence_id.trim() || !draftEvidence.description.trim()}
          onClick={() => onCreate("evidence", draftEvidence)}
        >
          Add evidence
        </TextButton>
      </>
    );
  }

  return (
    <>
      <DraftField label="Disputed Fact ID" value={draftFact.fact_id} onChange={(value) => setDraftFact((current) => ({ ...current, fact_id: value }))} />
      <DraftField
        label="Factual issue"
        multiline
        value={draftFact.text}
        onChange={(value) => setDraftFact((current) => ({ ...current, text: value }))}
      />
      <TextButton
        className="border-[#26231f] bg-[#26231f] text-[#f7f1e6] hover:bg-[#38312a] focus-visible:ring-offset-[#fbf7f1]"
        disabled={!draftFact.fact_id.trim() || !draftFact.text.trim()}
        onClick={() => onCreate("disputed_fact", draftFact)}
      >
        Add disputed fact
      </TextButton>
    </>
  );
}

function getNewCardHeading(cardType: Exclude<CardType, "case_metadata">) {
  if (cardType === "witness") {
    return "New witness";
  }

  if (cardType === "evidence") {
    return "New evidence";
  }

  return "New disputed fact";
}

function getDrawerHeading(caseFile: CaseFile, card: SelectedCard) {
  if (card.card_type === "case_metadata") {
    return caseFile.case_title.trim() || "Case overview";
  }

  if (card.card_type === "witness") {
    const witness = caseFile.witnesses.find((item) => item.witness_id === card.card_id);
    return witness?.witness_id || "Witness";
  }

  if (card.card_type === "evidence") {
    const evidence = caseFile.evidence.find((item) => item.evidence_id === card.card_id);
    return evidence?.evidence_id || "Evidence";
  }

  const fact = caseFile.disputed_facts.find((item) => item.fact_id === card.card_id);
  return fact?.fact_id || "Disputed fact";
}

export function SectionToggle({
  actions,
  collapsed,
  countLabel,
  description,
  onToggle,
  title,
}: {
  actions?: ReactNode;
  collapsed: boolean;
  countLabel: string;
  description: string;
  onToggle: () => void;
  title: string;
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <button
        type="button"
        onClick={onToggle}
        className="min-w-0 flex-1 rounded-[18px] px-1 py-1 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f6f0e7]"
      >
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-[1.02rem] font-medium tracking-[-0.02em] text-[#181511]">{title}</h2>
            <span className="rounded-full border border-[#e0d6ca] bg-[#fffdfa] px-2.5 py-1 text-[0.68rem] text-[#706456]">
              {countLabel}
            </span>
          </div>
          <p className="mt-1 text-sm leading-6 text-[#5b5248]">{description}</p>
        </div>
      </button>
      <div className="mt-1 inline-flex items-center gap-2 self-start">
        {actions}
        <button
          type="button"
          onClick={onToggle}
          aria-label={collapsed ? `Expand ${title}` : `Collapse ${title}`}
          className={`inline-flex h-9 w-9 items-center justify-center rounded-full border border-[#ddd2c4] bg-[#fffdfa] text-[#2e2821] transition-transform duration-150 ${collapsed ? "" : "rotate-180"}`}
        >
          <ChevronDownIcon />
        </button>
      </div>
    </div>
  );
}
