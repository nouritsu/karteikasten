// D12: of the word's sentences (up to five, best first), show the one with the most
// words the learner already knows; ties go to fewer unknown words, then deck order.

import type { DeckWord, Sentence } from '../types'

export function chooseSentence(word: DeckWord, known: (id: string) => boolean): Sentence | undefined {
  let best: Sentence | undefined
  let bestKnown = -1
  let bestUnknown = Infinity
  for (const sentence of word.sentences) {
    const others = (sentence.deck_token_ids ?? []).filter((id) => id !== word.id)
    const knownCount = others.filter(known).length
    const unknown = others.length - knownCount + (sentence.out_of_deck ?? 0)
    if (knownCount > bestKnown || (knownCount === bestKnown && unknown < bestUnknown)) {
      best = sentence
      bestKnown = knownCount
      bestUnknown = unknown
    }
  }
  return best
}
