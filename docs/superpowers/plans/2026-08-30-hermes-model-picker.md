# Hermes Model Picker (OmniRoute Auto + Explicit) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose OmniRoute **Auto** (eight workload profiles → `model: auto` + envelope) and **Models** (explicit catalog IDs, no envelope) in all Hermes pickers via one shared inventory extension, without modifying the OmniRouter v0 contract.

**Architecture:** Extend `hermes_cli/inventory.py` once to emit structured `model_groups` for the `omniroute` provider; add a shared alias filter for explicit lists; split OmniRoute provider coercion so envelope attaches only in auto mode; thread `routing_mode` + `profile` through `ModelSwitchRequest` → session `model_config` → `omniroute_envelope` in chat transport; render a three-stage tree in TUI/web (provider → group → entry). Telegram/Discord v1: Auto defaults to `general`; explicit list uses the same filter. **Out of scope:** ACP envelope channel, cron pinning changes, OmniRoute server edits.

**Tech stack:** Python 3.11+, Hermes agent (`hermes_cli`, `plugins/model-providers`, `tui_gateway`, `gateway`), React Ink TUI (`ui-tui`), web dashboard (`web/src`), existing `scripts/run_tests.sh` / pytest.

**Design spec (locked):** HermesVault `docs/superpowers/specs/2026-08-30-hermes-model-picker-design.md` (Option B). **OmniRouter contract:** HermesVault `docs/superpowers/specs/2026-08-30-omnirouter-policy-contract-design.md` — **consume only; do not edit.**

## Global Constraints

- **Auto mode:** wire `model: "auto"` + `omniroute: { profile }` (eight profiles only: `general`, `coding`, `hard_reasoning`, `review`, `long_context`, `cheap`, `vision`, `web`).
- **Explicit mode:** wire catalog `model` id; **no** `omniroute` body key.
- **Explicit Models list:** from OmniRoute `/v1/models` (or cached inventory), **excluding** bare `auto`, all `auto/*`, and internal routing aliases (`auto/best-chat`, `auto/best-free`, `auto/coding`, brand `auto/claude-*`, etc.).
- **Never** expose `auto/*` aliases in Hermes UI as selectable policy (internal OmniRoute vocabulary only).
- **No ACP** changes in v1.
- **No cron** scope expansion (pinned jobs unchanged; drift guard unchanged).
- **No OmniRoute repo changes** in this plan.
- TDD: failing test → implement → green per task; commit per task.
- Non-OmniRoute providers: picker behavior unchanged (flat `models[]`).

---

## File map (created / modified)

| File | Responsibility |
| --- | --- |
| **Create** `hermes_cli/omniroute_picker.py` | Alias filter, profile catalog labels, inventory row shaping for `omniroute` |
| **Create** `tests/hermes_cli/test_omniroute_picker.py` | Filter + group payload unit tests |
| **Modify** `plugins/model-providers/omniroute/__init__.py` | `fallback_models`, mode-aware coerce + `build_extra_body` |
| **Modify** `tests/providers/test_omniroute_envelope.py` | Split auto vs explicit wire tests |
| **Modify** `hermes_cli/inventory.py` | Call omniroute grouper in `build_models_payload` |
| **Modify** `hermes_cli/model_switch.py` | `ModelSwitchRequest.profile`, `routing_mode`; apply switch |
| **Create** `tests/hermes_cli/test_model_switch_omniroute.py` | Parse + persist auto/explicit |
| **Modify** `tui_gateway/server.py` | `_apply_model_switch`, `_runtime_model_config`, `config.set model` |
| **Modify** `run_agent.py` | Read `model_config.omniroute_envelope` / routing_mode into transport |
| **Modify** `agent/transports/chat_completions.py` | Pass envelope only when `routing_mode=="auto"` |
| **Modify** `ui-tui/src/gatewayTypes.ts` | Types for `model_groups`, entries |
| **Modify** `ui-tui/src/components/modelPicker.tsx` | Stage `group` for omniroute |
| **Modify** `web/src/components/ModelPickerDialog.tsx` | Same tree |
| **Modify** `web/src/pages/ModelsPage.tsx` | Display chip `Auto · Profile` |
| **Modify** `gateway/slash_commands.py` | Parse `--profile` on `/model` (Telegram/Discord path) |
| **Modify** `plugins/platforms/telegram/adapter.py` | Omniroute picker: Auto → general default |
| **Modify** `plugins/platforms/discord/adapter.py` | Same as Telegram |
| **Modify** `cli.py` | Legacy prompt_toolkit picker: omniroute groups |

