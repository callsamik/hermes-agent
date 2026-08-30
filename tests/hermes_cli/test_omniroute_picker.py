from hermes_cli.omniroute_picker import (
    OMNIROUTE_PROFILES,
    filter_explicit_omniroute_models,
    is_omniroute_internal_alias,
)


def test_internal_aliases_rejected():
    blocked = [
        "auto",
        "auto/coding",
        "auto/cheap",
        "auto/best-chat",
        "auto/best-free",
        "auto/reasoning",
        "auto/claude-sonnet",
        "auto/fast",
        "auto/offline",
        "auto/smart",
    ]
    for mid in blocked:
        assert is_omniroute_internal_alias(mid) is True


def test_vendor_ids_allowed():
    allowed = [
        "anthropic/claude-sonnet-4-20250514",
        "openai/gpt-4o",
        "google/gemini-2.5-pro",
    ]
    for mid in allowed:
        assert is_omniroute_internal_alias(mid) is False


def test_filter_explicit_strips_aliases():
    raw = [
        "auto/best-chat",
        "anthropic/claude-sonnet-4-20250514",
        "auto/coding",
    ]
    assert filter_explicit_omniroute_models(raw) == [
        "anthropic/claude-sonnet-4-20250514"
    ]


def test_profile_catalog_has_eight_entries():
    assert len(OMNIROUTE_PROFILES) == 8
    assert OMNIROUTE_PROFILES[0][0] == "general"


def test_build_omniroute_model_groups_structure():
    from hermes_cli.omniroute_picker import build_omniroute_model_groups

    groups = build_omniroute_model_groups(
        ["auto/coding", "anthropic/claude-sonnet-4-20250514", "auto/best-free"]
    )
    assert groups[0]["id"] == "auto"
    assert len(groups[0]["entries"]) == 8
    assert groups[1]["id"] == "models"
    assert [e["wire_model"] for e in groups[1]["entries"]] == [
        "anthropic/claude-sonnet-4-20250514"
    ]
