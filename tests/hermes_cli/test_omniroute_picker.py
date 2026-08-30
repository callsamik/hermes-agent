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


def test_provider_inventory_model_count_uses_groups():
    from hermes_cli.omniroute_picker import (
        provider_has_model_groups,
        provider_inventory_model_count,
    )

    row = {
        "slug": "omniroute",
        "models": [],
        "model_groups": [
            {"entries": [{"id": "general"}, {"id": "coding"}]},
            {"entries": [{"id": "anthropic/claude-sonnet-4-20250514"}]},
        ],
    }
    assert provider_has_model_groups(row) is True
    assert provider_inventory_model_count(row) == 3


def test_omniroute_picker_switch_kwargs_auto_and_explicit():
    from hermes_cli.omniroute_picker import omniroute_picker_switch_kwargs

    auto_group = {"routing_mode": "auto"}
    coding = {"id": "coding", "label": "Coding", "profile": "coding", "wire_model": "auto"}
    assert omniroute_picker_switch_kwargs(auto_group, coding) == {
        "raw_input": "auto",
        "omniroute_routing_mode": "auto",
        "omniroute_profile": "coding",
    }

    explicit_group = {"routing_mode": "explicit"}
    vendor = {
        "id": "anthropic/claude-sonnet-4-20250514",
        "label": "anthropic/claude-sonnet-4-20250514",
        "wire_model": "anthropic/claude-sonnet-4-20250514",
    }
    assert omniroute_picker_switch_kwargs(explicit_group, vendor) == {
        "raw_input": "anthropic/claude-sonnet-4-20250514",
        "omniroute_routing_mode": "explicit",
        "omniroute_profile": "",
    }


def test_picker_provider_rows_filter_omniroute_explicit(monkeypatch):
    from hermes_cli import model_switch
    from hermes_cli.omniroute_picker import provider_has_model_groups

    def _fake_list(**kwargs):
        return [
            {
                "slug": "omniroute",
                "name": "OmniRoute",
                "models": [
                    "auto/coding",
                    "auto/best-free",
                    "anthropic/claude-sonnet-4-20250514",
                ],
                "total_models": 3,
                "authenticated": True,
            }
        ]

    monkeypatch.setattr(model_switch, "list_authenticated_providers", _fake_list)
    monkeypatch.setattr(
        "hermes_cli.models.fetch_openrouter_models", lambda *a, **kw: []
    )

    rows = model_switch.list_picker_providers()
    omni = next(p for p in rows if p["slug"] == "omniroute")
    assert provider_has_model_groups(omni)
    models_group = next(g for g in omni["model_groups"] if g["id"] == "models")
    wire_models = [e["wire_model"] for e in models_group["entries"]]
    assert "auto/coding" not in wire_models
    assert "auto/best-free" not in wire_models
    assert wire_models == ["anthropic/claude-sonnet-4-20250514"]


def test_build_platform_omniroute_picker_entries_all_profiles():
    from hermes_cli.omniroute_picker import (
        OMNIROUTE_PROFILES,
        build_omniroute_model_groups,
        build_platform_omniroute_picker_entries,
        omniroute_picker_switch_kwargs,
    )

    groups = build_omniroute_model_groups(
        ["auto/coding", "anthropic/claude-sonnet-4-20250514"]
    )
    entries = build_platform_omniroute_picker_entries(groups)
    auto_entries = [e for e in entries if (e.get("_picker_group") or {}).get("id") == "auto"]
    assert len(auto_entries) == len(OMNIROUTE_PROFILES)
    assert auto_entries[0]["label"] == "Auto · General"
    assert auto_entries[1]["label"] == "Auto · Coding"
    switch_kw = omniroute_picker_switch_kwargs(
        auto_entries[1]["_picker_group"], auto_entries[1]
    )
    assert switch_kw == {
        "raw_input": "auto",
        "omniroute_routing_mode": "auto",
        "omniroute_profile": "coding",
    }
    assert entries[-1]["wire_model"] == "anthropic/claude-sonnet-4-20250514"
