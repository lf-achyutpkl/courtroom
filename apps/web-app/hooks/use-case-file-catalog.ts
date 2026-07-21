"use client";

import { useCallback, useEffect, useState } from "react";

import type { StoredCaseFile } from "@/lib/case-files";

type RequestState = "idle" | "loading" | "ready" | "error";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isStoredCaseFile(value: unknown): value is StoredCaseFile {
  return (
    isRecord(value) &&
    typeof value.id === "string" &&
    typeof value.status === "string" &&
    typeof value.revision === "number" &&
    typeof value.created_at === "string" &&
    typeof value.updated_at === "string" &&
    isRecord(value.case_file)
  );
}

export function useCaseFileCatalog() {
  const [caseFiles, setCaseFiles] = useState<StoredCaseFile[]>([]);
  const [requestState, setRequestState] = useState<RequestState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => {
    setReloadKey((value) => value + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;

    Promise.resolve()
      .then(() => {
        if (cancelled) {
          return null;
        }

        setRequestState("loading");
        setErrorMessage(null);
        return fetch("/api/case-files", { cache: "no-store" });
      })
      .then((response) => {
        if (!response) {
          return null;
        }

        if (!response.ok) {
          throw new Error(`case file catalog fetch failed with status ${response.status}`);
        }

        return response.json() as Promise<unknown>;
      })
      .then((payload) => {
        if (cancelled || payload === null) {
          return;
        }

        if (!Array.isArray(payload) || !payload.every(isStoredCaseFile)) {
          throw new Error("case file catalog payload does not match the frontend contract");
        }

        setCaseFiles(payload);
        setRequestState("ready");
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }

        setCaseFiles([]);
        setRequestState("error");
        setErrorMessage(
          error instanceof Error ? error.message : "case file catalog fetch failed",
        );
      });

    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  return {
    caseFiles,
    errorMessage,
    reload,
    requestState,
  };
}
