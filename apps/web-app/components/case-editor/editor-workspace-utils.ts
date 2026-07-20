"use client";

import type {
  CardType,
  CaseEditResult,
  CaseFile,
  DisputedFact,
  Evidence,
  ManualMutationRequest,
  SelectedCard,
  WitnessProfile,
} from "@/lib/case-files";

export type EditorTarget =
  | {
      kind: "existing";
      card: SelectedCard;
    }
  | {
      kind: "new";
      cardType: Exclude<CardType, "case_metadata">;
    };

export type CompletionSummary = {
  completeCount: number;
  missingCount: number;
  status: "complete" | "needs_details";
};

export type ReadinessSummary = {
  percentComplete: number;
  completeItems: number;
  totalItems: number;
  missingRequiredDetails: number;
  warnings: string[];
};

export type ChangeDetail = {
  label: string;
  previousValue: string;
  newValue: string;
};

export type RecentCardChange = {
  id: string;
  action: CaseEditResult["action"];
  cardType: CardType | null;
  cardId: string | null;
  cardLabel: string;
  summary: {
    added: string[];
    changed: string[];
    removed: string[];
  };
  details: ChangeDetail[];
  selectedCard: SelectedCard | null;
  undoRequest:
    | Omit<ManualMutationRequest, "expected_revision">
    | null;
  timestamp: string;
};

type FieldState = {
  label: string;
  value: string | null | undefined;
};

export function formatDisplayValue(value: string | null | undefined) {
  const trimmed = value?.trim();
  if (!trimmed) {
    return "Not provided";
  }

  return trimmed;
}

export function formatKnowledgeValue(value: string | null | undefined) {
  const trimmed = value?.trim();
  if (!trimmed) {
    return "Needs details";
  }

  return trimmed;
}

export function formatUnconfirmedValue(value: string | null | undefined) {
  const trimmed = value?.trim();
  if (!trimmed) {
    return "Unconfirmed";
  }

  return trimmed;
}

function isFilled(value: string | null | undefined) {
  return Boolean(value?.trim());
}

function getCompletionSummary(fields: FieldState[]): CompletionSummary {
  const completeCount = fields.filter((field) => isFilled(field.value)).length;
  const missingCount = fields.length - completeCount;

  return {
    completeCount,
    missingCount,
    status: missingCount === 0 ? "complete" : "needs_details",
  };
}

export function getOverviewCompletion(caseFile: CaseFile) {
  return getCompletionSummary(getOverviewFields(caseFile));
}

export function getWitnessCompletion(witness: WitnessProfile) {
  return getCompletionSummary(getWitnessFields(witness));
}

export function getEvidenceCompletion(evidence: Evidence) {
  return getCompletionSummary(getEvidenceFields(evidence));
}

export function getDisputedFactCompletion(fact: DisputedFact) {
  return getCompletionSummary(getDisputedFactFields(fact));
}

export function getCaseReadiness(caseFile: CaseFile): ReadinessSummary {
  const warnings: string[] = [];
  const overviewSummary = getOverviewCompletion(caseFile);
  const witnessSummaries = caseFile.witnesses.map(getWitnessCompletion);
  const evidenceSummaries = caseFile.evidence.map(getEvidenceCompletion);
  const disputedFactSummaries = caseFile.disputed_facts.map(getDisputedFactCompletion);

  if (!caseFile.witnesses.length) {
    warnings.push("Add at least one witness.");
  }

  if (!caseFile.evidence.length) {
    warnings.push("Add at least one evidence item.");
  }

  if (!caseFile.disputed_facts.length) {
    warnings.push("Define at least one disputed fact.");
  }

  const totalItems =
    1 +
    Math.max(caseFile.witnesses.length, 1) +
    Math.max(caseFile.evidence.length, 1) +
    Math.max(caseFile.disputed_facts.length, 1);
  const completeItems =
    (overviewSummary.status === "complete" ? 1 : 0) +
    witnessSummaries.filter((summary) => summary.status === "complete").length +
    evidenceSummaries.filter((summary) => summary.status === "complete").length +
    disputedFactSummaries.filter((summary) => summary.status === "complete").length;
  const missingRequiredDetails =
    overviewSummary.missingCount +
    witnessSummaries.reduce((count, summary) => count + summary.missingCount, 0) +
    evidenceSummaries.reduce((count, summary) => count + summary.missingCount, 0) +
    disputedFactSummaries.reduce((count, summary) => count + summary.missingCount, 0) +
    warnings.length;

  return {
    percentComplete:
      totalItems === 0 ? 0 : Math.round((completeItems / totalItems) * 100),
    completeItems,
    totalItems,
    missingRequiredDetails,
    warnings,
  };
}

