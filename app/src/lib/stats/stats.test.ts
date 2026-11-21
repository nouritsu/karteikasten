import { describe, expect, it } from 'vitest'
import type { StudyEvent } from '../engine/events'
import { replay, scheduler } from '../engine/scheduler'
import { Rating, type Grade } from '../engine/score'
import { deckWords } from '../testing'
import {
  addDays,
  analyse,
  bars,
  coverageAt,
  daysIn,
  grades,
  heatmap,
  leeches,
  priorRange,
  rankBands,
  recall,
  records,
  rhythm,
  spanRange,
  streaks,
  summary,
} from './stats'

let counter = 0
function review(word: string, ts: string, grade: Grade, score = 70, activeMs = 6000): StudyEvent {
  return {
    id: `E${String(counter++).padStart(4, '0')}`,
    type: 'review',
    word_id: word,
    ts,
    deck_version: 'v',
    app_version: 'v',
    review: { shown_at: ts, ready_at: ts, answered_at: ts, answer: grade > 1 ? 'know' : 'dont_know', undo: false, score, hints: [], active_ms: activeMs, grade },
  }
}

// Local times (no Z): learning days roll over at 04:00 local time.
const words = deckWords(4) // a#noun#1 … d#noun#1, token_share 0.01 each
const [a, b, c] = words.map((w) => w.id)
const events: StudyEvent[] = [
  review(a, '2026-11-01T09:00:00', Rating.Easy, 90),
  review(b, '2026-11-01T09:01:00', Rating.Again, 0),
  review(b, '2026-11-01T09:10:00', Rating.Good, 60),
  review(a, '2026-11-02T21:00:00', Rating.Good, 70),
  review(c, '2026-11-03T21:05:00', Rating.Hard, 30),
  review(a, '2026-11-20T21:00:00', Rating.Again, 0),
]

describe('Stats', () => {
  const analysis = analyse(events, words, 0.9)

  it('replays once, knowing each review’s prior state and each word’s first day', () => {
    expect(analysis.reviews).toHaveLength(6)
    expect(analysis.reviews.map((x) => x.prior)).toEqual(['new', 'new', 'learning', 'review', 'new', 'review'])
    expect(analysis.firstDay.get(a)).toBe('2026-11-01')
    expect(analysis.firstDay.get(c)).toBe('2026-11-03')
    expect(analysis.days).toEqual(['2026-11-01', '2026-11-02', '2026-11-03', '2026-11-20'])
  })

  it('follows the coverage day by day', () => {
    expect(coverageAt(analysis, '2026-10-31')).toBe(0)
    expect(coverageAt(analysis, '2026-11-01')).toBeCloseTo(0.01) // a by Easy; b is still in its learning steps
    expect(coverageAt(analysis, '2026-11-25')).toBeCloseTo(coverageAt(analysis, '2026-11-20'))
  })

  it('sums up a span and the span before it', () => {
    const r = spanRange('30d', null, '2026-11-21', '2026-11-01')
    expect(r).toEqual({ from: '2026-10-23', to: '2026-11-21' })
    expect(priorRange('30d', r)).toEqual({ from: '2026-09-23', to: '2026-10-22' })
    expect(priorRange('all', r)).toBeNull()
    const s = summary(analysis, r)
    expect(s.reviews).toBe(6)
    expect(s.perDay).toBeCloseTo(6 / 30)
    expect(s.average).toBeCloseTo(250 / 6)
    expect(s.newWords).toBe(3)
    expect(s.retention).toBe(0.5) // of the two reviews of cards in Review, one known
  })

  it('draws a bar a day, or a week for long spans', () => {
    const daily = bars(analysis, { from: '2026-11-01', to: '2026-11-03' })
    expect(daily.map((bar) => [bar.reviews, bar.fresh, bar.average])).toEqual([
      [3, 2, 50],
      [1, 0, 70],
      [1, 1, 30],
    ])
    const weekly = bars(analysis, { from: '2026-06-01', to: '2026-11-22' })
    expect(weekly.length).toBeLessThan(30)
    expect(weekly.reduce((sum, bar) => sum + bar.reviews, 0)).toBe(6)
  })

  it('splits answers by grade and recall by the card’s age', () => {
    const all = { from: '2026-11-01', to: '2026-11-30' }
    expect(grades(analysis, all)).toEqual({ easy: 1, good: 2, hard: 1, again: 2 })
    const r = recall(analysis, all)
    expect(r.young.total + r.mature.total).toBe(2)
  })

  it('counts known words per 500 ranks from the states', () => {
    const states = replay(events, scheduler(0.9))
    const bands = rankBands(words, states, 4, 2)
    expect(bands.map((x) => [x.from, x.to, x.total])).toEqual([
      [1, 2, 2],
      [3, 4, 2],
    ])
  })

  it('lays out twelve weeks, Monday first, today in the last column', () => {
    const grid = heatmap(analysis, '2026-11-21') // a Saturday
    expect(grid).toHaveLength(12)
    expect(grid[11][5]).toEqual({ day: '2026-11-21', reviews: 0, future: false })
    expect(grid[11][6].future).toBe(true)
    expect(grid[0][0].day).toBe(addDays('2026-11-21', -5 - 77))
  })

  it('finds streaks, rhythm and records', () => {
    expect(streaks(analysis, { from: '2026-11-01', to: '2026-11-21' })).toEqual({ best: 3, perWeek: (4 / 21) * 7 })
    const rh = rhythm(analysis, { from: '2026-11-01', to: '2026-11-21' })
    expect(rh.peak).toBe(9) // three at 09 and three at 21: the earlier hour wins a tie
    expect(rh.sittingsPerDay).toBe(1) // each day's reviews sit within half an hour
    const rec = records(analysis)
    expect(rec.streak).toEqual({ days: 3, from: '2026-11-01', to: '2026-11-03' })
    expect(rec.mostReviews).toEqual({ reviews: 3, day: '2026-11-01' })
    expect(rec.bestAverage).toBeNull() // no day with ten reviews
    expect([rec.total, rec.studiedDays, rec.since]).toEqual([6, 4, '2026-11-01'])
  })

  it('lists words forgotten after they were learnt', () => {
    const states = replay(events, scheduler(0.9))
    expect(leeches(words, states, 1).map((x) => x.word.id)).toEqual([a])
  })

  it('counts days in a range, both ends included', () => {
    expect(daysIn({ from: '2026-11-01', to: '2026-11-30' })).toBe(30)
    expect(daysIn({ from: '2026-03-28', to: '2026-03-30' })).toBe(3) // across the clock change
  })
})
