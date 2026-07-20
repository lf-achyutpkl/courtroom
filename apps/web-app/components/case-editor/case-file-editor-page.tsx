"use client";

import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  startTransition,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import type { CaseEditorMessage } from "@/components/case-editor/case-editor-types";
import { EditorCardGrid } from "@/components/case-editor/editor-card-grid";
import { EditorChatPanel } from "@/components/case-editor/editor-chat-panel";
import {
  ArrowLeftIcon,
  EyeIcon,
  SparkIcon,
  TextButton,
  WarningIcon,
} from "@/components/case-editor/editor-primitives";
import { EditorStatus } from "@/components/case-editor/editor-status";
import type {
  EditorTarget,
  RecentCardChange,
} from "@/components/case-editor/editor-workspace-utils";
import {
  buildRecentChange,
  getCaseReadiness,
  getChatFocusLabel,
} from "@/components/case-editor/editor-workspace-utils";
import { useCaseFile } from "@/hooks/use-case-file";
import {
  applyCaseEditResult,
  type CaseEditResult,
  type CaseFile,
  type ManualMutationRequest,
} from "@/lib/case-files";

function applyManualRequest(caseFile: CaseFile, request: ManualMutationRequest) {
  if (request.action === "delete_card") {
    return applyCaseEditResult(caseFile, {
      action: "delete_card",
      card_type: request.card_type,
      card_id: request.card_id,
      updated_content: null,
    });
  }

  if (request.action === "edit_card") {
    if (request.card_type === "case_metadata") {
      const content = request.content ?? {};
      return {
        ...caseFile,
        ...content,
        parties: {
          ...caseFile.parties,
          ...((content.parties as CaseFile["parties"] | undefined) ?? {}),
        },
        jurisdiction: {
          ...caseFile.jurisdiction,
          ...((content.jurisdiction as CaseFile["jurisdiction"] | undefined) ?? {}),
        },
      };
    }

    const existing =
      request.card_type === "witness"
        ? caseFile.witnesses.find((item) => item.witness_id === request.card_id)
        : request.card_type === "evidence"
          ? caseFile.evidence.find((item) => item.evidence_id === request.card_id)
          : caseFile.disputed_facts.find((item) => item.fact_id === request.card_id);

    return applyCaseEditResult(caseFile, {
      action: "edit_card",
      card_type: request.card_type,
      card_id: request.card_id,
      updated_content: {
        ...existing,
        ...(request.content ?? {}),
      } as never,
    });
  }

  return applyCaseEditResult(caseFile, {
    action: "add_card",
    card_type: request.card_type,
    card_id: request.card_id,
    updated_content: request.content as never,
  });
}

