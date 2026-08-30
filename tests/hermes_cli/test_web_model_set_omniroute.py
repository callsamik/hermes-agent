"""Tests for OmniRoute fields on POST /api/model/set and model config helpers."""

from unittest.mock import patch

from hermes_cli.omniroute_picker import apply_omniroute_to_model_cfg


def test_apply_omniroute_auto_persists_profile_envelope():
    cfg = {"provider": "omniroute", "default": "auto"}
    out = apply_omniroute_to_model_cfg(
        cfg,
        provider="omniroute",
        routing_mode="auto",
        profile="coding",
    )
    assert out["omniroute_routing_mode"] == "auto"
    assert out["omniroute_envelope"] == {"profile": "coding"}


def test_apply_omniroute_explicit_clears_stale_envelope():
    cfg = {
        "provider": "omniroute",
        "default": "anthropic/claude-sonnet-4-20250514",
        "omniroute_routing_mode": "auto",
        "omniroute_envelope": {"profile": "coding", "constraints": {"max_cost": 1}},
    }
    out = apply_omniroute_to_model_cfg(
        cfg,
        provider="omniroute",
        routing_mode="explicit",
        profile="",
    )
    assert out["omniroute_routing_mode"] == "explicit"
    assert "omniroute_envelope" not in out


def test_apply_omniroute_non_provider_clears_keys():
    cfg = {
        "provider": "groq",
        "default": "llama",
        "omniroute_routing_mode": "auto",
        "omniroute_envelope": {"profile": "general"},
    }
    out = apply_omniroute_to_model_cfg(cfg, provider="groq")
    assert "omniroute_routing_mode" not in out
    assert "omniroute_envelope" not in out


def test_model_assignment_accepts_omniroute_fields():
    from hermes_cli.web_models import ModelAssignment

    body = ModelAssignment(
        scope="main",
        provider="omniroute",
        model="auto",
        omniroute_profile="coding",
        omniroute_routing_mode="auto",
    )
    assert body.omniroute_profile == "coding"
    assert body.omniroute_routing_mode == "auto"


def test_apply_model_assignment_sync_persists_omniroute_auto():
    from hermes_cli.web_server import _apply_model_assignment_sync

    saved: dict = {}

    def _fake_save(cfg):
        saved["cfg"] = cfg

    cfg = {
        "model": {"provider": "omniroute", "default": "auto"},
        "providers": {"omniroute": {"default_model": "auto"}},
    }

    with patch("hermes_cli.web_server.load_config", return_value=cfg), patch(
        "hermes_cli.web_server.save_config", side_effect=_fake_save
    ):
        result = _apply_model_assignment_sync(
            "main",
            "omniroute",
            "auto",
            "",
            "",
            "",
            omniroute_profile="coding",
            omniroute_routing_mode="auto",
        )

    model_cfg = saved["cfg"]["model"]
    assert model_cfg["default"] == "auto"
    assert model_cfg["omniroute_routing_mode"] == "auto"
    assert model_cfg["omniroute_envelope"] == {"profile": "coding"}
    assert result["ok"] is True


def test_apply_model_assignment_sync_explicit_clears_envelope():
    from hermes_cli.web_server import _apply_model_assignment_sync

    saved: dict = {}

    def _fake_save(cfg):
        saved["cfg"] = cfg

    cfg = {
        "model": {
            "provider": "omniroute",
            "default": "auto",
            "omniroute_routing_mode": "auto",
            "omniroute_envelope": {"profile": "coding"},
        },
        "providers": {"omniroute": {"default_model": "auto"}},
    }

    with patch("hermes_cli.web_server.load_config", return_value=cfg), patch(
        "hermes_cli.web_server.save_config", side_effect=_fake_save
    ):
        _apply_model_assignment_sync(
            "main",
            "omniroute",
            "anthropic/claude-sonnet-4-20250514",
            "",
            "",
            "",
            omniroute_profile="",
            omniroute_routing_mode="explicit",
        )

    model_cfg = saved["cfg"]["model"]
    assert model_cfg["default"] == "anthropic/claude-sonnet-4-20250514"
    assert model_cfg["omniroute_routing_mode"] == "explicit"
    assert "omniroute_envelope" not in model_cfg
