"use client";

import { useEffect, useState } from "react";

import type { StoredCaseFile } from "@/lib/case-files";

type RequestState = "idle" | "loading" | "ready" | "error";

export function useCaseFile(caseFileId: string) {
  const [record, setRecord] = useState<StoredCaseFile | null>(null);
  const [requestState, setRequestState] = useState<RequestState>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetch(`/api/case-files/${caseFileId}`, {
      cache: "no-store",
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`case file fetch failed with status ${response.status}`);
        }

        return (await response.json()) as StoredCaseFile;
      })
      .then((payload) => {
        if (cancelled) {
          return;
        }

        setRecord(payload);
        setRequestState("ready");
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }

        setRequestState("error");
        setErrorMessage(
          error instanceof Error ? error.message : "case file fetch failed",
        );
      });

    return () => {
      cancelled = true;
    };
  }, [caseFileId]);

  return {
    errorMessage,
    record,
    requestState,
    setRecord,
  };
}