---

## Acceptance tests (plan-level)

**Status: PASS (2026-08-30)** — branch `omniroute-model-picker` @ `39a4b395e9`

Run after all tasks:

```bash
cd ~/.hermes/hermes-agent
HERMES_TEST_FILE_RETRIES=0 ./scripts/run_tests.sh \
  tests/hermes_cli/test_omniroute_picker.py \
  tests/hermes_cli/test_model_switch_omniroute.py \
  tests/providers/test_omniroute_envelope.py \
  tests/providers/test_omniroute_config_contract.py -q
```

**Result:** 22/22 passed (plan command). Extended suite **32/32** (+ `test_web_model_set_omniroute`, `test_list_picker_providers`). TUI vitest **4/4** (`modelPicker.omniroute.test.ts`). Web vitest **4/4** (`omnirouteModelPicker.test.ts`).

Manual (documented below — automated contract tests cover wire invariants; live UI smoke optional on stock `:20128`):

- [x] **1. TUI** Ctrl+O → OmniRoute → Auto → Coding → status `OmniRoute · Auto · Coding`; wire `model=auto` + envelope — **PASS (contract):** `ui-tui` omniroute picker tests + `test_omniroute_envelope` auto path. Live TUI smoke not re-run this session.
- [x] **2. TUI explicit** OmniRoute → Models → vendor id → explicit id, no `omniroute` key — **PASS (contract):** `test_build_extra_body_explicit_mode_empty`, TUI picker tests.
- [x] **3. Web Models page** same tree — **PASS (contract):** `test_web_model_set_omniroute` (6), web `omnirouteModelPicker.test.ts` (4).
- [x] **4. Telegram `/model`** OmniRoute Auto → `general`; explicit list has no `auto/coding` — **PASS (contract):** `test_picker_provider_rows_filter_omniroute_explicit`, `build_platform_omniroute_picker_entries_v1`.
- [x] **5. Auto ↔ Explicit mid-session** chip/override updates — **PASS (contract):** `test_model_switch_omniroute`, `test_web_model_set_omniroute`, gateway session override wiring (Task 9).
- [x] **6. Flat providers unchanged** Groq/Ollama/etc. — **PASS:** `test_list_picker_providers` passthrough; no `model_groups` on non-OmniRoute rows.

**Representative skill smoke (not in scope for full matrix):** After routing contract passes, run **one** cron-adjacent path (e.g. `hermes-vault` recall or 8am script dry-run) and **one** interactive tool skill (e.g. `plan` or `email-inbox-triage` read-only) — confirm tools execute and outputs arrive. Do **not** test every OOTB skill against every profile; skills do not own model selection.

- [x] **Vault recall:** `vault_manager.py recall "Shared Project Board"` → exit 0, 19 wiki files / 34 matching lines.
- [x] **Interactive tool skill:** `hermes skills list` → `email-inbox-triage` + `plan` enabled (builtin); `email-inbox-triage` SKILL.md load smoke PASS. Skills subsystem operational; no skill×profile matrix.

**Envelope invariant (verified):**

| Mode | model | routing_mode | profile | envelope |
| --- | --- | --- | --- | --- |
| Auto | `auto` | `auto` | `general` (platform) / user-selected (TUI/web) | `{profile}` |
| Explicit | catalog id | `explicit` | `""` | none |

**Upstream / branch hygiene (operational):** Hermes changes on integration branch; merge Nous with contract tests. OmniRoute policy branch separate lifecycle; prod cutover explicit. See HermesVault `.superpowers/sdd/progress.md` § Operational policy.

---

### Task 1: OmniRoute internal-alias filter

**Files:**
- Create: `hermes_cli/omniroute_picker.py`
- Test: `tests/hermes_cli/test_omniroute_picker.py`

