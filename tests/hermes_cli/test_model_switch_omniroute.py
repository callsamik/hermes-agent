"""OmniRoute routing_mode + profile parsing for /model switches."""

from hermes_cli.model_switch import ModelSwitchResult, parse_model_switch_args, switch_model


def test_switch_omniroute_auto_accepts_bare_auto_not_in_catalog(monkeypatch):
    """Bare ``auto`` is valid for OmniRoute auto routing but not in /v1/models."""

    def _reject_auto(*args, **kwargs):
        return {
            "accepted": False,
            "persist": False,
            "recognized": False,
            "message": "Model `auto` was not found in this provider's model listing.",
        }

    monkeypatch.setattr(
        "hermes_cli.models.validate_requested_model", _reject_auto
    )

    result = switch_model(
        raw_input="auto",
        current_provider="omniroute",
        current_model="openai/gpt-4o-mini",
        current_base_url="http://127.0.0.1:20128/v1",
        current_api_key="test-key",
        user_providers={
            "omniroute": {
                "base_url": "http://127.0.0.1:20128/v1",
                "default_model": "auto",
            }
        },
        omniroute_routing_mode="auto",
        omniroute_profile="cheap",
    )

    assert isinstance(result, ModelSwitchResult)
    assert result.success is True
    assert result.new_model == "auto"
    assert result.omniroute_routing_mode == "auto"
    assert result.omniroute_profile == "cheap"
    assert not result.warning_message


def test_parse_profile_and_routing_mode():
    req = parse_model_switch_args(
        "auto --provider omniroute --profile coding --routing-mode auto"
    )
    assert req.target == "auto"
    assert req.explicit_provider == "omniroute"
    assert req.omniroute_profile == "coding"
    assert req.omniroute_routing_mode == "auto"


def test_explicit_routing_clears_profile():
    req = parse_model_switch_args(
        "anthropic/claude-sonnet-4-20250514 --provider omniroute --routing-mode explicit"
    )
    assert req.omniroute_routing_mode == "explicit"
    assert req.omniroute_profile == ""
