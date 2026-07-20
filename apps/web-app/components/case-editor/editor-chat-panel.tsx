import type { CaseEditorMessage } from "@/components/case-editor/case-editor-types";
import {
  EyeIcon,
  JumpIcon,
  SparkIcon,
  StopIcon,
  TextButton,
  UndoIcon,
} from "@/components/case-editor/editor-primitives";
import type { RecentCardChange } from "@/components/case-editor/editor-workspace-utils";

function MessageBubble({
  message,
}: {
  message: CaseEditorMessage;
}) {
  const text = message.parts
    .filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("");

  if (!text) {
    return null;
  }

  const isUser = message.role === "user";

  return (
    <article
      className={`rounded-[18px] border px-4 py-3 text-sm leading-6 shadow-[0_14px_30px_rgba(54,42,23,0.05)] ${
        isUser
          ? "ml-8 border-[#e2cdb0] bg-[#f7ead6] text-[#1f1b16]"
          : "mr-8 border-[#cfd7d7] bg-[linear-gradient(180deg,#f8fbfb_0%,#f1f6f6_100%)] text-[#22302f]"
      }`}
    >
      <p className={`text-[0.64rem] tracking-[0.18em] uppercase ${isUser ? "text-[#7c6d58]" : "text-[#547170]"}`}>
        {isUser ? "You" : "AI assistant"}
      </p>
      <p className="mt-2 whitespace-pre-wrap">{text}</p>
    </article>
  );
}

