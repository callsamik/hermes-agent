import { describe, expect, it } from "vitest";

import type { ModelOptionGroup } from "./api";
import {
  buildOmnirouteSelectCommand,
  formatMainModelLabel,
  profileDisplayLabel,
  providerUsesModelGroups,
} from "./omnirouteModelPicker";

const groups: ModelOptionGroup[] = [
  {
    id: "auto",
    label: "Auto",
    routing_mode: "auto",
    entries: [
      { id: "coding", label: "Coding", profile: "coding", wire_model: "auto" },
    ],
  },
  {
    id: "models",
    label: "Models",
    routing_mode: "explicit",
    entries: [
      {
        id: "anthropic/claude-sonnet-4-20250514",
        label: "anthropic/claude-sonnet-4-20250514",
        wire_model: "anthropic/claude-sonnet-4-20250514",
      },
    ],
  },
];

describe("omnirouteModelPicker web helpers", () => {
  it("formats auto chip as OmniRoute · Auto · Profile", () => {
    expect(
      formatMainModelLabel({
        provider: "omniroute",
        model: "auto",
        omniroute_routing_mode: "auto",
        omniroute_envelope: { profile: "coding" },
      }),
    ).toBe("OmniRoute · Auto · Coding");
  });

  it("formats explicit chip without auto profile", () => {
    expect(
      formatMainModelLabel({
        provider: "omniroute",
        model: "anthropic/claude-sonnet-4-20250514",
        omniroute_routing_mode: "explicit",
      }),
    ).toBe("OmniRoute · anthropic/claude-sonnet-4-20250514");
  });

  it("builds auto command with profile and routing mode", () => {
    expect(
      buildOmnirouteSelectCommand(
        "omniroute",
        groups[0]!,
        groups[0]!.entries[0]!,
        "",
      ),
    ).toBe(
      "auto --provider omniroute --profile coding --routing-mode auto",
    );
  });

  it("detects model_groups on provider row", () => {
    expect(
      providerUsesModelGroups({
        name: "OmniRoute",
        slug: "omniroute",
        model_groups: groups,
      }),
    ).toBe(true);
    expect(profileDisplayLabel("hard_reasoning")).toBe("Hard reasoning");
  });
});
