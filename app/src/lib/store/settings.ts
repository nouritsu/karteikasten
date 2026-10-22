// Study settings, kept in IndexedDB and in every export. Optionen edits them (Phase 6);
// language and theme stay in localStorage, which index.html reads before the first paint.

import { DEFAULT_SCORE, type ScoreSettings } from '../engine/score'

export interface Settings {
  newPerDay: number
  n: number | null // study the top n words; null means the whole deck (its n_max)
  retention: number // FSRS desired retention
  score: ScoreSettings
  audioAfterAnswer: boolean
  haptics: boolean
  learnAheadMin: number // with nothing else left, a learning card due this soon comes early
}

export const DEFAULT_SETTINGS: Settings = {
  newPerDay: 15,
  n: null,
  retention: 0.9,
  score: DEFAULT_SCORE,
  audioAfterAnswer: true,
  haptics: true,
  learnAheadMin: 20,
}

/** Saved settings over the defaults, so a setting added later gets its default. */
export function withDefaults(saved: Partial<Settings> | undefined): Settings {
  const score = { ...DEFAULT_SCORE, ...saved?.score }
  score.penalties = { ...DEFAULT_SCORE.penalties, ...saved?.score?.penalties }
  score.bands = { ...DEFAULT_SCORE.bands, ...saved?.score?.bands }
  return { ...DEFAULT_SETTINGS, ...saved, score }
}
