"use client";

import { useEffect, useState } from "react";

import { type SimulationRunCatalogItem } from "@/lib/simulation-runs";

type SimulationRunCatalogRequestState = "idle" | "loading" | "ready" | "error";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isCatalogItem(value: unknown): value is SimulationRunCatalogItem {
  if (!isRecord(value) || !isRecord(value.caseFile) || !isRecord(value.playback)) {
    return false;
  }

  return (
    typeof value.simulationRunId === "string" &&
    typeof value.status === "string" &&
    typeof value.caseFile.id === "string" &&
    typeof value.caseFile.charge === "string" &&
    typeof value.playback.turnCount === "number" &&
    typeof value.playback.durationMs === "number"
  );
}

export function useSimulationRunCatalog() {
  const [catalog, setCatalog] = useState<SimulationRunCatalogItem[]>([]);
  const [requestState, setRequestState] =
    useState<SimulationRunCatalogRequestState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    Promise.resolve()
      .then(() => {
        if (cancelled) {
          return null;
        }

        setRequestState("loading");
        setErrorMessage(null);

        return fetch("/api/simulation-runs");
      })
      .then((response) => {
        if (!response) {
          return null;
        }

        if (!response.ok) {
          throw new Error(`simulation run catalog fetch failed with status ${response.status}`);
        }

        return response.json() as Promise<unknown>;
      })
      .then((payload) => {
        if (cancelled || payload === null) {
          return;
        }

        if (!Array.isArray(payload) || !payload.every(isCatalogItem)) {
          throw new Error("simulation run catalog payload does not match the frontend contract");
        }

        setCatalog(payload);
        setRequestState("ready");
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }

        setCatalog([]);
        setRequestState("error");
        setErrorMessage(
          error instanceof Error ? error.message : "simulation run catalog fetch failed",
        );
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return {
    catalog,
    errorMessage,
    requestState,
  };
}
