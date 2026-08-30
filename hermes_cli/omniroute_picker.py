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


def provider_has_model_groups(provider_row: dict) -> bool:
    groups = provider_row.get("model_groups")
    return isinstance(groups, list) and bool(groups)


def provider_inventory_model_count(provider_row: dict) -> int:
    if provider_has_model_groups(provider_row):
        total = 0
        for group in provider_row["model_groups"]:
            if isinstance(group, dict):
                total += len(group.get("entries") or [])
        return total
    models = provider_row.get("models") or []
    return int(provider_row.get("total_models") or len(models))


def resolve_model_picker_entry_by_label(
    entries: list, label: str
) -> dict | None:
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("label") or "") == label or str(entry.get("id") or "") == label:
            return entry
    return None


def omniroute_picker_switch_kwargs(group: dict, entry: dict) -> dict[str, str]:
    """Build ``switch_model`` kwargs for a grouped OmniRoute picker selection."""
    routing_mode = str(group.get("routing_mode") or "auto").strip().lower()
    if routing_mode == "explicit":
        wire = str(entry.get("wire_model") or entry.get("id") or "")
        return {
            "raw_input": wire,
            "omniroute_routing_mode": "explicit",
            "omniroute_profile": "",
        }
    profile = str(entry.get("profile") or entry.get("id") or "general")
    return {
        "raw_input": "auto",
        "omniroute_routing_mode": "auto",
        "omniroute_profile": profile,
    }
