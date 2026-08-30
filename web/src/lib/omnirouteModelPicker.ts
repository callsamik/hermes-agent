import type { ModelGroupEntry, ModelOptionGroup } from "./api";

const PROFILE_LABELS: Record<string, string> = {
  general: "General",
  coding: "Coding",
  hard_reasoning: "Hard reasoning",
  review: "Review",
  long_context: "Long context",
  cheap: "Cheap",
  vision: "Vision",
  web: "Web",
};

export interface MainModelDisplay {
  provider: string;
  model: string;
  omniroute_routing_mode?: string;
  omniroute_envelope?: { profile?: string };
}

export function profileDisplayLabel(profile: string): string {
  return PROFILE_LABELS[profile] ?? profile.replace(/_/g, " ");
}

export function providerUsesModelGroups(
  provider: { model_groups?: ModelOptionGroup[] } | null | undefined,
): boolean {
  return (provider?.model_groups?.length ?? 0) > 0;
}

export function providerModelCount(provider: {
  model_groups?: ModelOptionGroup[];
  models?: string[];
  total_models?: number;
}): number {
  if (providerUsesModelGroups(provider)) {
    return (
      provider.model_groups?.reduce((n, g) => n + g.entries.length, 0) ?? 0
    );
  }
  return provider.total_models ?? provider.models?.length ?? 0;
}

export function buildOmnirouteSelectCommand(
  providerSlug: string,
  group: ModelOptionGroup,
  entry: ModelGroupEntry,
  persistSuffix: string,
): string {
  const suffix = persistSuffix ? ` ${persistSuffix.trim()}` : "";
  if (group.routing_mode === "auto") {
    const profile = entry.profile ?? entry.id;
    return `auto --provider ${providerSlug} --profile ${profile} --routing-mode auto${suffix}`;
  }
  return `${entry.wire_model} --provider ${providerSlug} --routing-mode explicit${suffix}`;
}

export function formatMainModelLabel(main: MainModelDisplay): string {
  const prov = (main.provider || "").trim().toLowerCase();
  const model = (main.model || "").trim();
  if (!prov && !model) {
    return "(unset)";
  }
  if (prov === "omniroute" && main.omniroute_routing_mode === "auto") {
    const profile = main.omniroute_envelope?.profile ?? "general";
    return `OmniRoute · Auto · ${profileDisplayLabel(profile)}`;
  }
  if (prov === "omniroute" && main.omniroute_routing_mode === "explicit") {
    return `OmniRoute · ${model || "(unset)"}`;
  }
  const parts = [main.provider, main.model].filter(Boolean);
  return parts.join(" · ") || "(unset)";
}

export interface OmnirouteApplyPayload {
  model: string;
  omnirouteRoutingMode?: "auto" | "explicit";
  omnirouteProfile?: string;
}

export function omnirouteApplyPayload(
  providerSlug: string,
  group: ModelOptionGroup,
  entry: ModelGroupEntry,
): OmnirouteApplyPayload | null {
  if (group.routing_mode === "auto") {
    return {
      model: "auto",
      omnirouteRoutingMode: "auto",
      omnirouteProfile: entry.profile ?? entry.id,
    };
  }
  return {
    model: entry.wire_model,
    omnirouteRoutingMode: "explicit",
    omnirouteProfile: "",
  };
}
