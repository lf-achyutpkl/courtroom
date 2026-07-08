#!/usr/bin/env python3
import json
import sys
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPT_PATH = ROOT / "app" / "courtroom-transcript.json"
VOICE_CONFIG_PATH = ROOT / "app" / "kokoro-voices.json"
OUTPUT_AUDIO_DIR = ROOT / "public" / "audio"
OUTPUT_MANIFEST_PATH = ROOT / "public" / "manifest.json"


def parse_emotion_and_text(text: str):
    emotion = None
    cleaned = []
    token = ""
    in_brackets = False

    for char in text:
        if char == "[":
            in_brackets = True
            token = ""
            continue
        if char == "]" and in_brackets:
            in_brackets = False
            emotion = (token or "").strip().lower() or emotion
            token = ""
            continue
        if in_brackets:
            token += char
        else:
            cleaned.append(char)

    clean_text = " ".join("".join(cleaned).split())
    return emotion, clean_text


def split_chunks(text: str):
    chunks = []
    current = []
    for char in text:
        current.append(char)
        if char in ".!?":
            chunk = "".join(current).strip()
            if chunk:
                chunks.append(chunk)
            current = []
    if current:
        chunk = "".join(current).strip()
        if chunk:
            chunks.append(chunk)
    return chunks or [text]


def write_wav(path: Path, samples, rate: int):
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(rate)
        wav_file.writeframes(samples.tobytes())


def build_manifest_turn(turn, voice_preset, duration_ms):
    emotion, clean_text = parse_emotion_and_text(turn["text"])
    chunks = split_chunks(clean_text)
    total_chars = sum(len(chunk) for chunk in chunks) or 1
    cursor = 0
    subtitle_chunks = []
    for index, chunk in enumerate(chunks):
        chunk_duration = (
            duration_ms - cursor
            if index == len(chunks) - 1
            else max(900, round((len(chunk) / total_chars) * duration_ms))
        )
        start_ms = cursor
        end_ms = min(duration_ms, start_ms + chunk_duration)
        cursor = end_ms
        subtitle_chunks.append(
            {
                "text": chunk,
                "startMs": start_ms,
                "endMs": end_ms,
            }
        )

    return {
        "turnId": turn["index"],
        "speakerId": turn["speaker_id"],
        "scene": turn["scene"],
        "text": turn["text"],
        "cleanText": clean_text,
        "emotion": emotion,
        "audioUrl": f"/audio/{turn['index']}.wav",
        "durationMs": duration_ms,
        "subtitleChunks": subtitle_chunks,
        "voice": voice_preset["voice"],
        "stylePreset": voice_preset["stylePreset"],
    }


def main():
    try:
        from kokoro import KPipeline
    except ImportError as exc:
        raise SystemExit(
            "Kokoro is not installed. Install with `pip install kokoro soundfile` and ensure `espeak-ng` is available."
        ) from exc

    with TRANSCRIPT_PATH.open() as transcript_file:
        transcript = json.load(transcript_file)
    with VOICE_CONFIG_PATH.open() as voice_file:
        voice_config = json.load(voice_file)

    OUTPUT_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="a")
    manifest = []

    for turn in transcript["audio_script_timeline"]:
        voice_preset = voice_config[turn["speaker_id"]]
        emotion, clean_text = parse_emotion_and_text(turn["text"])
        speed = voice_preset.get("speed", 1.0)
        audio_segments = []

        generator = pipeline(clean_text, voice=voice_preset["voice"], speed=speed)
        for _, _, audio in generator:
            audio_segments.append(audio)

        if not audio_segments:
            print(f"Skipping turn {turn['index']} because Kokoro produced no audio.", file=sys.stderr)
            continue

        import numpy as np

        samples = np.concatenate(audio_segments)
        output_file = OUTPUT_AUDIO_DIR / f"{turn['index']}.wav"
        write_wav(output_file, (samples * 32767).astype(np.int16), 24000)
        duration_ms = round((len(samples) / 24000) * 1000)
        manifest_turn = build_manifest_turn(turn, voice_preset, duration_ms)
        manifest_turn["emotion"] = emotion
        manifest.append(manifest_turn)
        print(f"Generated audio for turn {turn['index']} -> {output_file}")

    with OUTPUT_MANIFEST_PATH.open("w") as manifest_file:
        json.dump(manifest, manifest_file, indent=2)
        manifest_file.write("\n")

    print(f"Wrote manifest to {OUTPUT_MANIFEST_PATH}")


if __name__ == "__main__":
    main()
