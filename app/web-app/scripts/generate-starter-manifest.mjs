import fs from "node:fs/promises";
import path from "node:path";

import transcript from "../app/courtroom-transcript.json" with { type: "json" };
import voiceConfig from "../app/kokoro-voices.json" with { type: "json" };

const SENTENCE_SPLIT_REGEX = /[^.!?]+[.!?]+|[^.!?]+$/g;

function parseEmotionAndText(text) {
  const match = text.match(/\[(?<emotion>[^[\]]+)\]/);
  const emotion = match?.groups?.emotion?.trim().toLowerCase() ?? null;
  const cleanText = text.replace(/\s*\[[^[\]]+\]\s*/g, " ").replace(/\s+/g, " ").trim();

  return { emotion, cleanText };
}

function splitIntoSubtitleChunks(text) {
  return (text.match(SENTENCE_SPLIT_REGEX) ?? [text])
    .map((chunk) => chunk.trim())
    .filter(Boolean);
}

function estimateDurationMs(text, speed = 1) {
  const words = text.split(/\s+/).filter(Boolean).length;
  const rawDuration = words * 360 + Math.max(600, text.length * 16);
  return Math.max(1800, Math.round(rawDuration / speed));
}

function buildSubtitleChunks(text, durationMs) {
  const chunks = splitIntoSubtitleChunks(text);
  const totalChars = chunks.reduce((sum, chunk) => sum + chunk.length, 0) || 1;
  let cursor = 0;

  return chunks.map((chunk, index) => {
    const chunkDuration =
      index === chunks.length - 1
        ? durationMs - cursor
        : Math.max(900, Math.round((chunk.length / totalChars) * durationMs));
    const startMs = cursor;
    const endMs = Math.min(durationMs, startMs + chunkDuration);
    cursor = endMs;

    return { text: chunk, startMs, endMs };
  });
}

const manifest = transcript.audio_script_timeline.map((turn) => {
  const preset = voiceConfig[turn.speaker_id];
  const { emotion, cleanText } = parseEmotionAndText(turn.text);
  const durationMs = estimateDurationMs(cleanText, preset?.speed ?? 1);

  return {
    turnId: turn.index,
    speakerId: turn.speaker_id,
    scene: turn.scene,
    text: turn.text,
    cleanText,
    emotion,
    audioUrl: `/audio/${turn.index}.wav`,
    durationMs,
    subtitleChunks: buildSubtitleChunks(cleanText, durationMs),
  };
});

const outputPath = path.join(process.cwd(), "public", "manifest.json");
await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.writeFile(outputPath, `${JSON.stringify(manifest, null, 2)}\n`);

console.log(`Wrote ${manifest.length} manifest turns to ${outputPath}`);
