// Your level (D67). The words up to its rank are likely known already, so instead of
// coming one by one with the new words, they come as quick checks, a few a day: a word
// you know gets Easy and comes back in about a week, then months; one you miss is
// learnt like any new word. New words start right after the level's rank.
//
// The ranks are a starting guess at CEFR sub-levels: the deck is ranked by frequency,
// and CEFR word lists also hold topic words of lower frequency.

export const LEVELS = [
  { id: 'beginner', name: 'Beginner', rank: 0 },
  { id: 'a1.1', name: 'A1.1', rank: 100 },
  { id: 'a1.2', name: 'A1.2', rank: 250 },
  { id: 'a2.1', name: 'A2.1', rank: 500 },
  { id: 'a2.2', name: 'A2.2', rank: 800 },
  { id: 'b1.1', name: 'B1.1', rank: 1200 },
  { id: 'b1.2', name: 'B1.2', rank: 1600 },
] as const

export type Level = (typeof LEVELS)[number]
export type LevelId = Level['id']
export const LEVEL_IDS: LevelId[] = LEVELS.map((l) => l.id)

export const levelOf = (id: LevelId): Level => LEVELS.find((l) => l.id === id) ?? LEVELS[0]

/** The level `direction` steps from `id`, or the same at either end. */
export function stepLevel(id: LevelId, direction: -1 | 1): LevelId {
  const i = LEVEL_IDS.indexOf(id) + direction
  return LEVEL_IDS[Math.min(LEVEL_IDS.length - 1, Math.max(0, i))]
}

/** How many of the last first answers the nudge looks at, and how many must be known. */
export const NUDGE_WINDOW = 50
export const NUDGE_KNOWN = 48

export interface Nudge {
  known: number
  total: number
  next: Level
}

/** The next level up, when the last NUDGE_WINDOW first answers on the words up to its rank
 *  were nearly all known (`grades` in time order); else null. */
export function nudge(grades: readonly number[], id: LevelId): Nudge | null {
  const next = levelOf(stepLevel(id, 1))
  if (next.id === id || grades.length < NUDGE_WINDOW) return null
  const last = grades.slice(-NUDGE_WINDOW)
  const known = last.filter((grade) => grade > 1).length
  return known >= NUDGE_KNOWN ? { known, total: last.length, next } : null
}
