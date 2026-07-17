"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { isWitnessSpeaker, type PlaybackManifestTurn } from "@/lib/courtroom";

export type PlaybackMode = "audio" | "timeline";

export function getWitnessOccupant(manifest: PlaybackManifestTurn[], index: number) {
  let latestWitnessId: string | null = null;

  for (let cursor = index; cursor >= 0; cursor -= 1) {
    const turn = manifest[cursor];
    const speakerId = turn?.speakerId;
    if (!turn) {
      continue;
    }

    if (turn.scene === "closing") {
      return null;
    }

    if (speakerId && isWitnessSpeaker(speakerId)) {
      latestWitnessId = speakerId;
      break;
    }
  }

  return latestWitnessId;
}

export function useCourtroomPlayback(manifest: PlaybackManifestTurn[]) {
  const [index, setIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTimeMs, setCurrentTimeMs] = useState(0);
  const [mode, setMode] = useState<PlaybackMode>("timeline");
  const [playbackRate, setPlaybackRate] = useState(1);
  const [volume, setVolume] = useState(1);

  const animationFrameRef = useRef<number | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const transitionTimeoutRef = useRef<number | null>(null);
  const currentTimeRef = useRef(0);

  const currentTurn = manifest[index] ?? null;
  const totalDurationMs = useMemo(
    () => manifest.reduce((total, turn) => total + turn.durationMs, 0),
    [manifest],
  );

  const elapsedBeforeCurrentMs = useMemo(
    () =>
      manifest.slice(0, index).reduce((total, turn) => total + turn.durationMs, 0),
    [manifest, index],
  );

  useEffect(() => {
    currentTimeRef.current = currentTimeMs;
  }, [currentTimeMs]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = playbackRate;
    }
  }, [playbackRate]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume;
    }
  }, [volume]);

  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (transitionTimeoutRef.current) {
        window.clearTimeout(transitionTimeoutRef.current);
      }
      audioRef.current?.pause();
    };
  }, []);

  useEffect(() => {
    if (!currentTurn || !isPlaying) {
      audioRef.current?.pause();
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      return;
    }

    let disposed = false;
    let startedTimeline = false;

    const advanceTurn = () => {
      if (disposed) {
        return;
      }

      setCurrentTimeMs(currentTurn.durationMs);
      currentTimeRef.current = currentTurn.durationMs;
      transitionTimeoutRef.current = window.setTimeout(() => {
        if (index >= manifest.length - 1) {
          setCurrentTimeMs(0);
          currentTimeRef.current = 0;
          setIndex(0);
          setIsPlaying(false);
          return;
        }

        setCurrentTimeMs(0);
        currentTimeRef.current = 0;
        setIndex((value) => value + 1);
      }, 220);
    };

    const runTimeline = (startAtMs: number) => {
      if (disposed || startedTimeline) {
        return;
      }

      startedTimeline = true;
      setMode("timeline");
      const startedAt = performance.now();

      const tick = (timestamp: number) => {
        if (disposed) {
          return;
        }

        const elapsed = Math.min(
          currentTurn.durationMs,
          startAtMs + (timestamp - startedAt) * playbackRate,
        );
        setCurrentTimeMs(elapsed);
        currentTimeRef.current = elapsed;

        if (elapsed >= currentTurn.durationMs) {
          advanceTurn();
          return;
        }

        animationFrameRef.current = requestAnimationFrame(tick);
      };

      animationFrameRef.current = requestAnimationFrame(tick);
    };

    const attemptAudioPlayback = async () => {
      const audio = audioRef.current ?? new Audio();
      audioRef.current = audio;
      audio.pause();
      audio.src = currentTurn.audioUrl;
      audio.currentTime = currentTimeRef.current / 1000;
      audio.playbackRate = playbackRate;
      audio.volume = volume;
      audio.preload = "auto";

      const handleTimeUpdate = () => {
        const nextTime = audio.currentTime * 1000;
        setCurrentTimeMs(nextTime);
        currentTimeRef.current = nextTime;
      };

      const handleEnded = () => {
        advanceTurn();
      };

      const handleError = () => {
        audio.removeEventListener("timeupdate", handleTimeUpdate);
        audio.removeEventListener("ended", handleEnded);
        runTimeline(currentTimeRef.current);
      };

      audio.addEventListener("timeupdate", handleTimeUpdate);
      audio.addEventListener("ended", handleEnded);
      audio.addEventListener("error", handleError, { once: true });

      try {
        await audio.play();
        if (disposed) {
          audio.pause();
          return;
        }
        setMode("audio");
      } catch {
        handleError();
      }
    };

    void attemptAudioPlayback();

    return () => {
      disposed = true;
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      if (transitionTimeoutRef.current) {
        window.clearTimeout(transitionTimeoutRef.current);
        transitionTimeoutRef.current = null;
      }
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.removeAttribute("src");
        audioRef.current.load();
      }
    };
  }, [currentTurn, index, isPlaying, manifest, playbackRate, volume]);

  const overallProgress = totalDurationMs
    ? (elapsedBeforeCurrentMs + currentTimeMs) / totalDurationMs
    : 0;

  const elapsedMs = elapsedBeforeCurrentMs + currentTimeMs;

  const seekTo = (nextElapsedMs: number) => {
    if (manifest.length === 0) {
      return;
    }

    const clampedElapsedMs = Math.max(0, Math.min(totalDurationMs, nextElapsedMs));
    let remainingElapsedMs = clampedElapsedMs;
    let nextIndex = manifest.length - 1;

    for (let cursor = 0; cursor < manifest.length; cursor += 1) {
      const turn = manifest[cursor];
      if (remainingElapsedMs <= turn.durationMs || cursor === manifest.length - 1) {
        nextIndex = cursor;
        break;
      }
      remainingElapsedMs -= turn.durationMs;
    }

    const nextTurn = manifest[nextIndex];
    const nextCurrentTimeMs =
      nextIndex === manifest.length - 1 && clampedElapsedMs === totalDurationMs
        ? nextTurn.durationMs
        : remainingElapsedMs;

    currentTimeRef.current = nextCurrentTimeMs;
    setIndex(nextIndex);
    setCurrentTimeMs(nextCurrentTimeMs);
  };

  const goToTurn = (nextIndex: number) => {
    if (nextIndex < 0 || nextIndex >= manifest.length) {
      return;
    }

    currentTimeRef.current = 0;
    setIndex(nextIndex);
    setCurrentTimeMs(0);
  };

  return {
    currentTurn,
    currentTimeMs,
    elapsedMs,
    index,
    isPlaying,
    mode,
    overallProgress,
    playbackRate,
    totalDurationMs,
    volume,
    goToTurn,
    seekTo,
    setCurrentTimeMs,
    setIndex,
    setIsPlaying,
    setPlaybackRate,
    setVolume,
  };
}
