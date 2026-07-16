from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from courtroom_domain import CaseFile


@dataclass(frozen=True)
class VoicePreset:
    voice: str
    speed: float
    style_preset: str


class VoiceCatalog:
    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or (
            Path(__file__).resolve().parent / "config" / "voice_presets.json"
        )
        with self.config_path.open() as config_file:
            loaded = json.load(config_file)
        if not isinstance(loaded, dict):
            raise RuntimeError("Voice preset config must be a JSON object.")
        self._config = cast(dict[str, object], loaded)

    def resolve(self, *, speaker_id: str, case_file: CaseFile) -> VoicePreset:
        speaker_presets = _mapping_from_object(self._config.get("speaker_presets", {}))
        class_presets = _mapping_from_object(
            self._config.get("speaker_class_presets", {})
        )

        if speaker_id in speaker_presets:
            return _voice_preset_from_object(speaker_presets[speaker_id])

        witness = next(
            (
                candidate
                for candidate in case_file.witnesses
                if candidate.witness_id == speaker_id
            ),
            None,
        )
        if witness is not None:
            witness_key = f"{witness.called_by}_witness"
            if witness_key in class_presets:
                return _voice_preset_from_object(class_presets[witness_key])
            if "witness_default" in class_presets:
                return _voice_preset_from_object(class_presets["witness_default"])

        if "default" in class_presets:
            return _voice_preset_from_object(class_presets["default"])

        raise RuntimeError(f"No voice preset configured for speaker '{speaker_id}'.")


def _voice_preset_from_dict(payload: dict[str, object]) -> VoicePreset:
    voice = str(payload.get("voice", "")).strip()
    if not voice:
        raise RuntimeError("Voice preset is missing a voice identifier.")

    return VoicePreset(
        voice=voice,
        speed=_float_from_object(payload.get("speed", 1.0)),
        style_preset=str(payload.get("stylePreset", "default")),
    )


def _voice_preset_from_object(payload: object) -> VoicePreset:
    return _voice_preset_from_dict(_mapping_from_object(payload))


def _mapping_from_object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    return cast(dict[str, object], value)


def _float_from_object(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(value)
    raise RuntimeError(
        f"Voice preset speed must be numeric, got {type(value).__name__}."
    )
