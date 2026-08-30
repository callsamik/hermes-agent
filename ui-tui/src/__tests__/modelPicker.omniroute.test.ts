import { describe, expect, it } from 'vitest'

import {
  autoProfileEntryCount,
  buildOmnirouteSelectCommand,
  providerUsesModelGroups
} from '../lib/omnirouteModelPicker.js'
import type { ModelOptionGroup, ModelOptionProvider } from '../gatewayTypes.js'

const omnirouteGroups: ModelOptionGroup[] = [
  {
    id: 'auto',
    label: 'Auto',
    routing_mode: 'auto',
    entries: [
      { id: 'general', label: 'General', profile: 'general', wire_model: 'auto' },
      { id: 'coding', label: 'Coding', profile: 'coding', wire_model: 'auto' }
    ]
  },
  {
    id: 'models',
    label: 'Models',
    routing_mode: 'explicit',
    entries: [
      {
        id: 'anthropic/claude-sonnet-4-20250514',
        label: 'anthropic/claude-sonnet-4-20250514',
        wire_model: 'anthropic/claude-sonnet-4-20250514'
      }
    ]
  }
]

describe('OmniRoute model picker helpers', () => {
  it('detects providers with model_groups', () => {
    const withGroups: ModelOptionProvider = {
      name: 'OmniRoute',
      slug: 'omniroute',
      model_groups: omnirouteGroups
    }
    const flat: ModelOptionProvider = { name: 'Groq', slug: 'groq', models: ['llama'] }

    expect(providerUsesModelGroups(withGroups)).toBe(true)
    expect(providerUsesModelGroups(flat)).toBe(false)
  })

  it('auto group exposes profile entries', () => {
    expect(autoProfileEntryCount(omnirouteGroups)).toBe(2)
  })

  it('builds auto slash command with profile and routing mode', () => {
    const cmd = buildOmnirouteSelectCommand(
      'omniroute',
      omnirouteGroups[0]!,
      omnirouteGroups[0]!.entries[1]!,
      '--session'
    )
    expect(cmd).toBe(
      'auto --provider omniroute --profile coding --routing-mode auto --session'
    )
  })

  it('builds explicit slash command without envelope flags', () => {
    const cmd = buildOmnirouteSelectCommand(
      'omniroute',
      omnirouteGroups[1]!,
      omnirouteGroups[1]!.entries[0]!,
      '--session'
    )
    expect(cmd).toBe(
      'anthropic/claude-sonnet-4-20250514 --provider omniroute --routing-mode explicit --session'
    )
  })
})
