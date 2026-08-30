import type { ModelGroupEntry, ModelOptionGroup, ModelOptionProvider } from '@/types/hermes'

const PROFILE_LABELS: Record<string, string> = {
  general: 'General',
  coding: 'Coding',
  hard_reasoning: 'Hard reasoning',
  review: 'Review',
  long_context: 'Long context',
  cheap: 'Cheap',
  vision: 'Vision',
  web: 'Web'
}

export function profileDisplayLabel(profile: string): string {
  return PROFILE_LABELS[profile] ?? profile.replace(/_/g, ' ')
}

export function providerUsesModelGroups(
  provider: Pick<ModelOptionProvider, 'model_groups'> | null | undefined
): boolean {
  return (provider?.model_groups?.length ?? 0) > 0
}

export function providerModelCount(
  provider: Pick<ModelOptionProvider, 'model_groups' | 'models' | 'total_models'>
): number {
  if (providerUsesModelGroups(provider)) {
    return provider.model_groups?.reduce((n, g) => n + g.entries.length, 0) ?? 0
  }

  return provider.total_models ?? provider.models?.length ?? 0
}

export function buildOmnirouteSelectCommand(
  providerSlug: string,
  group: ModelOptionGroup,
  entry: ModelGroupEntry,
  persistSuffix: string
): string {
  const suffix = persistSuffix.startsWith(' ') ? persistSuffix : ` ${persistSuffix}`

  if (group.routing_mode === 'auto') {
    const profile = entry.profile ?? entry.id

    return `auto --provider ${providerSlug} --profile ${profile} --routing-mode auto${suffix}`
  }

  return `${entry.wire_model} --provider ${providerSlug} --routing-mode explicit${suffix}`
}

export function buildModelConfigSetValue(selection: {
  model: string
  provider: string
  omnirouteRoutingMode?: 'auto' | 'explicit'
  omnirouteProfile?: string
}, scope: string): string {
  const scopePart = scope.startsWith(' ') ? scope : ` ${scope}`

  if (selection.omnirouteRoutingMode === 'auto') {
    const profile = (selection.omnirouteProfile || 'general').trim() || 'general'

    return `auto --provider ${selection.provider} --profile ${profile} --routing-mode auto${scopePart}`
  }

  if (selection.omnirouteRoutingMode === 'explicit') {
    return `${selection.model} --provider ${selection.provider} --routing-mode explicit${scopePart}`
  }

  return `${selection.model} --provider ${selection.provider}${scopePart}`
}

export interface OmnirouteApplyPayload {
  model: string
  omnirouteRoutingMode?: 'auto' | 'explicit'
  omnirouteProfile?: string
}

export function omnirouteApplyPayload(
  providerSlug: string,
  group: ModelOptionGroup,
  entry: ModelGroupEntry
): OmnirouteApplyPayload {
  void providerSlug

  if (group.routing_mode === 'auto') {
    return {
      model: 'auto',
      omnirouteRoutingMode: 'auto',
      omnirouteProfile: entry.profile ?? entry.id
    }
  }

  return {
    model: entry.wire_model,
    omnirouteRoutingMode: 'explicit',
    omnirouteProfile: ''
  }
}

/** Flatten OmniRoute groups into catalog rows (label + switch payload). */
export function flattenOmnirouteCatalogEntries(provider: ModelOptionProvider): Array<{
  key: string
  label: string
  model: string
  omnirouteRoutingMode: 'auto' | 'explicit'
  omnirouteProfile: string
  groupLabel: string
}> {
  const rows: Array<{
    key: string
    label: string
    model: string
    omnirouteRoutingMode: 'auto' | 'explicit'
    omnirouteProfile: string
    groupLabel: string
  }> = []

  for (const group of provider.model_groups ?? []) {
    for (const entry of group.entries) {
      const profile = entry.profile ?? ''
      const label =
        group.routing_mode === 'auto'
          ? entry.label.toLowerCase().startsWith('auto')
            ? entry.label
            : `Auto · ${entry.label}`
          : entry.label

      rows.push({
        key: `${provider.slug}:${group.id}:${entry.id}`,
        label,
        model: entry.wire_model,
        omnirouteRoutingMode: group.routing_mode,
        omnirouteProfile: profile,
        groupLabel: group.label
      })
    }
  }

  return rows
}
