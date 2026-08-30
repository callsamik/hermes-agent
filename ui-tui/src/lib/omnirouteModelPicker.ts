import type { ModelGroupEntry, ModelOptionGroup, ModelOptionProvider } from '../gatewayTypes.js'

export function providerUsesModelGroups(provider: ModelOptionProvider | undefined): boolean {
  return (provider?.model_groups?.length ?? 0) > 0
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

export function autoProfileEntryCount(groups: ModelOptionGroup[] | undefined): number {
  const auto = groups?.find(g => g.id === 'auto')
  return auto?.entries.length ?? 0
}
