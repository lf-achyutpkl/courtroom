"use client";

import { useCallback, useRef, useState } from "react";

export type RecorderState = "idle" | "recording" | "stopping" | "error";

export function useAudioRecorder() {
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const [state, setState] = useState<RecorderState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [recording, setRecording] = useState<Blob | null>(null);

  const start = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setState("error");
      setErrorMessage("Audio recording is not supported by this browser.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = ["audio/webm", "audio/mp4", "audio/ogg"].find((type) =>
        MediaRecorder.isTypeSupported(type),
      );
      const next = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      chunks.current = [];
      setRecording(null);
      next.ondataavailable = (event) => {
        if (event.data.size) chunks.current.push(event.data);
      };
      next.onstop = () => {
        setRecording(new Blob(chunks.current, { type: next.mimeType || "audio/webm" }));
        stream.getTracks().forEach((track) => track.stop());
        setState("idle");
      };
      recorder.current = next;
      next.start();
      setErrorMessage(null);
      setState("recording");
    } catch {
      setState("error");
      setErrorMessage("Microphone permission was denied or unavailable.");
    }
  }, []);

  const stop = useCallback(() => {
    if (recorder.current?.state !== "recording") return;
    setState("stopping");
    recorder.current.stop();
  }, []);

  const clear = useCallback(() => {
    chunks.current = [];
    setRecording(null);
    setErrorMessage(null);
    if (recorder.current?.state !== "recording") setState("idle");
  }, []);

  return { start, stop, clear, recording, state, errorMessage };
}
