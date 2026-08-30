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


def test_coerce_auto_mode_returns_auto():
    profile = _profile()

    for model in (None, "", "auto", "auto/best-chat", "claude-sonnet"):
        assert profile.coerce_model_id(model, routing_mode="auto") == "auto"


def test_coerce_explicit_mode_preserves_model_id():
    profile = _profile()
    explicit = "anthropic/claude-sonnet-4-20250514"
    assert profile.coerce_model_id(explicit, routing_mode="explicit") == explicit


def test_build_extra_body_explicit_mode_empty():
    assert _profile().build_extra_body(
        omniroute_routing_mode="explicit",
        omniroute_envelope={"profile": "coding"},
    ) == {}


def test_build_extra_body_auto_mode_keeps_envelope():
    body = _profile().build_extra_body(
        omniroute_routing_mode="auto",
        omniroute_envelope={"profile": "coding"},
    )
    assert body == {"omniroute": {"profile": "coding"}}


def test_explicit_mode_ignores_stale_envelope_in_context():
    """Explicit wire must never attach a leftover auto envelope."""
    body = _profile().build_extra_body(
        omniroute_routing_mode="explicit",
        omniroute_envelope={
            "profile": "coding",
            "constraints": {"max_cost": 0.5},
        },
    )
    assert body == {}
    assert "omniroute" not in body


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


def test_chat_completions_explicit_mode_no_envelope():
    from agent.transports import get_transport

    profile = _profile()
    transport = get_transport("chat_completions")
    explicit = "anthropic/claude-sonnet-4-20250514"
    kwargs = transport.build_kwargs(
        model=explicit,
        messages=[{"role": "user", "content": "Hi"}],
        tools=[],
        provider_profile=profile,
        provider_name="omniroute",
        omniroute_routing_mode="explicit",
        omniroute_envelope={"profile": "coding"},
    )
    assert kwargs["model"] == explicit
    assert "omniroute" not in (kwargs.get("extra_body") or {})
