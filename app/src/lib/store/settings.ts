// Settings, kept in IndexedDB and in every export; Options edits them. Language and
// theme stay in localStorage, which index.html reads before the first paint, as do
// copies of the colours and the text's size and motion.

import { DEFAULT_COLORS, toColors, type Colors } from '../colors'
import { CLOCKS, SWITCHABLE, TEXT_SIZES, type Clock, type Switchable, type TextSize } from '../display'
import { LEVEL_IDS, type LevelId } from '../engine/level'
import { DEFAULT_SCORE, type ScoreSettings } from '../engine/score'
import { SPANS, STAT_PANES, toOrder, toSubset, type DayRange, type Span, type StatPane } from '../stats/panes'

/** The study reminder (D63): at `at` minutes after midnight, on days with cards due. */
export interface Reminder {
  on: boolean
  at: number
}

/** Exports (D62): one file replaced each time instead of one a day, and exports on a
 *  schedule, a calendar event in systemd's OnCalendar notation. */
export interface ExportPlan {
  oneFile: boolean
  scheduled: boolean
  calendar: string
}

export interface Settings {
  newPerDay: number
  n: number | null // study the top n words; null means the whole deck (its n_max)
  retention: number // FSRS desired retention
  score: ScoreSettings
  audioAfterAnswer: boolean
  learnAheadMin: number // with nothing else left, a learning card due this soon comes early
  level: LevelId // D67: words up to its rank come as checks, and new words start after it
  checksPerDay: number
  // Display (D59)
  textSize: TextSize
  motion: Switchable
  haptics: Switchable
  clock: Clock
  colors: Colors // D58
  reminder: Reminder
  exports: ExportPlan
  cloudBackup: boolean // Android's cloud backup of the app's data (D62); a direct transfer works either way
  // Stats (D60)
  statsSpan: Span
  statsRange: DayRange | null
  statsPanes: StatPane[]
  hiddenStats: StatPane[]
}

export const DEFAULT_SETTINGS: Settings = {
  newPerDay: 15,
  n: null,
  retention: 0.9,
  score: DEFAULT_SCORE,
  audioAfterAnswer: true,
  learnAheadMin: 20,
  level: 'beginner',
  checksPerDay: 20,
  textSize: 'system',
  motion: 'system',
  haptics: 'system',
  clock: 'system',
  colors: DEFAULT_COLORS,
  reminder: { on: false, at: 19 * 60 },
  exports: { oneFile: false, scheduled: false, calendar: '*-*-* 22:00' },
  cloudBackup: false,
  statsSpan: '30d',
  statsRange: null,
  statsPanes: [...STAT_PANES],
  hiddenStats: [],
}

const oneOf = <T extends string>(v: unknown, all: readonly T[], fallback: T): T => (all.includes(v as T) ? (v as T) : fallback)

const isDay = (v: unknown): v is string => typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v)

/** Saved settings over the defaults, so a setting added later gets its default and a
 *  value this version cannot read falls back to it. */
export function withDefaults(saved: Partial<Settings> | undefined): Settings {
  const s = (saved ?? {}) as Partial<Record<keyof Settings, unknown>>
  const score = { ...DEFAULT_SCORE, ...(s.score as Partial<ScoreSettings> | undefined) }
  score.penalties = { ...DEFAULT_SCORE.penalties, ...(s.score as Partial<ScoreSettings> | undefined)?.penalties }
  score.bands = { ...DEFAULT_SCORE.bands, ...(s.score as Partial<ScoreSettings> | undefined)?.bands }
  const reminder = { ...DEFAULT_SETTINGS.reminder, ...(s.reminder as Partial<Reminder> | undefined) }
  const exports = { ...DEFAULT_SETTINGS.exports, ...(s.exports as Partial<ExportPlan> | undefined) }
  const range = s.statsRange as Partial<DayRange> | null | undefined
  // Haptics was on or off before D59: on now follows the phone.
  const haptics = typeof s.haptics === 'boolean' ? (s.haptics ? 'system' : 'off') : oneOf(s.haptics, SWITCHABLE, 'system')
  return {
    ...DEFAULT_SETTINGS,
    ...(saved as Partial<Settings>),
    score,
    level: oneOf(s.level, LEVEL_IDS, 'beginner'),
    checksPerDay: typeof s.checksPerDay === 'number' ? s.checksPerDay : DEFAULT_SETTINGS.checksPerDay,
    textSize: oneOf(s.textSize, TEXT_SIZES, 'system'),
    motion: oneOf(s.motion, SWITCHABLE, 'system'),
    haptics,
    clock: oneOf(s.clock, CLOCKS, 'system'),
    colors: toColors(s.colors),
    reminder,
    exports,
    cloudBackup: s.cloudBackup === true,
    statsSpan: oneOf(s.statsSpan, SPANS, '30d'),
    statsRange: range && isDay(range.from) && isDay(range.to) ? { from: range.from, to: range.to } : null,
    statsPanes: toOrder(s.statsPanes, STAT_PANES),
    hiddenStats: toSubset(s.hiddenStats, STAT_PANES),
  }
}