export function getCardDisplayTitle(
  caseFile: CaseFile,
  selectedCard: SelectedCard | null,
) {
  if (!selectedCard) {
    return null;
  }

  if (selectedCard.card_type === "case_metadata") {
    return caseFile.case_title.trim() || "Case overview";
  }

  if (selectedCard.card_type === "witness") {
    return (
      caseFile.witnesses.find((witness) => witness.witness_id === selectedCard.card_id)
        ?.name || selectedCard.card_id
    );
  }

  if (selectedCard.card_type === "evidence") {
    const evidence = caseFile.evidence.find(
      (item) => item.evidence_id === selectedCard.card_id,
    );
    return evidence?.description.trim() || selectedCard.card_id;
  }

  const fact = caseFile.disputed_facts.find(
    (item) => item.fact_id === selectedCard.card_id,
  );
  return fact?.text.trim() || selectedCard.card_id;
}

export function getChatFocusLabel(
  caseFile: CaseFile,
  target: EditorTarget | null,
) {
  if (!target) {
    return null;
  }

  if (target.kind === "new") {
    if (target.cardType === "witness") {
      return "Adding witness";
    }

    if (target.cardType === "evidence") {
      return "Adding evidence";
    }

    return "Adding disputed fact";
  }

  if (target.card.card_type === "case_metadata") {
    return "Editing case overview";
  }

  const title = getCardDisplayTitle(caseFile, target.card) ?? "Selected card";

  if (target.card.card_type === "witness") {
    return `Editing witness: ${title}`;
  }

  if (target.card.card_type === "evidence") {
    return `Editing evidence: ${target.card.card_id}`;
  }

  return `Editing disputed fact: ${target.card.card_id}`;
}

export function isCaseMostlyEmpty(caseFile: CaseFile) {
  return (
    !isFilled(caseFile.case_title) &&
    !isFilled(caseFile.charge_or_claim) &&
    !isFilled(caseFile.parties.plaintiff_or_prosecution) &&
    !isFilled(caseFile.parties.defendant) &&
    !caseFile.witnesses.length &&
    !caseFile.evidence.length &&
    !caseFile.disputed_facts.length
  );
}

