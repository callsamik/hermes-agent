"""OmniRoute routing_mode + profile parsing for /model switches."""

from hermes_cli.model_switch import parse_model_switch_args


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
