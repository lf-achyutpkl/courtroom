from pathlib import Path

from dotenv import load_dotenv


def load_service_env() -> None:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
