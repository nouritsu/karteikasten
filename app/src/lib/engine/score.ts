// The score of one review (spec: Card flow and score). Every number is a setting.

export type Hint = 'audio' | 'forms' | 'sentence' | 'picture' | 'cognate'

export interface ScoreSettings {
  start: number
  step: number // points lost per interval
  intervalMs: number
  graceMs: number // no decay before this much active time
  penalties: Record<Hint, number>
  // Lowest score of each band after "Weiß ich"; below `good` is Hard.
  bands: { good: number; easy: number }
}

export const DEFAULT_SCORE: ScoreSettings = {
  start: 100,
  step: 10,
  intervalMs: 3000,
  graceMs: 2000,
  penalties: { audio: 10, forms: 15, sentence: 20, picture: 50, cognate: 30 },
  bands: { good: 40, easy: 85 },
}

/** Score after `activeMs` of active time with these hints charged (each at most once). */
export function score(activeMs: number, hints: Iterable<Hint>, settings: ScoreSettings = DEFAULT_SCORE): number {
  const steps = Math.floor(Math.max(0, activeMs - settings.graceMs) / settings.intervalMs)
  let penalty = 0
  for (const hint of new Set(hints)) penalty += settings.penalties[hint]
  return Math.min(100, Math.max(0, settings.start - settings.step * steps - penalty))
}

// FSRS ratings as ts-fsrs numbers them.
export const Rating = { Again: 1, Hard: 2, Good: 3, Easy: 4 } as const
export type Grade = (typeof Rating)[keyof typeof Rating]

export type Band = 'easy' | 'good' | 'hard'

/** The band a score is in: the grade "Weiß ich" would give it now. */
export function band(value: number, settings: ScoreSettings = DEFAULT_SCORE): Band {
  if (value >= settings.bands.easy) return 'easy'
  if (value >= settings.bands.good) return 'good'
  return 'hard'
}

const BAND_GRADE: Record<Band, Grade> = { easy: Rating.Easy, good: Rating.Good, hard: Rating.Hard }

/** The FSRS grade for an answer; "Weiß ich nicht" and "war doch falsch" are Again. */
export function grade(
  answer: 'know' | 'dont_know',
  value: number,
  undone = false,
  settings: ScoreSettings = DEFAULT_SCORE,
): Grade {
  if (answer === 'dont_know' || undone) return Rating.Again
  return BAND_GRADE[band(value, settings)]
}
