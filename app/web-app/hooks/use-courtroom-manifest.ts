"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import {
  buildFallbackManifest,
  type PlaybackManifestTurn,
  type TranscriptData,
} from "@/lib/courtroom";

export function useCourtroomManifest(transcript: TranscriptData) {
  const fallbackManifest = useMemo(
    () => buildFallbackManifest(transcript),
    [transcript],
  );
  const [manifest, setManifest] = useState<PlaybackManifestTurn[]>(fallbackManifest);
  const [manifestSource, setManifestSource] = useState("Estimated preview timeline");
  const loadedManifestRef = useRef(false);

  useEffect(() => {
    if (loadedManifestRef.current) {
      return;
    }

    loadedManifestRef.current = true;

    fetch("/manifest.json")
      .then((response) => {
        if (!response.ok) {
          throw new Error("manifest fetch failed");
        }

        return response.json() as Promise<PlaybackManifestTurn[]>;
      })
      .then((data) => {
        if (!Array.isArray(data) || data.length === 0) {
          return;
        }

        setManifest(data);
        setManifestSource("Generated Kokoro-ready manifest");
      })
      .catch(() => {
        setManifest(fallbackManifest);
      });
  }, [fallbackManifest]);

  return { fallbackManifest, manifest, manifestSource };
}
