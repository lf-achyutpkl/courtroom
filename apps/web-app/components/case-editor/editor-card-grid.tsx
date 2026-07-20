"use client";

import { useMemo, useState } from "react";

import type {
  CaseFile,
  CaseEditResult,
  DisputedFact,
  Evidence,
  ManualMutationRequest,
  SelectedCard,
  WitnessProfile,
} from "@/lib/case-files";
import { applyCaseEditResult } from "@/lib/case-files";

import {
  CaseCardEditorDrawer,
  DisputedFactSummaryCard,
  EmptySectionCard,
  EvidenceSummaryCard,
  OverviewSummaryCard,
  SectionToggle,
  WitnessSummaryCard,
} from "@/components/case-editor/editor-cards";
import {
  PlusIcon,
  TextButton,
} from "@/components/case-editor/editor-primitives";
import type {
  EditorTarget,
  RecentCardChange,
} from "@/components/case-editor/editor-workspace-utils";
import {
  getCaseReadiness,
  isCaseMostlyEmpty,
} from "@/components/case-editor/editor-workspace-utils";

function nextCardId(existingIds: string[], prefix: string) {
  let nextIndex = 1;

  for (const value of existingIds) {
    if (!value.startsWith(prefix)) {
      continue;
    }

    const parsed = Number(value.slice(prefix.length));
    if (Number.isFinite(parsed)) {
      nextIndex = Math.max(nextIndex, parsed + 1);
    }
  }

  return `${prefix}${nextIndex}`;
}

function SectionShell({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <section className="border border-[#ddd2c4] bg-[linear-gradient(180deg,#fbf7f1_0%,#f4ede3_100%)] p-4 shadow-[0_18px_40px_rgba(54,42,23,0.07)] sm:p-5">
      {children}
    </section>
  );
}