export function buildRecentChange(
  previousCaseFile: CaseFile,
  result: CaseEditResult,
): RecentCardChange | null {
  if (result.action === "full_regenerate") {
    const nextCaseFile = result.updated_content as CaseFile;
    return {
      id: `change-${Date.now()}`,
      action: result.action,
      cardType: null,
      cardId: null,
      cardLabel: nextCaseFile.case_title.trim() || "Case file",
      summary: {
        added: [
          `${nextCaseFile.witnesses.length} witness${
            nextCaseFile.witnesses.length === 1 ? "" : "es"
          }`,
          `${nextCaseFile.evidence.length} evidence item${
            nextCaseFile.evidence.length === 1 ? "" : "s"
          }`,
          `${nextCaseFile.disputed_facts.length} disputed fact${
            nextCaseFile.disputed_facts.length === 1 ? "" : "s"
          }`,
        ],
        changed: compactList([
          compareScalarChange(
            "Case title",
            previousCaseFile.case_title,
            nextCaseFile.case_title,
          ),
          compareScalarChange(
            "Claim",
            previousCaseFile.charge_or_claim,
            nextCaseFile.charge_or_claim,
          ),
        ]),
        removed: [],
      },
      details: compactList([
        buildChangeDetail(
          "Case title",
          previousCaseFile.case_title,
          nextCaseFile.case_title,
        ),
        buildChangeDetail(
          "Charge or claim",
          previousCaseFile.charge_or_claim,
          nextCaseFile.charge_or_claim,
        ),
      ]),
      selectedCard: { card_type: "case_metadata", card_id: null },
      undoRequest: null,
      timestamp: new Date().toISOString(),
    };
  }

  if (!result.card_type) {
    return null;
  }

  const previousContent = getCardContent(previousCaseFile, result.card_type, result.card_id);
  const nextContent =
    result.action === "delete_card" ? null : result.updated_content;
  const selectedCard: SelectedCard | null =
    result.card_type === "case_metadata"
      ? { card_type: "case_metadata", card_id: null }
      : result.card_id
        ? {
            card_type: result.card_type,
            card_id: result.card_id,
          }
        : null;

  return {
    id: `change-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    action: result.action,
    cardType: result.card_type,
    cardId: result.card_id,
    cardLabel: resolveCardLabel(result.card_type, previousContent, nextContent, result.card_id),
    summary: buildChangeSummary(result.card_type, previousContent, nextContent),
    details: buildChangeDetails(result.card_type, previousContent, nextContent),
    selectedCard,
    undoRequest: buildUndoRequest(result.card_type, result.card_id, previousContent, nextContent, result.action),
    timestamp: new Date().toISOString(),
  };
}

function compactList<T>(items: Array<T | null>) {
  return items.filter((item): item is T => item !== null);
}

function compareScalarChange(label: string, previousValue: string, nextValue: string) {
  if (previousValue.trim() === nextValue.trim()) {
    return null;
  }

  return label;
}

function buildChangeDetail(
  label: string,
  previousValue: string,
  nextValue: string,
): ChangeDetail | null {
  if (previousValue.trim() === nextValue.trim()) {
    return null;
  }

  return {
    label,
    previousValue: formatDisplayValue(previousValue),
    newValue: formatDisplayValue(nextValue),
  };
}

function resolveCardLabel(
  cardType: CardType,
  previousContent: unknown,
  nextContent: unknown,
  cardId: string | null,
) {
  if (cardType === "case_metadata") {
    const content = (nextContent ?? previousContent) as CaseFile | null;
    return content?.case_title?.trim() || "Case overview";
  }

  if (cardType === "witness") {
    const witness = (nextContent ?? previousContent) as WitnessProfile | null;
    return witness?.name?.trim() || cardId || "Witness";
  }

  if (cardType === "evidence") {
    return cardId || "Evidence";
  }

  return cardId || "Disputed fact";
}

function buildChangeSummary(
  cardType: CardType,
  previousContent: unknown,
  nextContent: unknown,
) {
  const previousFields = getFieldsForCard(cardType, previousContent);
  const nextFields = getFieldsForCard(cardType, nextContent);
  const added: string[] = [];
  const changed: string[] = [];
  const removed: string[] = [];

  for (const nextField of nextFields) {
    const previousField = previousFields.find((field) => field.label === nextField.label);
    const previousValue = previousField?.value?.trim() ?? "";
    const nextValue = nextField.value?.trim() ?? "";

    if (!previousValue && nextValue) {
      added.push(nextField.label);
      continue;
    }

    if (previousValue && !nextValue) {
      removed.push(nextField.label);
      continue;
    }

    if (previousValue !== nextValue) {
      changed.push(nextField.label);
    }
  }

  if (!nextFields.length && previousFields.length) {
    removed.push(...previousFields.map((field) => field.label));
  }

  return { added, changed, removed };
}

function buildChangeDetails(
  cardType: CardType,
  previousContent: unknown,
  nextContent: unknown,
) {
  const labels = new Set<string>();
  const details: ChangeDetail[] = [];

  for (const field of getFieldsForCard(cardType, previousContent)) {
    labels.add(field.label);
  }

  for (const field of getFieldsForCard(cardType, nextContent)) {
    labels.add(field.label);
  }

  for (const label of labels) {
    const previousField = getFieldsForCard(cardType, previousContent).find(
      (field) => field.label === label,
    );
    const nextField = getFieldsForCard(cardType, nextContent).find(
      (field) => field.label === label,
    );
    const previousValue = previousField?.value?.trim() ?? "";
    const nextValue = nextField?.value?.trim() ?? "";

    if (previousValue === nextValue) {
      continue;
    }

    details.push({
      label,
      previousValue: formatDisplayValue(previousField?.value),
      newValue: formatDisplayValue(nextField?.value),
    });
  }

  return details;
}

function buildUndoRequest(
  cardType: CardType,
  cardId: string | null,
  previousContent: unknown,
  nextContent: unknown,
  action: CaseEditResult["action"],
): Omit<ManualMutationRequest, "expected_revision"> | null {
  if (action === "full_regenerate") {
    return null;
  }

  if (action === "edit_card") {
    return {
      action: "edit_card",
      card_type: cardType,
      card_id: cardId,
      content: (previousContent as Record<string, unknown> | null) ?? {},
    };
  }

  if (action === "add_card") {
    const resolvedCardId = getEntityId(cardType, nextContent);
    return {
      action: "delete_card",
      card_type: cardType,
      card_id: resolvedCardId,
      content: null,
    };
  }

  return {
    action: "add_card",
    card_type: cardType,
    card_id: null,
    content: previousContent as Record<string, unknown>,
  };
}

function getEntityId(cardType: CardType, content: unknown) {
  if (cardType === "witness") {
    return (content as WitnessProfile | null)?.witness_id ?? null;
  }

  if (cardType === "evidence") {
    return (content as Evidence | null)?.evidence_id ?? null;
  }

  if (cardType === "disputed_fact") {
    return (content as DisputedFact | null)?.fact_id ?? null;
  }

  return null;
}

function getCardContent(
  caseFile: CaseFile,
  cardType: CardType,
  cardId: string | null,
): unknown {
  if (cardType === "case_metadata") {
    return caseFile;
  }

  if (cardType === "witness") {
    return caseFile.witnesses.find((witness) => witness.witness_id === cardId) ?? null;
  }

  if (cardType === "evidence") {
    return caseFile.evidence.find((item) => item.evidence_id === cardId) ?? null;
  }

  return caseFile.disputed_facts.find((item) => item.fact_id === cardId) ?? null;
}

function getFieldsForCard(cardType: CardType, content: unknown): FieldState[] {
  if (!content) {
    return [];
  }

  if (cardType === "case_metadata") {
    return getOverviewFields(content as CaseFile);
  }

  if (cardType === "witness") {
    return getWitnessFields(content as WitnessProfile);
  }

  if (cardType === "evidence") {
    return getEvidenceFields(content as Evidence);
  }

  return getDisputedFactFields(content as DisputedFact);
}

function getOverviewFields(caseFile: CaseFile): FieldState[] {
  return [
    { label: "Case title", value: caseFile.case_title },
    { label: "Charge or claim", value: caseFile.charge_or_claim },
    {
      label: "Plaintiff or prosecution",
      value: caseFile.parties.plaintiff_or_prosecution,
    },
    { label: "Defendant", value: caseFile.parties.defendant },
    { label: "State", value: caseFile.jurisdiction.state },
    { label: "Court", value: caseFile.jurisdiction.court },
  ];
}

function getWitnessFields(witness: WitnessProfile): FieldState[] {
  return [
    { label: "Name", value: witness.name },
    { label: "Role", value: witness.persona },
    { label: "Side", value: witness.called_by },
    { label: "Knowledge summary", value: witness.knowledge_scope },
  ];
}

function getEvidenceFields(evidence: Evidence): FieldState[] {
  return [
    { label: "Title", value: evidence.evidence_id },
    { label: "Submitted by", value: evidence.submitted_by },
    { label: "Description", value: evidence.description },
  ];
}

function getDisputedFactFields(fact: DisputedFact): FieldState[] {
  return [
    { label: "Factual issue", value: fact.text },
  ];
}
