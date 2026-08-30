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
