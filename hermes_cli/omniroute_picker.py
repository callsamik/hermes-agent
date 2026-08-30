from __future__ import annotations

OMNIROUTE_PROFILES: tuple[tuple[str, str], ...] = (
    ("general", "General"),
    ("coding", "Coding"),
    ("hard_reasoning", "Hard reasoning"),
    ("review", "Review"),
    ("long_context", "Long context"),
    ("cheap", "Cheap"),
    ("vision", "Vision"),
    ("web", "Web"),
)

_INTERNAL_PREFIX = "auto/"


def is_omniroute_internal_alias(model_id: str) -> bool:
    mid = (model_id or "").strip()
    if not mid:
        return True
    lower = mid.lower()
    if lower == "auto":
        return True
    if lower.startswith(_INTERNAL_PREFIX):
        return True
    return False


def filter_explicit_omniroute_models(model_ids: list[str]) -> list[str]:
    return [m for m in model_ids if not is_omniroute_internal_alias(m)]


def build_omniroute_model_groups(model_ids: list[str]) -> list[dict[str, object]]:
    """Structured picker groups for OmniRoute: Auto profiles + explicit models."""
    auto_entries = [
        {
            "id": profile_id,
            "label": label,
            "profile": profile_id,
            "wire_model": "auto",
        }
        for profile_id, label in OMNIROUTE_PROFILES
    ]
    explicit = filter_explicit_omniroute_models(model_ids)
    model_entries = [
        {
            "id": mid,
            "label": mid,
            "wire_model": mid,
        }
        for mid in explicit
    ]
    return [
        {
            "id": "auto",
            "label": "Auto",
            "routing_mode": "auto",
            "entries": auto_entries,
        },
        {
            "id": "models",
            "label": "Models",
            "routing_mode": "explicit",
            "entries": model_entries,
        },
    ]


def apply_omniroute_to_model_cfg(
    model_cfg: dict,
    *,
    provider: str,
    routing_mode: str = "",
    profile: str = "",
) -> dict:
    """Persist OmniRoute routing mode + envelope on a model config dict.

    Explicit mode always clears any stale ``omniroute_envelope``. Non-OmniRoute
    providers drop omniroute keys entirely.
    """
    if not isinstance(model_cfg, dict):
        model_cfg = {}
    prov = (provider or "").strip().lower()
    if prov != "omniroute":
        model_cfg.pop("omniroute_routing_mode", None)
        model_cfg.pop("omniroute_envelope", None)
        return model_cfg

    mode = (routing_mode or "auto").strip().lower()
    model_cfg["omniroute_routing_mode"] = mode
    if mode == "explicit":
        model_cfg.pop("omniroute_envelope", None)
        return model_cfg

    prof = (profile or "general").strip() or "general"
    if prof not in {p for p, _ in OMNIROUTE_PROFILES}:
        prof = "general"
    model_cfg["omniroute_envelope"] = {"profile": prof}
    return model_cfg
