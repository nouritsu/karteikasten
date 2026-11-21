// Stats' numbers (D60): plain functions over the study events, the deck and the
// current card states. One replay of the events (`analyse`) gives each review the state
// its card was in before it, the day each word was first studied, and the coverage at the
// end of each day; the blocks then read a span of learning days from it.

import { dayKey, streak as streakFrom } from '../engine/day'
import { byTime, type StudyEvent } from '../engine/events'
import { isKnown, scheduler, State, step, type WordState } from '../engine/scheduler'
import type { DeckWord } from '../types'
import type { DayRange, Span } from './panes'

/** A card is young while its stability is under this many days, mature after (Recall). */
export const MATURE_DAYS = 21

export interface ReviewRecord {
  ts: number
  day: string
  hour: number
  score: number
  grade: number // 1 Again, 2 Hard, 3 Good, 4 Easy
  activeMs: number
  wordId: string
  prior: 'new' | 'learning' | 'review' // the card's state before the review
  young: boolean // before the review, a card in Review with stability under MATURE_DAYS
}

export interface Analysis {
  reviews: ReviewRecord[] // in time order
  firstDay: Map<string, string> // word id → the learning day it was first studied
  coverageByDay: [string, number][] // the coverage at the end of each day with events, in order
  days: string[] // learning days with at least one review, in order
}

const known = (state: WordState | undefined) => (isKnown(state) ? 1 : 0)

/** Replays every event once (spec: Scheduling), keeping what the blocks need. */
export function analyse(events: readonly StudyEvent[], words: readonly DeckWord[], retention: number): Analysis {
  const f = scheduler(retention)
  const share = new Map(words.map((w) => [w.id, w.token_share]))
  const states = new Map<string, WordState>()
  const reviews: ReviewRecord[] = []
  const firstDay = new Map<string, string>()
  const coverageByDay: [string, number][] = []
  const days: string[] = []
  let coverage = 0
  for (const event of [...events].sort(byTime)) {
    const before = states.get(event.word_id)
    const after = step(before, event, f)
    states.set(event.word_id, after)
    const day = dayKey(event.ts)
    if (after.first && !firstDay.has(event.word_id)) firstDay.set(event.word_id, dayKey(after.first))
    coverage += (known(after) - known(before)) * (share.get(event.word_id) ?? 0)
    if (coverageByDay.at(-1)?.[0] === day) coverageByDay[coverageByDay.length - 1][1] = coverage
    else coverageByDay.push([day, coverage])
    if (event.type !== 'review' || !event.review) continue
    if (days.at(-1) !== day) days.push(day)
    const card = before?.card
    const prior = !card || card.state === State.New ? 'new' : card.state === State.Review ? 'review' : 'learning'
    const at = new Date(event.ts)
    reviews.push({
      ts: at.getTime(),
      day,
      hour: at.getHours(),
      score: event.review.score,
      grade: event.review.grade,
      activeMs: event.review.active_ms,
      wordId: event.word_id,
      prior,
      young: prior === 'review' && card!.stability < MATURE_DAYS,
    })
  }
  return { reviews, firstDay, coverageByDay, days }
}

// Days ---------------------------------------------------------------------------------

const parse = (day: string) => {
  const [y, m, d] = day.split('-').map(Number)
  return new Date(y, m - 1, d)
}
const pad = (n: number) => String(n).padStart(2, '0')
const keyOf = (date: Date) => `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`

/** The learning day `n` days after `day` (before, for a negative n). */
export function addDays(day: string, n: number): string {
  const date = parse(day)
  date.setDate(date.getDate() + n)
  return keyOf(date)
}

/** Days from `from` to `to`, both counted. */
export const daysIn = (r: DayRange): number => Math.round((parse(r.to).getTime() - parse(r.from).getTime()) / 86_400_000) + 1

export function eachDay(r: DayRange): string[] {
  const out: string[] = []
  for (let day = r.from; day <= r.to; day = addDays(day, 1)) out.push(day)
  return out
}

/** Weekday of a day, 0 Monday … 6 Sunday. */
export const weekday = (day: string): number => (parse(day).getDay() + 6) % 7

/** The days a span covers, ending today; all time starts at the first review. */
export function spanRange(span: Span, picked: DayRange | null, today: string, first: string | undefined): DayRange {
  switch (span) {
    case '30d':
      return { from: addDays(today, -29), to: today }
    case '90d':
      return { from: addDays(today, -89), to: today }
    case '1y':
      return { from: addDays(today, -364), to: today }
    case 'all':
      return { from: first && first < today ? first : today, to: today }
    case 'range':
      return picked && picked.from <= picked.to ? picked : { from: addDays(today, -29), to: today }
  }
}

