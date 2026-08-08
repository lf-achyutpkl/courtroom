from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set in the environment or .env")
    return database_url


def get_redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


def get_tts_provider_name() -> str:
    return os.getenv("TTS_PROVIDER", "kokoro")


def get_r2_endpoint_url() -> str:
    value = os.getenv("R2_ENDPOINT_URL")
    if not value:
        raise RuntimeError("R2_ENDPOINT_URL must be set for simulation audio uploads.")
    return value


def get_r2_bucket_name() -> str:
    value = os.getenv("R2_BUCKET_NAME")
    if not value:
        raise RuntimeError("R2_BUCKET_NAME must be set for simulation audio uploads.")
    return value


def get_r2_access_key_id() -> str:
    value = os.getenv("R2_ACCESS_KEY_ID")
    if not value:
        raise RuntimeError("R2_ACCESS_KEY_ID must be set for simulation audio uploads.")
    return value


def get_r2_secret_access_key() -> str:
    value = os.getenv("R2_SECRET_ACCESS_KEY")
    if not value:
        raise RuntimeError(
            "R2_SECRET_ACCESS_KEY must be set for simulation audio uploads."
        )
    return value


def get_r2_public_base_url() -> str:
    value = os.getenv("R2_PUBLIC_BASE_URL")
    if not value:
        raise RuntimeError(
            "R2_PUBLIC_BASE_URL must be set for simulation audio uploads."
        )
    return value.rstrip("/")


def get_r2_region() -> str:
    return os.getenv("R2_REGION", "auto")


def get_interactive_recording_mime_types() -> set[str]:
    values = os.getenv(
        "INTERACTIVE_RECORDING_MIME_TYPES", "audio/webm,audio/mp4,audio/ogg"
    )
    mime_types = {value.strip().lower() for value in values.split(",") if value.strip()}
    if not mime_types or not all(value.startswith("audio/") for value in mime_types):
        raise RuntimeError(
            "INTERACTIVE_RECORDING_MIME_TYPES must contain audio MIME types"
        )
    return mime_types


def get_interactive_recording_max_bytes() -> int:
    value = int(os.getenv("INTERACTIVE_RECORDING_MAX_BYTES", "10485760"))
    if value <= 0:
        raise RuntimeError("INTERACTIVE_RECORDING_MAX_BYTES must be positive")
    return value


def get_interactive_upload_expiry_seconds() -> int:
    value = int(os.getenv("INTERACTIVE_UPLOAD_EXPIRY_SECONDS", "300"))
    if not 1 <= value <= 3600:
        raise RuntimeError(
            "INTERACTIVE_UPLOAD_EXPIRY_SECONDS must be between 1 and 3600"
        )
    return value
