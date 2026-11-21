// Which card comes next (spec: Scheduling). In order: words introduced but not yet
// rated, learning and relearning cards due now, reviews due today (oldest first),
// then the level's checks and new words by rank, each up to its day's limit. With
// nothing else left, a learning card due soon comes early. New words run like reviews
// (D53): the first answer is their first FSRS rating. Words up to the level's rank come
// as checks, under their own limit, and new words start after it (D67).

import type { DeckWord } from '../types'
import { nextRollover } from './day'
import { awaitingCheck, State, type WordState } from './scheduler'

export interface QueueInput {
  words: readonly DeckWord[] // by rank
  states: ReadonlyMap<string, WordState>
  now: Date
  n: number // study the words up to this rank
  newLeft: number // new words still allowed today
  level?: number // words up to this rank come as checks (D67); 0 or absent: none do
  checksLeft?: number // checks still allowed today
  last?: string // the card just finished: not again straight away, unless it is the only one
  learnAheadMs: number
}

export type Kind = 'check' | 'learning' | 'review' | 'level' | 'new' | 'early'

export interface Pick {
  word: DeckWord
  kind: Kind
}

interface Groups {
  checks: DeckWord[] // introduced by an Intro (before D53) and never rated
  learning: DeckWord[] // due now
  reviews: DeckWord[] // due before the day ends
  level: DeckWord[] // new, up to the level's rank: its checks, by rank
  fresh: DeckWord[] // new, past the level, by rank
  soon: DeckWord[] // learning, due within the learn-ahead window
  later: DeckWord[] // learning, due later today
}

function groups(q: QueueInput): Groups {
  const g: Groups = { checks: [], learning: [], reviews: [], level: [], fresh: [], soon: [], later: [] }
  const rollover = nextRollover(q.now).getTime()
  const now = q.now.getTime()
  const due = (w: DeckWord) => q.states.get(w.id)!.card.due.getTime()
  for (const word of q.words) {
    if (word.rank > q.n) continue
    const state = q.states.get(word.id)
    if (state?.suspended) continue
    if (!state || (!state.introduced && state.card.state === State.New)) {
      if (word.rank <= (q.level ?? 0)) g.level.push(word)
      else g.fresh.push(word)
    } else if (awaitingCheck(state)) {
      g.checks.push(word)
    } else if (state.card.state === State.Learning || state.card.state === State.Relearning) {
      const at = due(word)
      if (at <= now) g.learning.push(word)
      else if (at <= now + q.learnAheadMs) g.soon.push(word)
      else if (at < rollover) g.later.push(word)
    } else if (state.card.state === State.Review && due(word) < rollover) {
      g.reviews.push(word)
    }
  }
  for (const list of [g.learning, g.reviews, g.soon, g.later]) list.sort((a, b) => due(a) - due(b) || a.rank - b.rank)
  return g
}

/** The next card, or null when the day is done. */
export function nextCard(q: QueueInput): Pick | null {
  const g = groups(q)
  const lists: [Kind, DeckWord[]][] = [
    ['check', g.checks],
    ['learning', g.learning],
    ['review', g.reviews],
    ['level', (q.checksLeft ?? 0) > 0 ? g.level : []],
    ['new', q.newLeft > 0 ? g.fresh : []],
    ['early', g.soon],
  ]
  for (const [kind, list] of lists) {
    const word = list.find((w) => w.id !== q.last)
    if (word) return { word, kind }
  }
  for (const [kind, list] of lists) {
    if (list.length) return { word: list[0], kind } // only the card just finished is left
  }
  return null
}

/** Status-bar counts: cards still due today (checks, learning, reviews) and new words left,
 *  the level's checks among them. */
export function counts(q: QueueInput): { due: number; fresh: number; nextDue: Date | null } {
  const g = groups(q)
  const learning = [...g.learning, ...g.soon, ...g.later]
  const nextDue = learning.length ? q.states.get(learning[0].id)!.card.due : null
  return {
    due: g.checks.length + learning.length + g.reviews.length,
    fresh: Math.min(Math.max(0, q.newLeft), g.fresh.length) + Math.min(Math.max(0, q.checksLeft ?? 0), g.level.length),
    nextDue,
  }
}