/** The span of the same length just before, to compare against; none for all time. */
export const priorRange = (span: Span, r: DayRange): DayRange | null =>
  span === 'all' ? null : { from: addDays(r.from, -daysIn(r)), to: addDays(r.from, -1) }

const inRange = (day: string, r: DayRange) => day >= r.from && day <= r.to

// Overview ---------------------------------------------------------------------------------

export interface Summary {
  reviews: number
  perDay: number // over every day of the span, studied or not
  average: number | null // the reviews' mean score
  newWords: number
  retention: number | null // Weiß ich among reviews of cards in Review
}

export function summary(a: Analysis, r: DayRange): Summary {
  const reviews = a.reviews.filter((x) => inRange(x.day, r))
  const recalled = reviews.filter((x) => x.prior === 'review')
  let newWords = 0
  for (const day of a.firstDay.values()) if (inRange(day, r)) newWords++
  return {
    reviews: reviews.length,
    perDay: reviews.length / daysIn(r),
    average: reviews.length ? reviews.reduce((sum, x) => sum + x.score, 0) / reviews.length : null,
    newWords,
    retention: recalled.length ? recalled.filter((x) => x.grade > 1).length / recalled.length : null,
  }
}

// History and Score -----------------------------------------------------------------------

export interface Bar {
  from: string // the first day it covers
  to: string
  reviews: number
  fresh: number // of them, words studied for the first time
  average: number | null
}

/** A bar a day, or a week once the span is longer than `maxBars` days. */
export function bars(a: Analysis, r: DayRange, maxBars = 92): Bar[] {
  const days = eachDay(r)
  const week = days.length > maxBars
  const out: Bar[] = []
  const index = new Map<string, Bar>()
  for (const day of days) {
    const start = week ? addDays(day, -weekday(day)) : day
    let bar = index.get(start)
    if (!bar) {
      bar = { from: start < r.from ? r.from : start, to: day, reviews: 0, fresh: 0, average: null }
      index.set(start, bar)
      out.push(bar)
    }
    bar.to = day
  }
  const sums = new Map<Bar, number>()
  const keyFor = (day: string) => (week ? addDays(day, -weekday(day)) : day)
  for (const x of a.reviews) {
    if (!inRange(x.day, r)) continue
    const bar = index.get(keyFor(x.day))!
    bar.reviews++
    sums.set(bar, (sums.get(bar) ?? 0) + x.score)
    if (x.prior === 'new') bar.fresh++
  }
  for (const bar of out) bar.average = bar.reviews ? Math.round(sums.get(bar)! / bar.reviews) : null
  return out
}

/** Answers by grade: Weiß ich in its bands (Easy, Good, Hard), and Weiß ich nicht. */
export function grades(a: Analysis, r: DayRange): { easy: number; good: number; hard: number; again: number } {
  const g = { easy: 0, good: 0, hard: 0, again: 0 }
  for (const x of a.reviews) {
    if (!inRange(x.day, r)) continue
    if (x.grade === 4) g.easy++
    else if (x.grade === 3) g.good++
    else if (x.grade === 2) g.hard++
    else g.again++
  }
  return g
}

// Recall ------------------------------------------------------------------------------

export interface Recall {
  known: number
  total: number
}

export function recall(a: Analysis, r: DayRange): { young: Recall; mature: Recall } {
  const young = { known: 0, total: 0 }
  const mature = { known: 0, total: 0 }
  for (const x of a.reviews) {
    if (!inRange(x.day, r) || x.prior !== 'review') continue
    const group = x.young ? young : mature
    group.total++
    if (x.grade > 1) group.known++
  }
  return { young, mature }
}

// Coverage ---------------------------------------------------------------------------

export interface RankBand {
  from: number
  to: number
  known: number
  total: number
}

/** Known words per 500 ranks up to `n`, from the current states. */
export function rankBands(words: readonly DeckWord[], states: ReadonlyMap<string, WordState>, n: number, size = 500): RankBand[] {
  const out: RankBand[] = []
  for (const word of words) {
    if (word.rank > n) continue
    const i = Math.floor((word.rank - 1) / size)
    out[i] ??= { from: i * size + 1, to: Math.min(n, (i + 1) * size), known: 0, total: 0 }
    out[i].total++
    if (isKnown(states.get(word.id))) out[i].known++
  }
  return out.filter(Boolean)
}

/** The coverage at the end of `day`: the last day with events up to it, else none. */
export function coverageAt(a: Analysis, day: string): number {
  let found = 0
  for (const [d, coverage] of a.coverageByDay) {
    if (d > day) break
    found = coverage
  }
  return found
}

