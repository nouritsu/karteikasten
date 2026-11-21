import { describe, expect, it } from 'vitest'
import { deckWord } from './testing'
import { fold, search } from './words'

describe('Words search', () => {
  const words = [
    deckWord('Hand#noun#1', 312, { gloss_en: [{ text: 'hand', tags: [] }] }),
    deckWord('handeln#verb#1', 1408, { gloss_en: [{ text: 'to act; to trade', tags: [] }] }),
    deckWord('Straße#noun#1', 200, { gloss_en: [{ text: 'street', tags: [] }] }),
    deckWord('schön#adj#1', 150, { gloss_en: [{ text: 'beautiful', tags: [] }] }),
  ]

  it('folds umlauts and ß', () => {
    expect(fold('Hände Straße')).toBe('haende strasse')
  })

  it('finds lemmas by prefix, then inside, then by meaning', () => {
    expect(search(words, 'hand').map((w) => w.lemma)).toEqual(['Hand', 'handeln'])
    expect(search(words, 'strasse').map((w) => w.lemma)).toEqual(['Straße'])
    expect(search(words, 'schoen').map((w) => w.lemma)).toEqual(['schön'])
    expect(search(words, 'trade').map((w) => w.lemma)).toEqual(['handeln'])
    expect(search(words, 'ac')).toEqual([]) // meanings (to act) from three letters
  })
})
