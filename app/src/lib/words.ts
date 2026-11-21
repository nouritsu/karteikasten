// Words (spec: Words; D54): each word's status, and the search, which is umlaut-tolerant
// (ae finds ä, ss finds ß) and finds a word by its lemma first, then by its English meaning.

import { State, type WordState } from './engine/scheduler'
import type { DeckWord } from './types'

export type WordStatus = 'new' | 'learning' | 'known' | 'paused'
export const STATUSES: WordStatus[] = ['new', 'learning', 'known', 'paused']

export function statusOf(state: WordState | undefined): WordStatus {
  if (state?.suspended) return 'paused'
  if (!state || state.card.state === State.New) return 'new'
  return state.card.state === State.Review ? 'known' : 'learning'
}

/** Lower case, umlauts and ß spelt out, so "Haende", "hände" and "HÄNDE" meet. */
export function fold(text: string): string {
  return text
    .toLowerCase()
    .replaceAll('ä', 'ae')
    .replaceAll('ö', 'oe')
    .replaceAll('ü', 'ue')
    .replaceAll('ß', 'ss')
}

/** The words matching `query`, by rank: lemmas starting with it, then lemmas containing it,
 *  then (from three letters) words whose meaning contains it. */
export function search(words: readonly DeckWord[], query: string): DeckWord[] {
  const q = fold(query.trim())
  if (!q) return [...words]
  const starts: DeckWord[] = []
  const contains: DeckWord[] = []
  const meaning: DeckWord[] = []
  for (const word of words) {
    const lemma = fold(word.lemma)
    if (lemma.startsWith(q)) starts.push(word)
    else if (lemma.includes(q)) contains.push(word)
    else if (q.length >= 3 && word.gloss_en.some((g) => fold(g.text).includes(q))) meaning.push(word)
  }
  return [...starts, ...contains, ...meaning]
}
