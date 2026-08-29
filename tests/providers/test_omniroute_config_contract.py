from pathlib import Path

import yaml

CFG = Path("/Users/callsamik/.hermes/profiles/omniroute/config.yaml")


def test_no_auto_slash_aliases_as_policy():
    data = yaml.safe_load(CFG.read_text())
    assert data["model"]["default"] == "auto"
    assert data["providers"]["omniroute"]["default_model"] == "auto"
    models = [e.get("model") for e in data.get("fallback_providers") or []]
    assert "auto/best-free" not in models
    assert all(not str(m).startswith("auto/") for m in models if m)
    assert data["delegation"]["model"] == "auto"
    assert data["auxiliary"]["compression"]["model"] == "auto"
    fb_providers = [e.get("provider") for e in data.get("fallback_providers") or []]
    assert "omniroute" not in fb_providers
    assert "ollama-launch" in fb_providers
