"""OmniRoute provider profile."""

from __future__ import annotations

from typing import Any

from providers import register_provider
from providers.base import ProviderProfile

_CATALOG = frozenset(
    {
        "general",
        "coding",
        "hard_reasoning",
        "review",
        "long_context",
        "cheap",
        "vision",
        "web",
    }
)


class OmniRouteProfile(ProviderProfile):
    """OmniRoute gateway — workload envelopes, never routed model IDs."""

    def coerce_omniroute_model(self, model: str | None) -> str:
        return "auto"

    def coerce_model_id(self, model: str | None) -> str:
        return self.coerce_omniroute_model(model)

    def build_extra_body(
        self, *, session_id: str | None = None, **context: Any
    ) -> dict[str, Any]:
        raw = context.get("omniroute_envelope")
        if not isinstance(raw, dict):
            raw = {"profile": "general"}

        profile = raw.get("profile") or "general"
        if profile not in _CATALOG:
            profile = "general"

        envelope: dict[str, Any] = {"profile": profile}
        if "constraints" in raw:
            envelope["constraints"] = raw["constraints"]
        if "objective" in raw:
            envelope["objective"] = raw["objective"]
        return {"omniroute": envelope}


omniroute = OmniRouteProfile(
    name="omniroute",
    aliases=("omni-route",),
    display_name="OmniRoute",
    description="Local OmniRoute gateway — workload envelope, not model IDs",
    env_vars=("OMNIROUTE_API_KEY",),
    base_url="http://127.0.0.1:20128/v1",
)

register_provider(omniroute)
