Architected three-part pipeline integrating TTS timestamps with PixiJS animations
Architected three-part pipeline integrating TTS timestamps with PixiJS animations
Good, confirmed — ElevenLabs' convert-with-timestamps endpoint returns character-level start/end times per character, which is exactly the sync signal this needs. Here's the full pipeline, split into the two stages we already committed to: pre-generation (once, offline) and playback (runtime, zero API calls).

Stage 1: Pre-generation — turn your JSON into a playable manifest
Run this once per case, not on every playback. For each entry in audio_script_timeline, synthesize audio with per-character timestamps, then collapse those into sentence-level chunks (since these texts are long paragraphs — a single "speech bubble" per turn won't work, more on that below).

javascript
// scripts/generate-audio-manifest.js — run once, offline, not at request time
import fs from "fs/promises";
import script from "../data/trial_script.json" assert { type: "json" };

const VOICE_IDS = {
prosecution: "voice_id_for_prosecution",
defense: "voice_id_for_defense",
judge: "voice_id_for_judge",
W1: "voice_id_for_laura", W2: "voice_id_for_victor",
W3: "voice_id_for_samantha", W5: "voice_id_for_evelyn",
};

function splitIntoSentences(text) {
return text.match(/[^.!?]+[.!?]+/g)?.map(s => s.trim()) ?? [text];
}

async function synthesizeTurn(turn) {
const res = await fetch(
`https://api.elevenlabs.io/v1/text-to-speech/${VOICE_IDS[turn.speaker_id]}/with-timestamps`,
{
method: "POST",
headers: { "xi-api-key": process.env.ELEVENLABS_API_KEY, "Content-Type": "application/json" },
body: JSON.stringify({ text: turn.text, model_id: "eleven_multilingual_v2" }),
}
);
const { audio_base64, alignment } = await res.json();

// Collapse character-level timestamps into sentence-level chunks for subtitles
const sentences = splitIntoSentences(turn.text);
let charCursor = 0;
const subtitle_chunks = sentences.map(sentence => {
const startIdx = charCursor;
const endIdx = charCursor + sentence.length;
charCursor = endIdx + 1; // skip the space/punct between sentences
return {
text: sentence,
start: alignment.character_start_times_seconds[startIdx] ?? 0,
end: alignment.character_end_times_seconds[Math.min(endIdx, alignment.character_end_times_seconds.length - 1)],
};
});

const audioPath = `public/audio/${turn.index}.mp3`;
await fs.writeFile(audioPath, Buffer.from(audio_base64, "base64"));

return {
index: turn.index,
scene: turn.scene,
speaker_id: turn.speaker_id,
audio_url: `/audio/${turn.index}.mp3`,
duration: alignment.character_end_times_seconds.at(-1),
subtitle_chunks,
};
}

const manifest = await Promise.all(script.audio_script_timeline.map(synthesizeTurn));
await fs.writeFile("public/manifest.json", JSON.stringify(manifest, null, 2));
That gives your frontend a clean, pre-synced manifest — no LLM or TTS calls happen at playback time, matching the architecture you committed to earlier.

The long-text problem — worth flagging directly
Looking at your actual data, several turns (the opening statements, W1's methodology answer at index 5) are full paragraphs — a comic-style speech bubble genuinely doesn't work here, it'd either overflow the screen or need to be tiny and unreadable. The practical fix: separate the "is this character speaking" indicator from the actual text. Use a small pulsing "..." or icon bubble above the character's head just to show who's talking, and a caption/subtitle bar along the bottom of the stage that advances sentence-by-sentence using the subtitle_chunks timing — this is standard practice in games/visual novels with long dialogue for exactly this reason, and it'll look and function much better than trying to cram paragraphs into a cartoon bubble.

Stage 2: PixiJS playback
Character positions, driven by role from voice_character_map:

javascript
const STAGE_POSITIONS = {
prosecution: { x: 200, y: 400 },
defense: { x: 600, y: 400 },
judge: { x: 400, y: 150 },
witness: { x: 400, y: 350 }, // whichever witness is currently speaking occupies this spot
};

function resolvePosition(speakerId, voiceMap) {
if (["prosecution", "defense", "judge"].includes(speakerId)) return STAGE_POSITIONS[speakerId];
return STAGE_POSITIONS.witness; // W1, W2, W3, W5 all take the witness stand slot
}
Character component — idle vs. talking animation via simple texture-swap on a timer, not real lip-sync:

javascript
import { useEffect, useRef } from "react";
import { AnimatedSprite, Texture } from "pixi.js";

function useTalkingAnimation(sprite, isTalking) {
const frames = useRef([Texture.from("mouth_closed.png"), Texture.from("mouth_open.png")]);
useEffect(() => {
if (!sprite) return;
if (!isTalking) { sprite.texture = frames.current[0]; return; }
const interval = setInterval(() => {
sprite.texture = sprite.texture === frames.current[0] ? frames.current[1] : frames.current[0];
}, 150); // crude mouth-flap rate, tune by ear
return () => clearInterval(interval);
}, [sprite, isTalking]);
}
Playback hook — the core sequencer, driven entirely by the manifest and native <audio> events:

javascript
import { useState, useRef, useEffect } from "react";

export function useTrialPlayback(manifest) {
const [index, setIndex] = useState(0);
const [currentSubtitle, setCurrentSubtitle] = useState("");
const [isPlaying, setIsPlaying] = useState(false);
const audioRef = useRef(new Audio());

const currentTurn = manifest[index];

useEffect(() => {
if (!currentTurn) return;
const audio = audioRef.current;
audio.src = currentTurn.audio_url;

    const onTimeUpdate = () => {
      const chunk = currentTurn.subtitle_chunks.find(
        c => audio.currentTime >= c.start && audio.currentTime < c.end
      );
      if (chunk) setCurrentSubtitle(chunk.text);
    };
    const onEnded = () => {
      setIsPlaying(false);
      if (index < manifest.length - 1) setIndex(i => i + 1);
    };

    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("ended", onEnded);
    audio.play();
    setIsPlaying(true);

    return () => {
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("ended", onEnded);
    };

}, [index, currentTurn]);

return { currentTurn, currentSubtitle, isPlaying, index };
}
Scene banner for context — since scene shifts between opening/direct/cross/ruling, and your data shows rapid-fire rulings (indices 6-7, 14-16 are back-to-back sustained objections), a small banner reading "Objection — Ruling" during those turns helps the audience track what's happening without reading the judge's full reasoning as a wall of text.

Next.js integration note
PixiJS needs window/canvas, so wrap it as a client-only component:

javascript
import dynamic from "next/dynamic";
const CourtroomStage = dynamic(() => import("@/components/CourtroomStage"), { ssr: false });
One thing worth deciding now: your sample data has back-to-back ruling turns with no witness turn between them (indices 14, 15, 16 — three sustained objections in a row before the next real testimony). That's a real pattern from the objection loop we designed (attorney rephrases after "sustained," and can get objected-to again) — make sure your animation doesn't need a witness-stand occupant during pure judge-to-attorney exchanges, or the witness sprite will look like it's idling oddly through several turns.
