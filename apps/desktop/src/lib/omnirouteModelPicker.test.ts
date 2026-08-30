import { describe, expect, it } from 'vitest'

import {
  buildModelConfigSetValue,
  buildOmnirouteSelectCommand,
  providerModelCount,
  providerUsesModelGroups
} from './omnirouteModelPicker'

const groups = [
  {
    id: 'auto',
    label: 'Auto',
    routing_mode: 'auto' as const,
    entries: [{ id: 'coding', label: 'Coding', profile: 'coding', wire_model: 'auto' }]
  },
  {
    id: 'models',
    label: 'Models',
    routing_mode: 'explicit' as const,
    entries: [
      {
        id: 'gemini/gemini-2.5-flash-lite',
        label: 'gemini/gemini-2.5-flash-lite',
        wire_model: 'gemini/gemini-2.5-flash-lite'
      }
    ]
  }
]

describe('omnirouteModelPicker desktop helpers', () => {
  it('builds auto config.set value with profile + routing-mode', () => {
    expect(
      buildModelConfigSetValue(
        {
          model: 'auto',
          provider: 'omniroute',
          omnirouteRoutingMode: 'auto',
          omnirouteProfile: 'coding'
        },
        '--global'
      )
    ).toBe('auto --provider omniroute --profile coding --routing-mode auto --global')
  })

  it('builds explicit config.set value', () => {
    expect(
      buildModelConfigSetValue(
        {
          model: 'gemini/gemini-2.5-flash-lite',
          provider: 'omniroute',
          omnirouteRoutingMode: 'explicit'
        },
        '--session'
      )
    ).toBe('gemini/gemini-2.5-flash-lite --provider omniroute --routing-mode explicit --session')
  })

  it('builds slash-style auto command', () => {
    expect(buildOmnirouteSelectCommand('omniroute', groups[0]!, groups[0]!.entries[0]!, '')).toBe(
      'auto --provider omniroute --profile coding --routing-mode auto'
    )
  })

  it('counts grouped models', () => {
    expect(providerUsesModelGroups({ model_groups: groups })).toBe(true)
    expect(providerModelCount({ model_groups: groups, models: [] })).toBe(2)
  })
})
