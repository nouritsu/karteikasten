import { describe, expect, it } from 'vitest'
import { strings } from '../strings'
import type { DeckWord } from '../types'
import { genderClass, keyFormLines } from './format'

function word(partial: Partial<DeckWord>): DeckWord {
  return {
    id: 'x#noun#1', rank: 1, lemma: 'x', pos: 'noun', gender: null, article: null, token_share: 0, coverage_cum: 0,
    ipa: null, syllables: null, stress_syllable: null, cognate_en: null, flags: [], key_forms: {}, tables: {},
    gloss_en: [], gloss_de: [], audio: null, sentences: [],
    ...partial,
  }
}

// Shapes as the pipeline writes them (data/dist/deck/*-spike).
describe('key form lines', () => {
  it('shows plural and genitive with articles', () => {
    const hand = word({ lemma: 'Hand', gender: 'f', article: 'die', key_forms: { plural: 'Hände', genitive: 'Hand' } })
    expect(keyFormLines(hand, strings)).toEqual(['pl. die Hände', 'gen. der Hand'])
  })

  it('marks plural-only and weak nouns', () => {
    expect(keyFormLines(word({ flags: ['plural_only'] }), strings)).toEqual(['plural only'])
    const junge = word({ gender: 'm', key_forms: { plural: 'Jungen', genitive: 'Jungen' }, flags: ['weak_noun'] })
    expect(keyFormLines(junge, strings)).toEqual(['pl. die Jungen', 'gen. des Jungen', 'weak noun'])
  })

  it('shows verb forms with both auxiliaries', () => {
    const fahren = word({
      lemma: 'fahren', pos: 'verb', flags: ['strong'],
      key_forms: { er: 'fährt', du: 'fährst', praeteritum: 'fuhr', partizip2: 'gefahren', auxiliary: ['haben', 'sein'] },
    })
    expect(keyFormLines(fahren, strings)).toEqual(['er fährt · du fährst', 'past fuhr · perfect hat/ist gefahren · strong'])
  })

  it('shows comparison, case and conjunction type', () => {
    expect(keyFormLines(word({ lemma: 'gut', pos: 'adj', key_forms: { comparative: 'besser', superlative: 'am besten' } }), strings))
      .toEqual(['gut · besser · am besten'])
    expect(keyFormLines(word({ pos: 'prep', key_forms: { case: 'two-way', cases: ['acc', 'dat'] } }), strings))
      .toEqual(['takes acc or dat (two-way)'])
    expect(keyFormLines(word({ pos: 'prep', key_forms: { case: 'gen', cases: ['gen', 'dat'] } }), strings)).toEqual(['takes gen / dat'])
    expect(keyFormLines(word({ pos: 'conj', key_forms: { conjunction: 'subordinating' } }), strings))
      .toEqual(['subordinating: the verb goes last'])
  })

  it('shows the modal class, contractions and ordinals', () => {
    const koennen = word({ pos: 'verb', flags: ['modal'], key_forms: { er: 'kann', praeteritum: 'konnte' } })
    expect(keyFormLines(koennen, strings)).toEqual(['er kann', 'past konnte · modal verb'])
    const in_ = word({ pos: 'prep', key_forms: { case: 'two-way', cases: ['acc', 'dat'], contractions: ['im', 'ins'] } })
    expect(keyFormLines(in_, strings)).toEqual(['takes acc or dat (two-way)', 'contractions: im, ins'])
    expect(keyFormLines(word({ pos: 'num', key_forms: { ordinal: 'zweite' } }), strings)).toEqual(['ordinal: zweite'])
  })

  it('colours articles by gender, plural-only in its own colour', () => {
    expect(genderClass(word({ gender: 'n' }))).toBe('das')
    expect(genderClass(word({ flags: ['plural_only'] }))).toBe('plural')
    expect(genderClass(word({ pos: 'verb' }))).toBe(null)
  })
})