export function EditorCardGrid({
  applyManualMutation,
  caseFile,
  editorTarget,
  onCloseEditor,
  onDeleteCard,
  onOpenEditor,
  onSelectTarget,
  selectedTarget,
  pendingMutationKey,
  recentAiChange,
  recordRevision,
  reviewChange,
}: {
  applyManualMutation: (
    request: ManualMutationRequest,
    optimisticUpdate: (caseFile: CaseFile) => CaseFile,
  ) => Promise<void>;
  caseFile: CaseFile;
  editorTarget: EditorTarget | null;
  onCloseEditor: () => void;
  onDeleteCard: (card: SelectedCard) => void;
  onOpenEditor: (target: EditorTarget) => void;
  onSelectTarget: (target: EditorTarget) => void;
  selectedTarget: EditorTarget | null;
  pendingMutationKey: string | null;
  recentAiChange: RecentCardChange | null;
  recordRevision: number;
  reviewChange: RecentCardChange | null;
}) {
  const [collapsedSections, setCollapsedSections] = useState({
    overview: false,
    witnesses: false,
    evidence: false,
    disputedFacts: false,
  });

  const readiness = useMemo(() => getCaseReadiness(caseFile), [caseFile]);
  const selectedCard =
    selectedTarget?.kind === "existing" ? selectedTarget.card : null;
  const isChangedCard = (card: SelectedCard) =>
    recentAiChange?.selectedCard?.card_type === card.card_type &&
    recentAiChange.selectedCard.card_id === card.card_id;

  function toggleSection(section: keyof typeof collapsedSections) {
    setCollapsedSections((current) => ({
      ...current,
      [section]: !current[section],
    }));
  }

  function saveCard(card: SelectedCard, content: Record<string, unknown>) {
    void applyManualMutation(
      {
        action: "edit_card",
        card_type: card.card_type,
        card_id: card.card_id,
        content,
        expected_revision: recordRevision,
      },
      (current) => {
        if (card.card_type === "case_metadata") {
          return {
            ...current,
            ...content,
            parties: {
              ...current.parties,
              ...((content.parties as CaseFile["parties"] | undefined) ?? {}),
            },
            jurisdiction: {
              ...current.jurisdiction,
              ...((content.jurisdiction as CaseFile["jurisdiction"] | undefined) ?? {}),
            },
          };
        }

        return applyCaseEditResult(current, {
          action: "edit_card",
          card_type: card.card_type,
          card_id: card.card_id,
          updated_content: resolveUpdatedContent(current, card, content),
        });
      },
    );
  }

  function createCard(
    cardType: "witness" | "evidence" | "disputed_fact",
    content: Record<string, unknown>,
  ) {
    const cardId =
      cardType === "witness"
        ? (content.witness_id as string | undefined) ??
          nextCardId(
            caseFile.witnesses.map((witness) => witness.witness_id),
            "W",
          )
        : cardType === "evidence"
          ? (content.evidence_id as string | undefined) ??
            nextCardId(
              caseFile.evidence.map((evidence) => evidence.evidence_id),
              "E",
            )
          : (content.fact_id as string | undefined) ??
            nextCardId(
              caseFile.disputed_facts.map((fact) => fact.fact_id),
              "F",
            );

    const normalizedContent =
      cardType === "witness"
        ? {
            witness_id: cardId,
            contradicts: null,
            ...content,
          }
        : cardType === "evidence"
          ? {
              evidence_id: cardId,
              ...content,
            }
          : {
              fact_id: cardId,
              ...content,
            };

    onOpenEditor({
      kind: "existing",
      card: {
        card_type: cardType,
        card_id: cardId,
      },
    });

    void applyManualMutation(
      {
        action: "add_card",
        card_type: cardType,
        card_id: null,
        content: normalizedContent,
        expected_revision: recordRevision,
      },
      (current) => applyCaseEditResult(current, {
        action: "add_card",
        card_type: cardType,
        card_id: null,
        updated_content: normalizedContent as never,
      }),
    );
  }

  function deleteCard(card: SelectedCard) {
    if (card.card_type === "case_metadata") {
      return;
    }

    void applyManualMutation(
      {
        action: "delete_card",
        card_type: card.card_type,
        card_id: card.card_id,
        content: null,
        expected_revision: recordRevision,
      },
      (current) => applyCaseEditResult(current, {
        action: "delete_card",
        card_type: card.card_type,
        card_id: card.card_id,
        updated_content: null,
      }),
    );
    onDeleteCard(card);
    onCloseEditor();
  }

  return (
    <aside className="relative flex h-full min-h-0 flex-col overflow-hidden rounded-[28px] border border-[#d6c9b7] bg-[linear-gradient(180deg,#efe6d7_0%,#f7f1e7_7%,#f3ece1_100%)] shadow-[0_26px_60px_rgba(54,42,23,0.11)]">
      <header className="border-b border-[#deceb7] bg-[linear-gradient(180deg,rgba(251,246,238,0.96)_0%,rgba(242,233,220,0.96)_100%)] px-4 py-4 sm:px-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-[0.8rem] font-medium tracking-[0.08em] text-[#5d4b31] uppercase">
            Case editor
          </p>
          <span className="rounded-full border border-[#dccfbf] bg-[#fff9f1] px-3 py-1.5 text-xs font-medium text-[#5a4a38]">
            {caseFile.witnesses.length + caseFile.evidence.length + caseFile.disputed_facts.length + 1} cards
          </span>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {readiness.warnings.length > 0 ? (
            readiness.warnings.map((warning) => (
              <span
                key={warning}
                className="rounded-full border border-[#e1cbb9] bg-[#fff5ed] px-3 py-1.5 text-xs text-[#7c4e2d]"
              >
                {warning}
              </span>
            ))
          ) : (
            <span className="rounded-full border border-[#d8ddcf] bg-[#f7faf5] px-3 py-1.5 text-xs text-[#415240]">
              All required sections are present.
            </span>
          )}
        </div>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto px-3 py-3 sm:px-0 sm:py-4">

      {isCaseMostlyEmpty(caseFile) ? (
        <SectionShell>
          <h2 className="text-[1.05rem] font-medium tracking-[-0.02em] text-[#1a1612]">
            Start with the dispute
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-[#5c5348]">
            Describe the matter in chat first. Witnesses, evidence, and disputed facts will appear only after meaningful details exist.
          </p>
        </SectionShell>
      ) : null}

        <SectionShell>
          <SectionToggle
            collapsed={collapsedSections.overview}
            countLabel="1 card"
            description="Core framing: title, claim, parties, and jurisdiction."
            onToggle={() => toggleSection("overview")}
            title="Overview"
          />
          {!collapsedSections.overview ? (
            <div className="mt-4">
              <OverviewSummaryCard
                caseFile={caseFile}
                changed={Boolean(
                  recentAiChange?.selectedCard?.card_type === "case_metadata",
                )}
                isSelected={selectedCard?.card_type === "case_metadata"}
                onSelect={() =>
                  onSelectTarget({
                    kind: "existing",
                    card: { card_type: "case_metadata", card_id: null },
                  })
                }
                onView={() =>
                  onOpenEditor({
                    kind: "existing",
                    card: { card_type: "case_metadata", card_id: null },
                  })
                }
              />
            </div>
          ) : null}
        </SectionShell>

        <SectionShell>
          <SectionToggle
            actions={
              <TextButton
                className="border-[#d8ccbb] bg-[#fffdfa] text-[#2d2620] hover:bg-[#f4ebdd] focus-visible:ring-offset-[#f8f3eb]"
                onClick={() => onOpenEditor({ kind: "new", cardType: "witness" })}
              >
                <PlusIcon />
                Add
              </TextButton>
            }
            collapsed={collapsedSections.witnesses}
            countLabel={`${caseFile.witnesses.length}`}
            description="People who move the narrative and carry the factual record."
            onToggle={() => toggleSection("witnesses")}
            title="Witnesses"
          />
          {!collapsedSections.witnesses ? (
            <div className="mt-4 grid gap-3">
              {caseFile.witnesses.length === 0 ? (
                <EmptySectionCard
                  actionLabel="Add first witness"
                  message="No witnesses yet. Add someone who knows a key part of the dispute."
                  onAction={() => onOpenEditor({ kind: "new", cardType: "witness" })}
                />
              ) : null}
              {caseFile.witnesses.map((witness) => (
                <WitnessSummaryCard
                  key={witness.witness_id}
                  changed={isChangedCard({
                    card_type: "witness",
                    card_id: witness.witness_id,
                  })}
                  isSelected={
                    selectedCard?.card_type === "witness" &&
                    selectedCard.card_id === witness.witness_id
                  }
                  onSelect={() =>
                    onSelectTarget({
                      kind: "existing",
                      card: { card_type: "witness", card_id: witness.witness_id },
                    })
                  }
                  onView={() =>
                    onOpenEditor({
                      kind: "existing",
                      card: { card_type: "witness", card_id: witness.witness_id },
                    })
                  }
                  witness={witness}
                />
              ))}
            </div>
          ) : null}
        </SectionShell>

        <SectionShell>
          <SectionToggle
            actions={
              <TextButton
                className="border-[#d8ccbb] bg-[#fffdfa] text-[#2d2620] hover:bg-[#f4ebdd] focus-visible:ring-offset-[#f8f3eb]"
                onClick={() => onOpenEditor({ kind: "new", cardType: "evidence" })}
              >
                <PlusIcon />
                Add
              </TextButton>
            }
            collapsed={collapsedSections.evidence}
            countLabel={`${caseFile.evidence.length}`}
            description="Documents, objects, and exhibits that support or weaken the case."
            onToggle={() => toggleSection("evidence")}
            title="Evidence"
          />
          {!collapsedSections.evidence ? (
            <div className="mt-4 grid gap-3">
              {caseFile.evidence.length === 0 ? (
                <EmptySectionCard
                  actionLabel="Add first evidence item"
                  message="No evidence yet. Add a concrete exhibit, record, or physical item."
                  onAction={() => onOpenEditor({ kind: "new", cardType: "evidence" })}
                />
              ) : null}
              {caseFile.evidence.map((evidence) => (
                <EvidenceSummaryCard
                  key={evidence.evidence_id}
                  changed={isChangedCard({
                    card_type: "evidence",
                    card_id: evidence.evidence_id,
                  })}
                  evidence={evidence}
                  isSelected={
                    selectedCard?.card_type === "evidence" &&
                    selectedCard.card_id === evidence.evidence_id
                  }
                  onSelect={() =>
                    onSelectTarget({
                      kind: "existing",
                      card: { card_type: "evidence", card_id: evidence.evidence_id },
                    })
                  }
                  onView={() =>
                    onOpenEditor({
                      kind: "existing",
                      card: { card_type: "evidence", card_id: evidence.evidence_id },
                    })
                  }
                />
              ))}
            </div>
          ) : null}
        </SectionShell>

        <SectionShell>
          <SectionToggle
            actions={
              <TextButton
                className="border-[#d8ccbb] bg-[#fffdfa] text-[#2d2620] hover:bg-[#f4ebdd] focus-visible:ring-offset-[#f8f3eb]"
                onClick={() => onOpenEditor({ kind: "new", cardType: "disputed_fact" })}
              >
                <PlusIcon />
                Add
              </TextButton>
            }
            collapsed={collapsedSections.disputedFacts}
            countLabel={`${caseFile.disputed_facts.length}`}
            description="The factual issues the parties disagree about."
            onToggle={() => toggleSection("disputedFacts")}
            title="Disputed facts"
          />
          {!collapsedSections.disputedFacts ? (
            <div className="mt-4 grid gap-3">
              {caseFile.disputed_facts.length === 0 ? (
                <EmptySectionCard
                  actionLabel="Add first disputed fact"
                  message="No disputed facts yet. Add the factual question the parties contest."
                  onAction={() => onOpenEditor({ kind: "new", cardType: "disputed_fact" })}
                />
              ) : null}
              {caseFile.disputed_facts.map((fact) => (
                <DisputedFactSummaryCard
                  key={fact.fact_id}
                  changed={isChangedCard({
                    card_type: "disputed_fact",
                    card_id: fact.fact_id,
                  })}
                  fact={fact}
                  isSelected={
                    selectedCard?.card_type === "disputed_fact" &&
                    selectedCard.card_id === fact.fact_id
                  }
                  onSelect={() =>
                    onSelectTarget({
                      kind: "existing",
                      card: { card_type: "disputed_fact", card_id: fact.fact_id },
                    })
                  }
                  onView={() =>
                    onOpenEditor({
                      kind: "existing",
                      card: { card_type: "disputed_fact", card_id: fact.fact_id },
                    })
                  }
                />
              ))}
            </div>
          ) : null}
        </SectionShell>
      </div>

      {editorTarget ? (
        <CaseCardEditorDrawer
          key={
            editorTarget.kind === "existing"
              ? `${editorTarget.card.card_type}:${editorTarget.card.card_id ?? "overview"}`
              : `new:${editorTarget.cardType}`
          }
          caseFile={caseFile}
          isPending={
            editorTarget.kind === "new"
              ? pendingMutationKey === `add_card:${editorTarget.cardType}:none`
              : pendingMutationKey ===
                `edit_card:${editorTarget.card.card_type}:${editorTarget.card.card_id ?? "none"}`
          }
          onClose={onCloseEditor}
          onCreate={createCard}
          onDelete={deleteCard}
          onSave={(card, content) => saveCard(card, content as Record<string, unknown>)}
          reviewChange={reviewChange}
          target={editorTarget}
        />
      ) : null}
    </aside>
  );
}

function resolveUpdatedContent(
  caseFile: CaseFile,
  card: SelectedCard,
  content: Record<string, unknown>,
): CaseEditResult["updated_content"] {
  if (card.card_type === "witness") {
    const witness = caseFile.witnesses.find((item) => item.witness_id === card.card_id);
    if (!witness) {
      return null;
    }
    return {
      ...witness,
      ...(content as Partial<WitnessProfile>),
    };
  }

  if (card.card_type === "evidence") {
    const evidence = caseFile.evidence.find((item) => item.evidence_id === card.card_id);
    if (!evidence) {
      return null;
    }
    return {
      ...evidence,
      ...(content as Partial<Evidence>),
    };
  }

  if (card.card_type === "disputed_fact") {
    const fact = caseFile.disputed_facts.find((item) => item.fact_id === card.card_id);
    if (!fact) {
      return null;
    }
    return {
      ...fact,
      ...(content as Partial<DisputedFact>),
    };
  }

  return caseFile;
}
