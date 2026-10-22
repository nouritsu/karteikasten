// Deck words for tests.

import type { DeckWord, Sentence } from './types'

export function deckWord(id: string, rank: number, extra: Partial<DeckWord> = {}): DeckWord {
  const [lemma, pos] = id.split('#')
  return {
    id, rank, lemma, pos: pos ?? 'noun', gender: null, article: null, token_share: 0.01, coverage_cum: 0, ipa: null,
    syllables: null, stress_syllable: null, cognate_en: null, flags: [], key_forms: {}, tables: {}, gloss_en: [],
    gloss_de: [], audio: null, sentences: [], ...extra,
  }
}

/** Words a#x#1, b#x#1, ... ranked in order. */
export function deckWords(count: number): DeckWord[] {
  return Array.from({ length: count }, (_, i) => deckWord(`${String.fromCharCode(97 + i)}#noun#1`, i + 1))
}

export function sentence(id: string, deckTokens: string[], outOfDeck = 0): Sentence {
  return {
    id, de: id, en: null, hl: [0, 1], source: 'test', source_url: '', author: 'x', license: 'CC0', native: true,
    en_author: null, en_license: null, deck_token_ids: deckTokens, out_of_deck: outOfDeck,
  }
}