function ChangeSummary({
  change,
  onJump,
  onReview,
  onUndo,
}: {
  change: RecentCardChange;
  onJump: (change: RecentCardChange) => void;
  onReview: (change: RecentCardChange) => void;
  onUndo: (change: RecentCardChange) => void;
}) {
  return (
    <article className="rounded-[20px] border border-[#d9bf88] bg-[#fff7e7] p-4 shadow-[0_14px_28px_rgba(77,58,23,0.08)]">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[0.64rem] tracking-[0.18em] text-[#7d673f] uppercase">
            AI update
          </p>
          <h3 className="mt-2 text-sm font-medium text-[#2b2418]">
            {change.cardLabel}
          </h3>
        </div>
        <span className="rounded-full border border-[#d5bb87] bg-[#fff0ce] px-2.5 py-1 text-[0.68rem] font-medium text-[#6e511d]">
          Changed
        </span>
      </div>

      <div className="mt-3 space-y-1 text-sm text-[#4f4334]">
        {change.summary.added.length > 0 ? (
          <p>Added: {change.summary.added.join(", ")}</p>
        ) : null}
        {change.summary.changed.length > 0 ? (
          <p>Changed: {change.summary.changed.join(", ")}</p>
        ) : null}
        {change.summary.removed.length > 0 ? (
          <p>Removed: {change.summary.removed.join(", ")}</p>
        ) : null}
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <TextButton
          className="border-[#d7be89] bg-[#fffdf8] text-[#2e2618] hover:bg-[#fff2d4] focus-visible:ring-offset-[#fff7e7]"
          onClick={() => onReview(change)}
        >
          <EyeIcon />
          Review changes
        </TextButton>
        <TextButton
          className="border-[#d7be89] bg-[#fffdf8] text-[#2e2618] hover:bg-[#fff2d4] focus-visible:ring-offset-[#fff7e7]"
          onClick={() => onJump(change)}
        >
          <JumpIcon />
          Jump to changed card
        </TextButton>
        <TextButton
          className="border-[#d7be89] bg-[#fffdf8] text-[#2e2618] hover:bg-[#fff2d4] focus-visible:ring-offset-[#fff7e7]"
          disabled={!change.undoRequest}
          onClick={() => onUndo(change)}
        >
          <UndoIcon />
          Undo
        </TextButton>
      </div>
    </article>
  );
}

export function EditorChatPanel({
  changeHistory,
  input,
  isStreaming,
  messages,
  mutationError,
  onClearFocus,
  onInputChange,
  onJumpToChange,
  onReviewChange,
  onStop,
  onSubmit,
  onUndoChange,
  selectedCardLabel,
  suggestedActions,
}: {
  changeHistory: RecentCardChange[];
  input: string;
  isStreaming: boolean;
  messages: CaseEditorMessage[];
  mutationError: string | null;
  onClearFocus: () => void;
  onInputChange: (value: string) => void;
  onJumpToChange: (change: RecentCardChange) => void;
  onReviewChange: (change: RecentCardChange) => void;
  onStop: () => void;
  onSubmit: () => void;
  onUndoChange: (change: RecentCardChange) => void;
  selectedCardLabel: string | null;
  suggestedActions: Array<{ id: string; label: string; onClick: () => void }>;
}) {
  const latestChanges = changeHistory.slice(-3).reverse();

  return (
    <aside className="flex h-full min-h-0 flex-col overflow-hidden rounded-[24px] border border-[#d8ccbd] bg-[#f8f3eb] shadow-[0_24px_54px_rgba(54,42,23,0.08)]">
      <header className="border-b border-[#e7ddd1] px-4 py-3 sm:px-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-[0.68rem] tracking-[0.2em] text-[#7b6f61] uppercase">
              Conversation
            </p>
            <h2 className="mt-1 text-[1.05rem] font-medium tracking-[-0.025em] text-[#1d1914]">
              Case-building chat
            </h2>
          </div>
          {selectedCardLabel ? (
            <div className="flex items-center gap-2 rounded-full border border-[#decfae] bg-[#fff8e8] px-3 py-1.5">
              <span className="text-sm text-[#403526]">{selectedCardLabel}</span>
              <button
                type="button"
                onClick={onClearFocus}
                className="text-xs font-medium text-[#695128] underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#fff8e8]"
              >
                Clear focus
              </button>
            </div>
          ) : (
            <p className="text-sm text-[#5e554a]">No card selected</p>
          )}
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-3 sm:px-5">
        <div className="space-y-3">
          {messages.length === 0 ? (
            <div className="rounded-[18px] border border-dashed border-[#d8ccbe] bg-[#fffdfa] px-4 py-5 text-sm leading-6 text-[#564d43]">
              Describe the dispute, ask for a first draft, or focus a card and fill in what is missing.
            </div>
          ) : null}

          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {latestChanges.map((change) => (
            <ChangeSummary
              key={change.id}
              change={change}
              onJump={onJumpToChange}
              onReview={onReviewChange}
              onUndo={onUndoChange}
            />
          ))}
        </div>
      </div>

      <div className="border-t border-[#e7ddd1] bg-[#f8f3eb] px-4 py-3 sm:px-5">
        {suggestedActions.length > 0 ? (
          <div className="mb-2.5">
            <p className="text-[0.64rem] tracking-[0.18em] text-[#7c6d58] uppercase">
              Suggested next actions
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {suggestedActions.slice(0, 3).map((action) => (
                <TextButton
                  key={action.id}
                  className="border-[#d8ccbb] bg-[#fffdfa] text-[#2e2720] hover:bg-[#f4ebdd] focus-visible:ring-offset-[#f8f3eb]"
                  onClick={action.onClick}
                >
                  {action.label}
                </TextButton>
              ))}
            </div>
          </div>
        ) : null}

        {mutationError ? (
          <p className="mb-3 rounded-[14px] border border-[#d3b19f] bg-[#f7e4dc] px-3 py-2 text-sm text-[#7b3f28]">
            {mutationError}
          </p>
        ) : null}

        <form
          className="space-y-2.5"
          onSubmit={(event) => {
            event.preventDefault();
            onSubmit();
          }}
        >
          <textarea
            value={input}
            onChange={(event) => onInputChange(event.target.value)}
            rows={3}
            placeholder="Ask for the next change or provide missing case details."
            className="w-full rounded-[18px] border border-[#e0d6ca] bg-[#fffdfa] px-4 py-3.5 text-sm leading-6 text-[#1b1916] outline-none transition-colors duration-150 placeholder:text-[#8e816f] focus:border-[#8a7757] focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f8f3eb]"
          />

          <div className="flex items-center justify-between gap-3">
            <div />
            <div className="flex items-center gap-2">
              {isStreaming ? (
                <button
                  type="button"
                  onClick={onStop}
                  aria-label="Stop response"
                  className="inline-flex h-10 items-center gap-2 rounded-full border border-[#d7cab8] bg-[#fffdfa] px-4 text-sm text-[#2b251e] transition-colors duration-150 hover:bg-[#f4ebdd] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f8f3eb]"
                >
                  <StopIcon />
                  Stop
                </button>
              ) : null}
              <button
                type="submit"
                disabled={isStreaming || input.trim().length === 0}
                className="inline-flex h-10 items-center gap-2 rounded-full border border-[#26231f] bg-[#26231f] px-4 text-sm font-medium text-[#f6f0e7] transition-colors duration-150 hover:bg-[#39332c] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#f8f3eb] disabled:cursor-not-allowed disabled:opacity-60"
              >
                <SparkIcon />
                Send
              </button>
            </div>
          </div>
        </form>
      </div>
    </aside>
  );
}
