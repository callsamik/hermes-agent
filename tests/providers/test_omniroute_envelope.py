"""Contract tests for the OmniRoute provider workload envelope."""

from providers import get_provider_profile


def _profile():
    profile = get_provider_profile("omniroute")
    assert profile is not None
    return profile


def test_omniroute_extra_body_defaults_to_general():
    assert _profile().build_extra_body() == {
        "omniroute": {"profile": "general"}
    }


def test_omniroute_extra_body_keeps_catalog_profile_only():
    body = _profile().build_extra_body(
        omniroute_envelope={
            "profile": "coding",
            "constraints": {"requires_vision": True},
            "objective": "Implement the requested change",
            "model": "auto/best-chat",
            "fallback_chain": ["anthropic/claude-sonnet"],
            "X-OmniRoute-Mode": "coding",
        }
    )

    assert body == {
        "omniroute": {
            "profile": "coding",
            "constraints": {"requires_vision": True},
            "objective": "Implement the requested change",
        }
    }
    assert "auto/" not in str(body)


def test_omniroute_unknown_profile_coerces_to_general():
    body = _profile().build_extra_body(
        omniroute_envelope={"profile": "not-in-the-catalog"}
    )

    assert body == {"omniroute": {"profile": "general"}}


def test_coerce_omniroute_model_always_returns_auto():
    profile = _profile()

    for model in (None, "", "auto", "auto/best-chat", "claude-sonnet"):
        assert profile.coerce_omniroute_model(model) == "auto"


def test_chat_completions_coerces_omniroute_model_to_auto():
    from agent.transports import get_transport

    profile = _profile()
    transport = get_transport("chat_completions")
    kwargs = transport.build_kwargs(
        model="auto/best-chat",
        messages=[{"role": "user", "content": "Hello"}],
        tools=[],
        provider_profile=profile,
        provider_name="omniroute",
        omniroute_envelope={"profile": "general"},
    )

    assert kwargs["model"] == "auto"
    assert kwargs["extra_body"] == {
        "omniroute": {"profile": "general"}
    }
