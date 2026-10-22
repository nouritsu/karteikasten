import { describe, expect, it } from 'vitest'
import { de } from '../i18n/de'
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
    expect(keyFormLines(hand, de)).toEqual(['Pl. die Hände', 'Gen. der Hand'])
  })

  it('marks plural-only and weak nouns', () => {
    expect(keyFormLines(word({ flags: ['plural_only'] }), de)).toEqual(['nur Plural'])
    const junge = word({ gender: 'm', key_forms: { plural: 'Jungen', genitive: 'Jungen' }, flags: ['weak_noun'] })
    expect(keyFormLines(junge, de)).toEqual(['Pl. die Jungen', 'Gen. des Jungen', 'schwach dekliniert'])
  })

  it('shows verb forms with both auxiliaries', () => {
    const fahren = word({
      lemma: 'fahren', pos: 'verb', flags: ['strong'],
      key_forms: { er: 'fährt', du: 'fährst', praeteritum: 'fuhr', partizip2: 'gefahren', auxiliary: ['haben', 'sein'] },
    })
    expect(keyFormLines(fahren, de)).toEqual(['er fährt · du fährst', 'Prät. fuhr · Perf. hat/ist gefahren · stark'])
  })

  it('shows comparison, case and conjunction type', () => {
    expect(keyFormLines(word({ lemma: 'gut', pos: 'adj', key_forms: { comparative: 'besser', superlative: 'am besten' } }), de))
      .toEqual(['gut · besser · am besten'])
    expect(keyFormLines(word({ pos: 'prep', key_forms: { case: 'two-way', cases: ['acc', 'dat'] } }), de))
      .toEqual(['mit Akk/Dat (Wechselpräposition)'])
    expect(keyFormLines(word({ pos: 'prep', key_forms: { case: 'gen', cases: ['gen', 'dat'] } }), de)).toEqual(['mit Gen / Dat'])
    expect(keyFormLines(word({ pos: 'conj', key_forms: { conjunction: 'subordinating' } }), de))
      .toEqual(['unterordnend (Verb am Ende)'])
  })

  it('colours articles by gender, plural-only in its own colour', () => {
    expect(genderClass(word({ gender: 'n' }))).toBe('das')
    expect(genderClass(word({ flags: ['plural_only'] }))).toBe('plural')
    expect(genderClass(word({ pos: 'verb' }))).toBe(null)
  })
})
