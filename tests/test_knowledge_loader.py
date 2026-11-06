import json

import pytest

from src.knowledge.loader import load_community_profile

def test_loads_default_community_profile():
    profile = load_community_profile()

    assert profile["community"]["name"] == "WillowBrook Senior Living"
    assert "facilities" in profile
    assert "services" in profile

def test_loads_custom_profile_path(tmp_path):
    profile_data = {
        "community": {"name": "Test Community"},
        "accommodation": {},
        "facilities": [],
        "services": [],
        "care_and_safety": {},
        "pricing": {},
        "appointments": {},
        "business_rules": {},
    }

    profile_path = tmp_path / "profile.json"
    profile_path.write_text(
        json.dumps(profile_data),
        encoding="utf-8",
    )

    result = load_community_profile(profile_path)

    assert result["community"]["name"] == "Test Community"

def test_missing_profile_raises_file_not_found(tmp_path):
    missing_path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        load_community_profile(missing_path)

def test_missing_required_section_raises_value_error(tmp_path):
    profile_path = tmp_path / "incomplete.json"
    profile_path.write_text(
        json.dumps({"community": {}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing sections"):
        load_community_profile(profile_path)