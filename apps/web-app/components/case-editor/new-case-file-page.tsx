"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import type { StoredCaseFile } from "@/lib/case-files";

export function NewCaseFilePage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!prompt.trim()) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    fetch("/api/case-files", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({}),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`case file creation failed with status ${response.status}`);
        }

        return (await response.json()) as StoredCaseFile;
      })
      .then((payload) => {
        router.push(`/case-files/${payload.id}?seed=${encodeURIComponent(prompt.trim())}`);
      })
      .catch((error: unknown) => {
        setErrorMessage(
          error instanceof Error ? error.message : "case file creation failed",
        );
      })
      .finally(() => {
        setIsSubmitting(false);
      });
  }

  return (
    <main className="min-h-screen bg-[#f4efe7] px-4 py-6 text-[#1b1916] sm:px-6 sm:py-8">
      <section className="mx-auto flex min-h-[calc(100vh-3rem)] w-full max-w-6xl items-center">
        <div className="grid w-full gap-5 lg:grid-cols-[minmax(0,1.08fr)_24rem]">
          <section className="rounded-[12px] border border-[#d4c8b8] bg-[#fbf7f1] px-6 py-8 shadow-[0_20px_60px_rgba(54,42,23,0.08)] sm:px-8 sm:py-10">
            <p className="text-[0.72rem] tracking-[0.24em] text-[#7c6d58] uppercase">
              Conversational case builder
            </p>
            <h1 className="mt-3 max-w-3xl text-[2.4rem] font-medium leading-tight tracking-[-0.04em] text-[#1b1916] sm:text-[3.2rem]">
              Start with the dispute, then shape the record.
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-[#554d43] sm:text-base">
              Describe the matter in plain language. The editor will generate the title, parties, witnesses, evidence, and disputed facts into live editable cards.
            </p>

            <div className="mt-8 grid gap-4 sm:grid-cols-3">
              <InsightCard
                label="Chat-guided"
                value="Scoped edits"
                copy="Select a witness, evidence item, or fact before asking for a refinement."
              />
              <InsightCard
                label="Manual override"
                value="Instant saves"
                copy="Edit any card directly and the next AI turn will use the stored version."
              />
              <InsightCard
                label="Structured output"
                value="Case-first"
                copy="The editor stays grounded in the stored case file instead of loose chat context."
              />
            </div>
          </section>

          <section className="rounded-[12px] border border-[#d4c8b8] bg-[#fbf7f1] p-6 shadow-[0_20px_60px_rgba(54,42,23,0.08)] sm:p-7">
            <div className="space-y-6">
              <div>
                <p className="text-[0.72rem] tracking-[0.24em] text-[#7c6d58] uppercase">
                  New matter
                </p>
                <h2 className="mt-2 text-[1.7rem] font-medium tracking-[-0.03em] text-[#1b1916]">
                  Seed the case file
                </h2>
                <p className="mt-2 text-sm leading-6 text-[#554d43]">
                  Keep it short. A few concrete sentences are enough.
                </p>
              </div>

              <form className="space-y-4" onSubmit={handleSubmit}>
                <label className="block">
                  <span className="mb-2 block text-sm text-[#312c26]">Prompt</span>
                  <textarea
                    value={prompt}
                    onChange={(event) => setPrompt(event.target.value)}
                    placeholder="Example: A civil fraud case involving a startup CFO, two contradictory board witnesses, and a disputed email chain about investor reporting."
                    rows={9}
                    className="w-full rounded-[10px] border border-[#d4c8b8] bg-[#fdfaf5] px-4 py-4 text-sm leading-7 text-[#1b1916] outline-none transition-colors duration-150 placeholder:text-[#8c8071] focus:border-[#8a7757] focus-visible:ring-2 focus-visible:ring-[#26231f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#fbf7f1]"
                  />
                </label>

                {errorMessage ? (
                  <p className="rounded-[10px] border border-[#d3b19f] bg-[#f7e4dc] px-4 py-3 text-sm text-[#7b3f28]">
                    {errorMessage}
                  </p>
                ) : null}

                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="submit"
                    disabled={isSubmitting || prompt.trim().length === 0}
                    className="inline-flex h-10 min-w-[180px] items-center justify-center rounded-[8px] border border-[#26231f] bg-[#26231f] px-5 text-sm font-medium text-[#f4efe6] transition-colors duration-150 hover:bg-[#36312b] disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isSubmitting ? "Preparing editor..." : "Generate case file"}
                  </button>

                  <Link
                    href="/"
                    className="inline-flex h-10 items-center justify-center rounded-[8px] border border-[#cbbbab] bg-[#f7f1e8] px-5 text-sm text-[#26231f] transition-colors duration-150 hover:bg-[#ece4d7]"
                  >
                    Back to library
                  </Link>
                </div>
              </form>
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}

function InsightCard({
  copy,
  label,
  value,
}: {
  copy: string;
  label: string;
  value: string;
}) {
  return (
    <article className="rounded-[10px] border border-[#d4c8b8] bg-[#f7f1e8] p-4">
      <p className="text-[0.68rem] tracking-[0.18em] text-[#7c6d58] uppercase">{label}</p>
      <h3 className="mt-3 text-lg font-medium tracking-[-0.02em] text-[#1b1916]">{value}</h3>
      <p className="mt-2 text-sm leading-6 text-[#554d43]">{copy}</p>
    </article>
  );
}