**Interfaces:**
- Produces:
  - `OMNIROUTE_PROFILES: tuple[tuple[str, str], ...]` — `(wire_id, label)` for eight profiles
  - `is_omniroute_internal_alias(model_id: str) -> bool`
  - `filter_explicit_omniroute_models(model_ids: list[str]) -> list[str]`

- [ ] **Step 1: Write the failing tests**

```python
# tests/hermes_cli/test_omniroute_picker.py
from hermes_cli.omniroute_picker import (
    OMNIROUTE_PROFILES,
    filter_explicit_omniroute_models,
    is_omniroute_internal_alias,
)


def test_internal_aliases_rejected():
    blocked = [
        "auto",
        "auto/coding",
        "auto/cheap",
        "auto/best-chat",
        "auto/best-free",
        "auto/reasoning",
        "auto/claude-sonnet",
        "auto/fast",
        "auto/offline",
        "auto/smart",
    ]
    for mid in blocked:
        assert is_omniroute_internal_alias(mid) is True


def test_vendor_ids_allowed():
    allowed = [
        "anthropic/claude-sonnet-4-20250514",
        "openai/gpt-4o",
        "google/gemini-2.5-pro",
    ]
    for mid in allowed:
        assert is_omniroute_internal_alias(mid) is False


def test_filter_explicit_strips_aliases():
    raw = [
        "auto/best-chat",
        "anthropic/claude-sonnet-4-20250514",
        "auto/coding",
    ]
    assert filter_explicit_omniroute_models(raw) == [
        "anthropic/claude-sonnet-4-20250514"
    ]


def test_profile_catalog_has_eight_entries():
    assert len(OMNIROUTE_PROFILES) == 8
    assert OMNIROUTE_PROFILES[0][0] == "general"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd ~/.hermes/hermes-agent
./venv/bin/python -m pytest tests/hermes_cli/test_omniroute_picker.py -v
```

Expected: FAIL — `ModuleNotFoundError: hermes_cli.omniroute_picker`

- [ ] **Step 3: Minimal implementation**

```python
# hermes_cli/omniroute_picker.py
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
```

- [ ] **Step 4: Run tests — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add hermes_cli/omniroute_picker.py tests/hermes_cli/test_omniroute_picker.py
git commit -m "feat: add OmniRoute picker alias filter and profile catalog"
```

---

### Task 2: Mode-aware OmniRoute provider (envelope only for auto)

**Files:**
- Modify: `plugins/model-providers/omniroute/__init__.py`
- Modify: `tests/providers/test_omniroute_envelope.py`

**Interfaces:**
- Consumes: `omniroute_routing_mode: str | None` in `build_extra_body(**context)` — `"auto"` | `"explicit"`
- Produces:
  - `coerce_model_id(model, *, routing_mode="auto")` → `"auto"` if auto else unchanged explicit id
  - `build_extra_body(..., omniroute_routing_mode="explicit")` → `{}`
  - `fallback_models=("auto",)` on registered profile

- [ ] **Step 1: Update tests (RED)**

Replace `test_coerce_omniroute_model_always_returns_auto` with:

```python
def test_coerce_explicit_mode_preserves_model_id():
    profile = _profile()
    assert profile.coerce_model_id(
        "anthropic/claude-sonnet-4-20250514",
        routing_mode="explicit",
    ) == "anthropic/claude-sonnet-4-20250514"


def test_coerce_auto_mode_returns_auto():
    profile = _profile()
    assert profile.coerce_model_id("anything", routing_mode="auto") == "auto"


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
```

Add signature support on `ProviderProfile.coerce_model_id` base default (`routing_mode` kw-only, default `"auto"` for backward compat on non-omniroute profiles — ignore extra kw).

- [ ] **Step 2: Run tests — expect FAIL**

- [ ] **Step 3: Implement**

In `omniroute/__init__.py`:

```python
def coerce_model_id(self, model: str | None, *, routing_mode: str = "auto") -> str:
    if routing_mode == "explicit" and model:
        return str(model)
    return "auto"

def build_extra_body(self, *, session_id: str | None = None, **context: Any) -> dict[str, Any]:
    if context.get("omniroute_routing_mode") == "explicit":
        return {}
    # ... existing envelope logic unchanged ...
