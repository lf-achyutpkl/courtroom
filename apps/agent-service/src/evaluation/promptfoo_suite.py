from __future__ import annotations

import json
from pathlib import Path

REQUIRED_ADVERSARIAL_CATEGORIES = {
    "role_confusion",
    "contradiction_injection",
    "unsupported_legal_claim",
    "malformed_evidence_reference",
    "unsafe_content_prompt",
}

DEFAULT_PROMPTFOO_CONFIG = (
    Path(__file__).resolve().parents[2] / "evals" / "promptfoo" / "promptfooconfig.json"
)


def load_promptfoo_config(path: Path = DEFAULT_PROMPTFOO_CONFIG) -> dict:
    with path.open() as handle:
        return json.load(handle)


def promptfoo_categories(path: Path = DEFAULT_PROMPTFOO_CONFIG) -> set[str]:
    config = load_promptfoo_config(path)
    return {
        test.get("metadata", {}).get("category")
        for test in config.get("tests", [])
        if test.get("metadata", {}).get("category")
    }


def validate_promptfoo_categories(path: Path = DEFAULT_PROMPTFOO_CONFIG) -> None:
    categories = promptfoo_categories(path)
    missing = REQUIRED_ADVERSARIAL_CATEGORIES - categories
    if missing:
        raise ValueError(
            "Promptfoo suite missing adversarial categories: "
            + ", ".join(sorted(missing))
        )


def main() -> None:
    validate_promptfoo_categories()
    print("Promptfoo adversarial categories validated.")


if __name__ == "__main__":
    main()
