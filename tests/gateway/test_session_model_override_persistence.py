"""Per-session /model overrides must survive gateway restarts (#3659 salvage).

``GatewayRunner._session_model_overrides`` is in-memory, so before persistence
a gateway restart silently reverted every session to the global default model.
The non-secret parts (model/provider/base_url) are now written through to the
session store (``SessionEntry.model_override`` in sessions.json) and lazily
rehydrated on first use after a restart, with credentials re-resolved through
the normal runtime provider resolution.

Covers:
  - the override survives a simulated restart (a second SessionStore instance
    reading the same sessions dir, and a fresh runner rehydrating from it)
  - /new (SessionStore.reset_session) clears the persisted override so a
    restart cannot resurrect it
  - api_key is NEVER serialized to sessions.json
"""
import json
from unittest.mock import patch

import pytest

from gateway.config import GatewayConfig, Platform
from gateway.session import (
    SessionEntry,
    SessionSource,
    SessionStore,
    sanitize_model_override,
)

OVERRIDE = {
    "model": "gpt-5o",
    "provider": "openai",
    "api_key": "sk-SUPER-SECRET-do-not-persist",
    "base_url": "https://api.openai.example/v1",
    "api_mode": "responses",
}


def _make_source() -> SessionSource:
    return SessionSource(
        platform=Platform.TELEGRAM,
        user_id="u1",
        chat_id="c1",
        user_name="tester",
        chat_type="dm",
    )


@pytest.fixture
def store_factory(tmp_path, monkeypatch):
    """Build SessionStores over a shared sessions dir, without SQLite."""

    def _raise():
        raise RuntimeError("SQLite disabled in test")

    import hermes_state

    monkeypatch.setattr(hermes_state, "SessionDB", _raise)

    def _make() -> SessionStore:
        store = SessionStore(sessions_dir=tmp_path, config=GatewayConfig())
        assert store._db is None
        return store

    return _make


def _sessions_json(tmp_path) -> str:
    return (tmp_path / "sessions.json").read_text(encoding="utf-8")


def test_override_persists_and_survives_restart(store_factory, tmp_path):
    store = store_factory()
    entry = store.get_or_create_session(_make_source())
    session_key = entry.session_key

    store.set_model_override(session_key, OVERRIDE)

    # Simulated restart: a brand-new store instance reads the same dir.
    store2 = store_factory()
    persisted = store2.get_model_override(session_key)
    assert persisted == {
        "model": "gpt-5o",
        "provider": "openai",
        "base_url": "https://api.openai.example/v1",
    }


def _make_runner(store):
    from gateway.run import GatewayRunner

    runner = object.__new__(GatewayRunner)
    runner._session_model_overrides = {}
    runner.session_store = store
    return runner


def test_runner_rehydrates_override_after_restart(store_factory):
    store = store_factory()
    entry = store.get_or_create_session(_make_source())
    session_key = entry.session_key
    store.set_model_override(session_key, OVERRIDE)

    # Simulated restart: fresh store + fresh runner with an empty in-memory
    # override map, credentials re-resolved via runtime provider resolution.
    runner = _make_runner(store_factory())
    with patch(
        "gateway.run._resolve_runtime_agent_kwargs_for_provider",
        return_value={
            "api_key": "sk-fresh-from-keychain",
            "api_mode": "responses",
            "base_url": "https://api.openai.example/v1",
            "provider": "openai",
        },
    ):
        runner._rehydrate_session_model_override(session_key)

    override = runner._session_model_overrides[session_key]
    assert override["model"] == "gpt-5o"
    assert override["provider"] == "openai"
    assert override["base_url"] == "https://api.openai.example/v1"
    # Credentials come from live resolution, never from disk.
    assert override["api_key"] == "sk-fresh-from-keychain"
    assert override["api_mode"] == "responses"