export function CaseFileEditorPage({ caseFileId }: { caseFileId: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const seedPrompt = searchParams.get("seed");
  const { errorMessage, record, requestState, setRecord } = useCaseFile(caseFileId);
  const [selectedTarget, setSelectedTarget] = useState<EditorTarget | null>(null);
  const [editorTarget, setEditorTarget] = useState<EditorTarget | null>(null);
  const [input, setInput] = useState("");
  const [mutationError, setMutationError] = useState<string | null>(null);
  const [pendingMutationKey, setPendingMutationKey] = useState<string | null>(null);
  const [changeHistory, setChangeHistory] = useState<RecentCardChange[]>([]);
  const [recentAiChange, setRecentAiChange] = useState<RecentCardChange | null>(null);
  const [reviewChange, setReviewChange] = useState<RecentCardChange | null>(null);
  const [mobileView, setMobileView] = useState<"chat" | "case">("chat");
  const hasSentSeedPrompt = useRef(false);
  const recordRef = useRef(record);

  useEffect(() => {
    recordRef.current = record;
  }, [record]);

  const selectedCard =
    selectedTarget?.kind === "existing" ? selectedTarget.card : null;

  const transport = useMemo(
    () =>
      new DefaultChatTransport<CaseEditorMessage>({
        api: `/api/case-files/${caseFileId}/messages`,
        prepareSendMessagesRequest: ({ messages }) => {
          const latestUserMessage = [...messages]
            .reverse()
            .find((message) => message.role === "user");
          const latestText = latestUserMessage?.parts
            .filter((part) => part.type === "text")
            .map((part) => part.text)
            .join("")
            .trim();

          return {
            body: {
              message: latestText ?? "",
              selected_card: selectedCard,
            },
          };
        },
      }),
    [caseFileId, selectedCard],
  );

  const { messages, sendMessage, status, stop } = useChat<CaseEditorMessage>({
    id: caseFileId,
    transport,
    onData: (part) => {
      if (part.type !== "data-case-file-update") {
        return;
      }

      const previousRecord = recordRef.current;
      if (!previousRecord) {
        return;
      }

      const nextCaseFile = applyCaseEditResult(previousRecord.case_file, part.data);
      const change = buildRecentChange(previousRecord.case_file, part.data);

      setRecord({
        ...previousRecord,
        revision: previousRecord.revision + 1,
        updated_at: new Date().toISOString(),
        case_file: nextCaseFile,
      });

      if (change) {
        setRecentAiChange(change);
        setReviewChange(change);
        setChangeHistory((current) => [...current, change].slice(-8));
      }
    },
  });

  useEffect(() => {
    if (!seedPrompt || hasSentSeedPrompt.current || requestState !== "ready") {
      return;
    }

    hasSentSeedPrompt.current = true;
    void sendMessage({ text: seedPrompt });
    startTransition(() => {
      router.replace(`/case-files/${caseFileId}`);
    });
  }, [caseFileId, requestState, router, seedPrompt, sendMessage]);

  async function applyManualMutation(
    request: ManualMutationRequest,
    optimisticUpdate: (caseFile: CaseFile) => CaseFile,
  ) {
    if (!recordRef.current) {
      return;
    }

    const previousRecord = recordRef.current;
    setMutationError(null);
    setPendingMutationKey(
      `${request.action}:${request.card_type}:${request.card_id ?? "none"}`,
    );
    setRecord({
      ...previousRecord,
      revision: previousRecord.revision + 1,
      updated_at: new Date().toISOString(),
      case_file: optimisticUpdate(previousRecord.case_file),
    });

    try {
      const response = await fetch(`/api/case-files/${caseFileId}/mutations`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as
          | { detail?: string }
          | null;
        throw new Error(payload?.detail ?? `mutation failed with status ${response.status}`);
      }

      const payload = (await response.json()) as {
        revision: number;
        operation: CaseEditResult;
      };
      setRecord((current) =>
        current
          ? {
              ...current,
              revision: payload.revision,
              updated_at: new Date().toISOString(),
              case_file: applyCaseEditResult(previousRecord.case_file, payload.operation),
            }
          : current,
      );
    } catch (error: unknown) {
      setRecord(previousRecord);
      setMutationError(error instanceof Error ? error.message : "mutation failed");
    } finally {
      setPendingMutationKey(null);
    }
  }

  async function handleUndoChange(change: RecentCardChange) {
    if (!change.undoRequest || !recordRef.current) {
      return;
    }

    const undoRequest: ManualMutationRequest = {
      action: change.undoRequest.action,
      card_type: change.undoRequest.card_type,
      card_id: change.undoRequest.card_id,
      content: change.undoRequest.content,
      expected_revision: recordRef.current.revision,
    };

    await applyManualMutation(
      undoRequest,
      (current) => applyManualRequest(current, undoRequest),
    );

    setChangeHistory((current) => current.filter((item) => item.id !== change.id));
    if (recentAiChange?.id === change.id) {
      setRecentAiChange(null);
    }
    if (reviewChange?.id === change.id) {
      setReviewChange(null);
    }
  }

  if (requestState === "loading" || requestState === "idle") {
    return (
      <EditorStatus
        title="Loading case file"
        description="Fetching the persisted record and structured outline."
      />
    );
  }

  if (requestState === "error" || !record) {
    return (
      <EditorStatus
        title="Case file unavailable"
        description={errorMessage ?? "The editor could not load this case file."}
      />
    );
  }

  const caseFile = record.case_file;
  const readiness = getCaseReadiness(caseFile);
  const selectedCardLabel = getChatFocusLabel(caseFile, selectedTarget);
  const isStreaming = status === "submitted" || status === "streaming";
  const latestChange = recentAiChange ?? changeHistory.at(-1) ?? null;
  const suggestedActions = buildSuggestedActions(
    caseFile,
    selectedTarget,
    setInput,
    setSelectedTarget,
    setEditorTarget,
  );

  return (
    <main className="h-[100dvh] overflow-hidden bg-[radial-gradient(circle_at_top_left,_rgba(255,255,255,0.76),_transparent_34%),linear-gradient(180deg,_#f4eee5_0%,_#ede4d7_100%)] px-3 py-3 text-[#1b1916] sm:px-4 sm:py-4">
      <section className="mx-auto flex h-full max-w-[112rem] flex-col gap-2.5">
        <header className="rounded-[22px] border border-[#d8ccbd] bg-[#faf6ef] px-4 py-3 shadow-[0_16px_34px_rgba(54,42,23,0.06)] sm:px-5">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-3">
                <Link
                  href="/"
                  aria-label="Back to library"
                  className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-[#ddd2c4] bg-[#fffdfa] text-[#3f382f] transition-colors duration-150 hover:bg-[#f4ebdd] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#faf6ef]"
                >
                  <ArrowLeftIcon />
                </Link>
                <div className="min-w-0">
                  <p className="text-[0.68rem] tracking-[0.2em] text-[#7b6f61] uppercase">
                    Conversational case editor
                  </p>
                  <h1 className="truncate text-[1.2rem] font-medium tracking-[-0.03em] text-[#171411] sm:text-[1.35rem]">
                    {caseFile.case_title.trim() || "Untitled case"}
                  </h1>
                </div>
              </div>

              <div className="mt-2 flex flex-wrap gap-2">
                <span className="rounded-full border border-[#ddd1c4] bg-[#fffdfa] px-3 py-1.5 text-sm text-[#4f473d]">
                  {record.status === "ready" ? "Ready draft" : "Draft"}
                </span>
                <span className="rounded-full border border-[#ddd1c4] bg-[#fffdfa] px-3 py-1.5 text-sm text-[#4f473d]">
                  {readiness.percentComplete}% complete
                </span>
                <span className="rounded-full border border-[#ddd1c4] bg-[#fffdfa] px-3 py-1.5 text-sm text-[#4f473d]">
                  {readiness.completeItems}/{readiness.totalItems} complete items
                </span>
                {readiness.missingRequiredDetails > 0 ? (
                  <span className="inline-flex items-center gap-2 rounded-full border border-[#e1cab8] bg-[#fff3ea] px-3 py-1.5 text-sm text-[#824d2c]">
                    <WarningIcon />
                    {readiness.missingRequiredDetails} missing details
                  </span>
                ) : null}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <TextButton
                className="border-[#d8ccbb] bg-[#fffdfa] text-[#2d2620] hover:bg-[#f4ebdd] focus-visible:ring-offset-[#faf6ef]"
                onClick={() => {
                  if (latestChange?.selectedCard) {
                    setSelectedTarget({
                      kind: "existing",
                      card: latestChange.selectedCard,
                    });
                    setEditorTarget({
                      kind: "existing",
                      card: latestChange.selectedCard,
                    });
                    setReviewChange(latestChange);
                    setMobileView("case");
                    return;
                  }

                  setSelectedTarget({
                    kind: "existing",
                    card: { card_type: "case_metadata", card_id: null },
                  });
                  setEditorTarget({
                    kind: "existing",
                    card: { card_type: "case_metadata", card_id: null },
                  });
                  setMobileView("case");
                }}
              >
                <EyeIcon />
                Preview
              </TextButton>
              <button
                type="button"
                disabled
                title="Simulation launch is not wired from this editor view."
                className="inline-flex h-10 items-center gap-2 rounded-full border border-[#26231f] bg-[#26231f] px-4 text-sm font-medium text-[#f6f0e7] opacity-70"
              >
                <SparkIcon />
                Start simulation
              </button>
            </div>
          </div>
        </header>

        <div className="xl:hidden">
          <div className="grid grid-cols-2 gap-2 rounded-[18px] border border-[#d9cec0] bg-[#f8f3eb] p-1">
            {(["chat", "case"] as const).map((view) => (
              <button
                key={view}
                type="button"
                onClick={() => setMobileView(view)}
                className={`rounded-[14px] px-4 py-2.5 text-sm font-medium capitalize transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f8f3eb] ${
                  mobileView === view
                    ? "bg-[#fffdfa] text-[#191512] shadow-[0_10px_24px_rgba(54,42,23,0.08)]"
                    : "text-[#62584c]"
                }`}
              >
                {view}
              </button>
            ))}
          </div>
        </div>

        <section className="grid min-h-0 flex-1 gap-3 xl:grid-cols-[minmax(0,1.22fr)_minmax(24rem,0.78fr)]">
          <div className={`${mobileView === "chat" ? "block" : "hidden"} min-h-0 xl:block`}>
            <EditorChatPanel
              changeHistory={changeHistory}
              input={input}
              isStreaming={isStreaming}
              messages={messages}
              mutationError={mutationError}
              onClearFocus={() => {
                setSelectedTarget(null);
                setEditorTarget(null);
                setReviewChange(null);
              }}
              onInputChange={setInput}
              onJumpToChange={(change) => {
                if (!change.selectedCard) {
                  return;
                }

                setSelectedTarget({ kind: "existing", card: change.selectedCard });
                setEditorTarget({ kind: "existing", card: change.selectedCard });
                setReviewChange(null);
                setMobileView("case");
              }}
              onReviewChange={(change) => {
                if (!change.selectedCard) {
                  return;
                }

                setSelectedTarget({ kind: "existing", card: change.selectedCard });
                setEditorTarget({ kind: "existing", card: change.selectedCard });
                setReviewChange(change);
                setMobileView("case");
              }}
              onStop={() => {
                void stop();
              }}
              onSubmit={() => {
                const trimmed = input.trim();
                if (!trimmed) {
                  return;
                }

                void sendMessage({ text: trimmed });
                setInput("");
              }}
              onUndoChange={(change) => {
                void handleUndoChange(change);
              }}
              selectedCardLabel={selectedCardLabel}
              suggestedActions={suggestedActions}
            />
          </div>

          <div className={`${mobileView === "case" ? "block" : "hidden"} min-h-0 xl:block`}>
            <EditorCardGrid
              applyManualMutation={applyManualMutation}
              caseFile={caseFile}
              editorTarget={editorTarget}
              onCloseEditor={() => {
                setReviewChange(null);
                setEditorTarget(null);
              }}
              onDeleteCard={(card) => {
                setSelectedTarget((current) => {
                  if (current?.kind !== "existing") {
                    return current;
                  }

                  if (
                    current.card.card_type === card.card_type &&
                    current.card.card_id === card.card_id
                  ) {
                    return null;
                  }

                  return current;
                });
              }}
              onOpenEditor={(target) => {
                setSelectedTarget(target);
                setEditorTarget(target);
                if (
                  target.kind !== "existing" ||
                  !reviewChange?.selectedCard ||
                  reviewChange.selectedCard.card_type !== target.card.card_type ||
                  reviewChange.selectedCard.card_id !== target.card.card_id
                ) {
                  setReviewChange(null);
                }
              }}
              pendingMutationKey={pendingMutationKey}
              recentAiChange={recentAiChange}
              recordRevision={record.revision}
              reviewChange={reviewChange}
              selectedTarget={selectedTarget}
            />
          </div>
        </section>
      </section>

      {latestChange ? (
        <div className="pointer-events-none fixed inset-x-3 bottom-3 z-30 xl:hidden">
          <div className="pointer-events-auto flex items-center justify-between gap-3 rounded-[18px] border border-[#d6bc86] bg-[#fff7e7] px-4 py-3 shadow-[0_18px_36px_rgba(54,42,23,0.12)]">
            <p className="text-sm font-medium text-[#2b2418]">
              {changeHistory.length} {changeHistory.length === 1 ? "change" : "changes"} made
            </p>
            <div className="flex items-center gap-2">
              <TextButton
                className="border-[#d7be89] bg-[#fffdfa] text-[#2e2618] hover:bg-[#fff2d4] focus-visible:ring-offset-[#fff7e7]"
                onClick={() => {
                  if (latestChange.selectedCard) {
                    setSelectedTarget({ kind: "existing", card: latestChange.selectedCard });
                    setEditorTarget({ kind: "existing", card: latestChange.selectedCard });
                    setReviewChange(latestChange);
                    setMobileView("case");
                  }
                }}
              >
                Review
              </TextButton>
              <TextButton
                className="border-[#d7be89] bg-[#fffdfa] text-[#2e2618] hover:bg-[#fff2d4] focus-visible:ring-offset-[#fff7e7]"
                disabled={!latestChange.undoRequest}
                onClick={() => {
                  void handleUndoChange(latestChange);
                }}
              >
                Undo
              </TextButton>
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}

function buildSuggestedActions(
  caseFile: CaseFile,
  editorTarget: EditorTarget | null,
  setInput: (value: string) => void,
  setSelectedTarget: (target: EditorTarget | null) => void,
  setEditorTarget: (target: EditorTarget | null) => void,
) {
  const actions: Array<{ id: string; label: string; onClick: () => void }> = [];

  if (editorTarget?.kind === "existing" && editorTarget.card.card_type === "witness") {
    actions.push({
      id: "witness-detail",
      label: "Ask for stronger witness detail",
      onClick: () =>
        setInput("Refine this witness with a clearer role, what they know, and why their testimony matters."),
    });
  }

  if (caseFile.witnesses.length === 0) {
    actions.push({
      id: "first-witness",
      label: "Add the first witness",
      onClick: () =>
        setInput("Add the first witness and explain what they personally know about the dispute."),
    });
  }

  if (caseFile.evidence.length === 0) {
    actions.push({
      id: "first-evidence",
      label: "Add supporting evidence",
      onClick: () =>
        setInput("Add one concrete evidence item with who submitted it and why it matters."),
    });
  }

  if (caseFile.disputed_facts.length === 0) {
    actions.push({
      id: "first-fact",
      label: "Define a disputed fact",
      onClick: () =>
        setInput("Identify the main disputed fact the parties disagree about."),
    });
  }

  if (actions.length < 3) {
    actions.push({
      id: "overview",
      label: "Review case overview",
      onClick: () => {
        setSelectedTarget({
          kind: "existing",
          card: { card_type: "case_metadata", card_id: null },
        });
        setEditorTarget({
          kind: "existing",
          card: { card_type: "case_metadata", card_id: null },
        });
      },
    });
  }

  return actions.slice(0, 3);
}
