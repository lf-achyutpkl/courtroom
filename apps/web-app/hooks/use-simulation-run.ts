"use client";

import { useEffect, useState } from "react";

import { type SimulationRunPayload } from "@/lib/courtroom";

type SimulationRunRequestState = "idle" | "loading" | "ready" | "error";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isSimulationRunPayload(value: unknown): value is SimulationRunPayload {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.simulationRunId === "string" &&
    typeof value.status === "string" &&
    isRecord(value.transcript) &&
    Array.isArray(value.playbackManifest)
  );
}

function getSimulationRunUrl(simulationRunId: string) {
  return `/api/simulation-runs/${simulationRunId}/playback`;
}

export function useSimulationRun(simulationRunId: string | null) {
  const [simulationRun, setSimulationRun] = useState<SimulationRunPayload | null>(null);
  const [requestState, setRequestState] = useState<SimulationRunRequestState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [responseSource, setResponseSource] = useState("Backend response payload");

  useEffect(() => {
    if (!simulationRunId) {
      return;
    }

    let cancelled = false;

    Promise.resolve()
      .then(() => {
        if (cancelled) {
          return null;
        }

        setSimulationRun(null);
        setRequestState("loading");
        setErrorMessage(null);
        setResponseSource("Backend response payload");

        return fetch(getSimulationRunUrl(simulationRunId));
      })
      .then((response) => {
        if (!response) {
          return null;
        }

        if (!response.ok) {
          throw new Error(`simulation run fetch failed with status ${response.status}`);
        }

        return response.json() as Promise<unknown>;
      })
      .then((payload) => {
        if (cancelled || payload === null) {
          return;
        }

        if (!isSimulationRunPayload(payload)) {
          throw new Error("simulation run payload does not match the playback contract");
        }

        setSimulationRun(payload);
        setRequestState("ready");
        setResponseSource("Backend response payload");
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }

        setSimulationRun(null);
        setRequestState("error");
        setResponseSource("Backend response unavailable");
        setErrorMessage(error instanceof Error ? error.message : "simulation run fetch failed");
      });

    return () => {
      cancelled = true;
    };
  }, [simulationRunId]);

  return {
    errorMessage: simulationRunId ? errorMessage : null,
    requestState: simulationRunId ? requestState : "idle",
    responseSource,
    simulationRun: simulationRunId ? simulationRun : null,
  };
}
