import voiceConfig from "@/app/kokoro-voices.json";

export type TranscriptTurn = {
  index: number;
  scene: string;
  speaker_id: string;
  text: string;
};

export type TranscriptData = {
  case_metadata: {
    case_id: string;
    case_type: string;
    charge: string;
    defendant: string;
    prosecution: string;
  };
  voice_character_map: Record<
    string,
    {
      role?: string;
      name?: string;
      gender?: string;
      suggested_tone?: string;
    }
  >;
  audio_script_timeline: TranscriptTurn[];
};

export type SubtitleChunk = {
  text: string;
  startMs: number;
  endMs: number;
};

export type PlaybackManifestTurn = {
  turnId: number;
  speakerId: string;
  scene: string;
  text: string;
  cleanText: string;
  emotion: string | null;
  audioUrl: string;
  durationMs: number;
  subtitleChunks: SubtitleChunk[];
};

export type VoicePreset = {
  voice: string;
  speed: number;
  stylePreset: string;
};

export const kokoroVoiceConfig = voiceConfig as Record<string, VoicePreset>;

const SENTENCE_SPLIT_REGEX = /[^.!?]+[.!?]+|[^.!?]+$/g;
const EMOTION_REGEX = /\[([^[\]]+)\]/;

export function parseEmotionAndText(text: string) {
  const match = text.match(EMOTION_REGEX);
  const emotion = match?.[1]?.trim().toLowerCase() ?? null;
  const cleanText = text.replace(/\s*\[[^[\]]+\]\s*/g, " ").replace(/\s+/g, " ").trim();

  return { emotion, cleanText };
}

export function splitIntoSubtitleChunks(text: string) {
  const matches = text.match(SENTENCE_SPLIT_REGEX) ?? [text];
  return matches.map((chunk) => chunk.trim()).filter(Boolean);
}

export function estimateDurationMs(text: string, speed = 1) {
  const words = text.split(/\s+/).filter(Boolean).length;
  const rawDuration = words * 360 + Math.max(600, text.length * 16);
  return Math.max(1800, Math.round(rawDuration / speed));
}

export function buildSubtitleChunks(text: string, durationMs: number): SubtitleChunk[] {
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

export function buildFallbackManifest(transcript: TranscriptData): PlaybackManifestTurn[] {
  return transcript.audio_script_timeline.map((turn) => {
    const preset = kokoroVoiceConfig[turn.speaker_id];
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
}

export function getSpeakerLabel(transcript: TranscriptData, speakerId: string) {
  const speaker = transcript.voice_character_map[speakerId];
  if (!speaker) {
    return speakerId;
  }

  return speaker.name ? `${speaker.name} · ${speaker.role}` : speaker.role ?? speakerId;
}

export function getSpeakerShortName(transcript: TranscriptData, speakerId: string) {
  const speaker = transcript.voice_character_map[speakerId];
  return speaker?.name ?? speaker?.role ?? speakerId;
}

export function getSpeakerTone(transcript: TranscriptData, speakerId: string) {
  return transcript.voice_character_map[speakerId]?.suggested_tone ?? "Measured";
}

export function isWitnessSpeaker(speakerId: string) {
  return speakerId.startsWith("W");
}

export function getSceneLabel(scene: string) {
  return scene.charAt(0).toUpperCase() + scene.slice(1);
}

export function getCurrentSubtitle(
  subtitleChunks: SubtitleChunk[],
  currentTimeMs: number,
) {
  return (
    subtitleChunks.find(
      (chunk) => currentTimeMs >= chunk.startMs && currentTimeMs < chunk.endMs,
    ) ?? subtitleChunks.at(-1) ?? null
  );
}
