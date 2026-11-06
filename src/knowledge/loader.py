import json
from pathlib import Path
from typing import Any

DEFAULT_PROFILE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "processed"
    / "community_profile.json"
)

def load_community_profile(
    profile_path: Path | None = None,
) -> dict[str, Any]:
    """Load the authoritative community profile from JSON."""

    path = profile_path or DEFAULT_PROFILE_PATH

    if not path.exists():
        raise FileNotFoundError(
            f"Community profile not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        profile = json.load(file)

    required_sections = [
        "community",
        "accommodation",
        "facilities",
        "services",
        "care_and_safety",
        "pricing",
        "appointments",
        "business_rules",
    ]

    missing_sections = [
        section
        for section in required_sections
        if section not in profile
    ]

    if missing_sections:
        raise ValueError(
            f"Community profile is missing sections: "
            f"{', '.join(missing_sections)}"
        )

    return profile