```

Register with `fallback_models=("auto",)`.

Export `OMNIROUTE_PROFILES` re-export from plugin or import from `hermes_cli.omniroute_picker` in inventory (prefer import from hermes_cli to avoid circular imports).

- [ ] **Step 4: Run envelope + provider profile tests — PASS**

- [ ] **Step 5: Commit**

---

### Task 3: Shared inventory — `model_groups` for OmniRoute

**Files:**
- Modify: `hermes_cli/inventory.py`
- Modify: `hermes_cli/omniroute_picker.py` (add `build_omniroute_model_groups`)
- Test: extend `tests/hermes_cli/test_omniroute_picker.py`

**Interfaces:**
- Produces on omniroute provider row:

```python
{
  "slug": "omniroute",
  "models": [],  # legacy flat list empty or omitted for omniroute
  "model_groups": [
    {
      "id": "auto",
      "label": "Auto",
      "routing_mode": "auto",
      "entries": [
        {"id": "general", "label": "General", "profile": "general", "wire_model": "auto"},
        # ... eight profiles
      ],
    },
    {
      "id": "models",
      "label": "Models",
      "routing_mode": "explicit",
      "entries": [
        {"id": "anthropic/claude-...", "label": "anthropic/claude-...", "wire_model": "anthropic/claude-..."},
      ],
    },
  ],
}
```

- [ ] **Step 1: Failing test**

```python
def test_build_omniroute_model_groups_structure():
    from hermes_cli.omniroute_picker import build_omniroute_model_groups

    groups = build_omniroute_model_groups(
        ["auto/coding", "anthropic/claude-sonnet-4-20250514", "auto/best-free"]
    )
    assert groups[0]["id"] == "auto"
    assert len(groups[0]["entries"]) == 8
    assert groups[1]["id"] == "models"
    assert [e["wire_model"] for e in groups[1]["entries"]] == [
        "anthropic/claude-sonnet-4-20250514"
    ]
```

- [ ] **Step 2: RED run**

- [ ] **Step 3: Implement `build_omniroute_model_groups` + hook in `build_models_payload`**

After `_apply_custom_aliases(rows)`, for row where `slug == "omniroute"`:

```python
from hermes_cli.omniroute_picker import build_omniroute_model_groups

raw_models = row.get("models") or []
groups = build_omniroute_model_groups(raw_models)
row["model_groups"] = groups
row["models"] = []  # force UI to use groups for omniroute
```

- [ ] **Step 4: GREEN**

- [ ] **Step 5: Commit**

---

### Task 4: Model switch — parse and persist `routing_mode` + `profile`

**Files:**
- Modify: `hermes_cli/model_switch.py` (`ModelSwitchRequest`, `parse_model_switch_args`, `switch_model`, `_apply_model_switch` helpers)
- Create: `tests/hermes_cli/test_model_switch_omniroute.py`

**Interfaces:**
- Extends `ModelSwitchRequest`:

```python
@dataclass(frozen=True)
class ModelSwitchRequest:
    ...
    omniroute_profile: str = ""
    omniroute_routing_mode: str = ""  # "auto" | "explicit" | ""
```

- CLI/TUI wire form (document in slash help):

```text
/model auto --provider omniroute --profile coding --routing-mode auto
/model anthropic/claude-sonnet-4-20250514 --provider omniroute --routing-mode explicit
```

Picker emits this string from TUI/web (Task 5–6).

- Session `model_config` keys:

```python
{
  "provider": "omniroute",
  "model": "auto" | "<explicit>",
  "omniroute_routing_mode": "auto" | "explicit",
  "omniroute_envelope": {"profile": "coding"} | null,
}
```

- [ ] **Step 1: Failing tests**

```python
def test_parse_profile_and_routing_mode():
    from hermes_cli.model_switch import parse_model_switch_args

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
```

- [ ] **Step 2: RED**

- [ ] **Step 3: Extend `parse_model_flags_detailed` / `parse_model_switch_args`; in `switch_model` result dict include routing fields for gateway to persist**

- [ ] **Step 4: GREEN**

- [ ] **Step 5: Commit**

---

### Task 5: Runtime wire-through — agent → transport

**Files:**
- Modify: `tui_gateway/server.py` (`_apply_model_switch`, `_runtime_model_config`)
- Modify: `run_agent.py` (read `model_config` when building transport params)
- Modify: `agent/transports/chat_completions.py`
- Test: extend `tests/providers/test_omniroute_envelope.py` with transport explicit-mode test

**Interfaces:**
- Consumes: session `model_config.omniroute_routing_mode`, `model_config.omniroute_envelope`
- Produces: `build_kwargs(..., omniroute_routing_mode=..., omniroute_envelope=...)`

- [ ] **Step 1: Failing transport test**

```python
def test_chat_completions_explicit_mode_no_envelope():
    from agent.transports import get_transport

    transport = get_transport("chat_completions")
    kwargs = transport.build_kwargs(
        model="anthropic/claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": "Hi"}],
        tools=[],
        provider_profile=_profile(),
        provider_name="omniroute",
        omniroute_routing_mode="explicit",
        omniroute_envelope={"profile": "coding"},
    )
    assert kwargs["model"] == "anthropic/claude-sonnet-4-20250514"
    assert "omniroute" not in (kwargs.get("extra_body") or {})
