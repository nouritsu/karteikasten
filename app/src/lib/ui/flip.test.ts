import { describe, expect, it } from 'vitest'
import { flips, mirrored, NAME_ART } from './flip'

describe('card flip', () => {
  it('turns over on answering and on Weiter only', () => {
    expect(flips('running', 'answered')).toBe(true)
    expect(flips('answered', 'ready')).toBe(true)
    expect(flips('ready', 'reveal')).toBe(false)
    expect(flips('reveal', 'running')).toBe(false)
    expect(flips('answered', 'answered')).toBe(false)
    expect(flips('answered', 'done')).toBe(true)
    expect(flips('done', 'ready')).toBe(false) // a card coming due on Feierabend just appears
  })

  it('mirrors the title', () => {
    expect(mirrored('Karte')).toBe('etraK')
    expect(mirrored('Card')).toBe('draC')
  })

  it('keeps the name art at five lines and 41 columns', () => {
    const lines = NAME_ART.split('\n')
    expect(lines).toHaveLength(5)
    expect(Math.max(...lines.map((line) => line.length))).toBe(41)
    expect(lines[4]).toBe(String.raw` |_| |_|\___/ \__,_|_|  |_|\__|___/\__,_|`)
  })
})