// Days ----------------------------------------------------------------------------------

export interface DayCell {
  day: string
  reviews: number
  future: boolean
}

/** The last `weeks` weeks, Monday to Sunday, as columns of seven days; today's week last. */
export function heatmap(a: Analysis, today: string, weeks = 12): DayCell[][] {
  const counts = new Map<string, number>()
  for (const x of a.reviews) counts.set(x.day, (counts.get(x.day) ?? 0) + 1)
  const monday = addDays(today, -weekday(today) - 7 * (weeks - 1))
  return Array.from({ length: weeks }, (_, w) =>
    Array.from({ length: 7 }, (_, d) => {
      const day = addDays(monday, 7 * w + d)
      return { day, reviews: counts.get(day) ?? 0, future: day > today }
    }),
  )
}

/** The longest run of studied days within the span, and how many days a week were studied. */
export function streaks(a: Analysis, r: DayRange): { best: number; perWeek: number } {
  let best = 0
  let run = 0
  let last = ''
  let studied = 0
  for (const day of a.days) {
    if (!inRange(day, r)) continue
    studied++
    run = last && addDays(last, 1) === day ? run + 1 : 1
    best = Math.max(best, run)
    last = day
  }
  return { best, perWeek: (studied / daysIn(r)) * 7 }
}

export const currentStreak = (a: Analysis, today: string): number => streakFrom(new Set(a.days), today)

// Rhythm ------------------------------------------------------------------------------

const SESSION_GAP_MS = 30 * 60_000 // reviews further apart start a new sitting

export interface Rhythm {
  hours: number[] // reviews in each hour of the day
  peak: number | null // the busiest hour
  minutesPerDay: number | null // active minutes per studied day
  sittingsPerDay: number | null
}

export function rhythm(a: Analysis, r: DayRange): Rhythm {
  const hours = Array<number>(24).fill(0)
  let active = 0
  let sittings = 0
  let previous = -Infinity
  const studied = new Set<string>()
  for (const x of a.reviews) {
    if (!inRange(x.day, r)) continue
    hours[x.hour]++
    active += x.activeMs
    if (x.ts - previous > SESSION_GAP_MS) sittings++
    previous = x.ts
    studied.add(x.day)
  }
  const top = Math.max(...hours)
  return {
    hours,
    peak: top ? hours.indexOf(top) : null,
    minutesPerDay: studied.size ? active / 60_000 / studied.size : null,
    sittingsPerDay: studied.size ? sittings / studied.size : null,
  }
}

// Records (all time) ------------------------------------------------------------------------

export interface Records {
  streak: { days: number; from: string; to: string } | null
  mostReviews: { reviews: number; day: string } | null
  bestAverage: { average: number; day: string } | null // over days with at least MIN_DAY reviews
  total: number
  studiedDays: number
  since: string | null
}

const MIN_DAY = 10

export function records(a: Analysis): Records {
  const perDay = new Map<string, { n: number; sum: number }>()
  for (const x of a.reviews) {
    const d = perDay.get(x.day) ?? { n: 0, sum: 0 }
    d.n++
    d.sum += x.score
    perDay.set(x.day, d)
  }
  let streak: Records['streak'] = null
  let runFrom = ''
  let last = ''
  for (const day of a.days) {
    if (!last || addDays(last, 1) !== day) runFrom = day
    const days = daysIn({ from: runFrom, to: day })
    if (!streak || days > streak.days) streak = { days, from: runFrom, to: day }
    last = day
  }
  let mostReviews: Records['mostReviews'] = null
  let bestAverage: Records['bestAverage'] = null
  for (const [day, { n, sum }] of perDay) {
    if (!mostReviews || n > mostReviews.reviews) mostReviews = { reviews: n, day }
    const average = sum / n
    if (n >= MIN_DAY && (!bestAverage || average > bestAverage.average)) bestAverage = { average, day }
  }
  return { streak, mostReviews, bestAverage, total: a.reviews.length, studiedDays: a.days.length, since: a.days[0] ?? null }
}

// Trouble words (all time) ------------------------------------------------------------------

/** Words forgotten after they were learnt, most lapses first: FSRS counts each Again on a
 *  card in Review as a lapse. */
export function leeches(words: readonly DeckWord[], states: ReadonlyMap<string, WordState>, min = 2, count = 10) {
  return words
    .map((word) => ({ word, lapses: states.get(word.id)?.card.lapses ?? 0 }))
    .filter((x) => x.lapses >= min)
    .sort((x, y) => y.lapses - x.lapses || x.word.rank - y.word.rank)
    .slice(0, count)
}