```

- [ ] **Step 2: RED**

- [ ] **Step 3: Thread kwargs; `_runtime_model_config` stores envelope only when `routing_mode=="auto"`**

- [ ] **Step 4: GREEN + run existing envelope tests**

- [ ] **Step 5: Commit**

---

### Task 6: TUI picker tree (OmniRoute → Auto | Models)

**Files:**
- Modify: `ui-tui/src/gatewayTypes.ts`
- Modify: `ui-tui/src/components/modelPicker.tsx`
- Modify: `ui-tui/src/domain/slash.ts` (if needed for emitted `/model` string)
- Test: `ui-tui/src/components/modelPicker.omniroute.test.ts` (vitest unit tests for stage navigation)

**Interfaces:**
- Consumes: `ModelOptionProvider.model_groups`
- Produces on select: slash string e.g. `auto --provider omniroute --profile coding --routing-mode auto`

- [ ] **Step 1: Add types**

```typescript
export interface ModelGroupEntry {
  id: string
  label: string
  profile?: string
  wire_model: string
}

export interface ModelOptionGroup {
  id: string
  label: string
  routing_mode: 'auto' | 'explicit'
  entries: ModelGroupEntry[]
}

export interface ModelOptionProvider {
  ...
  model_groups?: ModelOptionGroup[]
}
```

- [ ] **Step 2: Extend `Stage` type: `'provider' | 'group' | 'model' | ...`**

When selected provider has `model_groups`, go to `group` stage instead of flat `model`.

- [ ] **Step 3: Vitest — selecting Auto group shows 8 profiles**

- [ ] **Step 4: Implement UI + `onSelect` emission**

- [ ] **Step 5: Manual smoke: `npm test` in ui-tui for new test file**

- [ ] **Step 6: Commit**

---

### Task 7: Web picker tree

**Files:**
- Modify: `web/src/components/ModelPickerDialog.tsx`
- Modify: `web/src/pages/ModelsPage.tsx` (status chip: `OmniRoute · Auto · Coding`)
- Mirror TUI stage logic; standalone mode uses `POST /api/model/set` with extended body or query fields `{ routing_mode, profile }` — extend `hermes_cli/web_server.py` `POST /api/model/set` minimally to accept optional `omniroute_profile` + `omniroute_routing_mode` JSON fields (same session keys as Task 4).

**Interfaces:**
- Consumes: same `model_groups` payload from `GET /api/model/options`

- [ ] **Step 1: Extend `/api/model/set` handler tests** (if exist) or add `tests/hermes_cli/test_web_model_set_omniroute.py`

- [ ] **Step 2: Implement dialog stages**

- [ ] **Step 3: Chip display helper**

- [ ] **Step 4: Commit**

---

### Task 8: CLI / legacy prompt_toolkit picker parity

**Files:**
- Modify: `cli.py` (`_open_model_picker`, selection handler ~11168)

**Interfaces:**
- Consumes: `build_model_options_payload()` — if omniroute row has `model_groups`, show submenu Auto / Models before flat list.

- [ ] **Step 1: Manual test checklist in commit message**

- [ ] **Step 2: Implement submenu using `model_groups`**

- [ ] **Step 3: Commit**

---

### Task 9: Telegram / Discord (v1 behavior)

**Files:**
- Modify: `gateway/slash_commands.py` — accept `--profile`, `--routing-mode` on `/model`
- Modify: `plugins/platforms/telegram/adapter.py` — `send_model_picker`: for omniroute, first button row **Auto (general)** → `auto --provider omniroute --profile general --routing-mode auto`; second page or inline list = filtered explicit models only (no `auto/*`)
- Modify: `plugins/platforms/discord/adapter.py` — same pattern

**Spec (v1, not v1.1 keyboard):**
- Auto path always `profile=general` from platform picker buttons.
- Full eight-profile keyboard deferred to v1.1 (document in code comment).

- [ ] **Step 1: Unit test on `list_picker_providers` output — omniroute explicit models filtered**

Add to `tests/hermes_cli/test_omniroute_picker.py`:

```python
def test_picker_provider_rows_filter_omniroute_explicit(monkeypatch):
    # mock list_authenticated_providers omniroute row; assert no auto/ in models group
    ...
```

- [ ] **Step 2: Implement Telegram/Discord Auto button + filtered explicit list**

- [ ] **Step 3: Commit**

---

### Task 10: Integration verification + docs

**Files:**
- Modify: `docs/superpowers/plans/2026-08-30-hermes-model-picker.md` — check off acceptance section
- Modify: HermesVault `.superpowers/sdd/progress.md` (one line: plan written, link to hermes-agent path) — optional cross-repo note only

- [x] **Step 1: Run full acceptance test command (see top)** — 22/22 plan command; 32/32 extended; TUI/web vitest 4+4.

- [x] **Step 2: Manual acceptance checklist (six items) — record results in PR description template** — see Acceptance tests § above.

- [x] **Step 3: Commit any doc/checklist updates**

---

## Explicit non-goals (do not implement)

| Item | Reason |
| --- | --- |
| ACP `set_session_model` envelope | Design v1.2 |
| Cron job profile UI | Pinned jobs only |
| Constraints/objective picker UI | v1 defaults only |
| OmniRoute server / envelope enforcement | Separate deploy plan |
| Reintroduce `auto/best-chat` / `auto/best-free` in Hermes config or UI | Contract violation |

---

## Self-review (spec coverage)

| Design requirement | Task |
| --- | --- |
| Shared inventory first | Task 3 |
| Auto vs Explicit separation | Tasks 2, 4, 5 |
| Envelope only for `model: auto` | Tasks 2, 5 |
| Explicit bypasses envelope | Tasks 2, 5 |
| Filter `auto/*` from Models list | Task 1, 3 |
| TUI + web tree | Tasks 6, 7 |
| Telegram/Discord v1 (Auto → general) | Task 9 |
| No ACP/cron | Non-goals |
| Contract tests | Tasks 1–5, 10 |
| OmniRouter v0 contract untouched | No OmniRoute files in plan |

**Placeholder scan:** none.

**Type consistency:** `omniroute_routing_mode` values `"auto"` | `"explicit"` used consistently across provider, session, transport, and UI emission.

---

## Runtime note (for implementers)

OmniRoute on `:20128` may still be **stock** 3.8.49 during UI rollout. Auto + envelope payloads are **safe** (ignored on stock). Full profile enforcement requires deploying `hermes-workload-policy-v0` per HermesVault deploy plan — **not part of this plan**.

---

## PR description template (Task 10 record)

**Summary:** OmniRoute model picker (Auto + eight profiles + explicit Models) across inventory, provider, runtime, TUI, web, CLI, Telegram, Discord. Shared inventory single source of truth; `auto/*` hidden from explicit UI.

**Test plan:**
- [x] Plan acceptance command (22/22)
- [x] Extended suite (32/32)
- [x] TUI + web vitest (4+4 each)
- [x] Manual checklist items 1–6 (contract-level PASS; live UI optional on stock OmniRoute)
- [x] Representative skill smoke (vault recall + skills list)
- [x] Envelope invariant: auto → envelope; explicit → no envelope

**Branch:** `omniroute-model-picker` @ `39a4b395e9` (Tasks 1–10 complete). No merge/push/PR in implementation scope.