def test_sanitize_model_override():
    assert sanitize_model_override(None) is None
    assert sanitize_model_override({}) is None
    assert sanitize_model_override({"api_key": "sk-x", "api_mode": "chat"}) is None
    assert sanitize_model_override(OVERRIDE) == {
        "model": "gpt-5o",
        "provider": "openai",
        "base_url": "https://api.openai.example/v1",
    }


def test_sanitize_keeps_omniroute_auto_profile():
    cleaned = sanitize_model_override(
        {
            "model": "auto",
            "provider": "omniroute",
            "base_url": "http://127.0.0.1:20128/v1",
            "api_key": "secret",
            "omniroute_routing_mode": "auto",
            "omniroute_envelope": {"profile": "coding", "constraints": {"x": 1}},
        }
    )
    assert cleaned == {
        "model": "auto",
        "provider": "omniroute",
        "base_url": "http://127.0.0.1:20128/v1",
        "omniroute_routing_mode": "auto",
        "omniroute_envelope": {"profile": "coding"},
    }


def test_sanitize_keeps_omniroute_explicit_mode():
    cleaned = sanitize_model_override(
        {
            "model": "gemini/gemini-2.5-flash-lite",
            "provider": "omniroute",
            "omniroute_routing_mode": "explicit",
            "omniroute_envelope": {"profile": "coding"},
        }
    )
    assert cleaned["omniroute_routing_mode"] == "explicit"
    assert "omniroute_envelope" not in cleaned


def test_omniroute_override_persists_and_rehydrates(store_factory):
    store = store_factory()
    entry = store.get_or_create_session(_make_source())
    session_key = entry.session_key
    store.set_model_override(
        session_key,
        {
            "model": "auto",
            "provider": "omniroute",
            "base_url": "http://127.0.0.1:20128/v1",
            "api_key": "sk-secret",
            "omniroute_routing_mode": "auto",
            "omniroute_envelope": {"profile": "cheap"},
        },
    )
    store2 = store_factory()
    persisted = store2.get_model_override(session_key)
    assert persisted["omniroute_routing_mode"] == "auto"
    assert persisted["omniroute_envelope"] == {"profile": "cheap"}
    assert "api_key" not in persisted

    runner = _make_runner(store_factory())
    with patch(
        "gateway.run._resolve_runtime_agent_kwargs_for_provider",
        return_value={
            "api_key": "sk-fresh",
            "api_mode": "chat_completions",
            "base_url": "http://127.0.0.1:20128/v1",
            "provider": "omniroute",
        },
    ):
        runner._rehydrate_session_model_override(session_key)
    override = runner._session_model_overrides[session_key]
    assert override["omniroute_routing_mode"] == "auto"
    assert override["omniroute_envelope"] == {"profile": "cheap"}


def test_apply_omniroute_from_session_override_sets_envelope():
    from gateway.run import GatewayRunner

    runner = object.__new__(GatewayRunner)
    runner._session_model_overrides = {
        "s1": {
            "model": "auto",
            "provider": "omniroute",
            "omniroute_routing_mode": "auto",
            "omniroute_envelope": {"profile": "coding"},
        }
    }

    class _Agent:
        provider = "omniroute"
        model = "auto"
        omniroute_routing_mode = ""
        omniroute_envelope = None

    agent = _Agent()
    runner._apply_omniroute_from_session_override("s1", agent)
    assert agent.omniroute_routing_mode == "auto"
    assert agent.omniroute_envelope == {"profile": "coding"}


def test_apply_omniroute_infers_explicit_from_model_id():
    from gateway.run import GatewayRunner

    runner = object.__new__(GatewayRunner)
    runner._session_model_overrides = {
        "s1": {
            "model": "gemini/gemini-2.5-flash-lite",
            "provider": "omniroute",
        }
    }

    class _Agent:
        provider = "omniroute"
        model = "gemini/gemini-2.5-flash-lite"
        omniroute_routing_mode = ""
        omniroute_envelope = {"profile": "stale"}

    agent = _Agent()
    runner._apply_omniroute_from_session_override("s1", agent)
    assert agent.omniroute_routing_mode == "explicit"
    assert agent.omniroute_envelope is None
