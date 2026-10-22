import { describe, expect, it } from 'vitest'
import { deckWord, deckWords, sentence } from '../testing'
import { dayKey, dayStart, nextRollover, streak } from './day'
import { byTime, ulid, type StudyEvent } from './events'
import { counts, nextCard, type QueueInput } from './queue'
import { isKnown, replay, scheduler, State, step, type WordState } from './scheduler'
import { Rating, type Grade } from './score'
import { chooseSentence } from './sentence'

const at = (text: string) => new Date(text)

describe('learning day', () => {
  it('rolls over at 04:00 local time', () => {
    expect(dayKey(at('2026-10-22T03:59:00'))).toBe('2026-10-21')
    expect(dayKey(at('2026-10-22T04:00:00'))).toBe('2026-10-22')
    expect(dayStart(at('2026-10-22T01:00:00'))).toEqual(at('2026-10-21T04:00:00'))
    expect(nextRollover(at('2026-10-22T23:00:00'))).toEqual(at('2026-10-23T04:00:00'))
  })

  it('counts a streak back from today, or from yesterday while today is empty', () => {
    const days = new Set(['2026-10-19', '2026-10-20', '2026-10-21'])
    expect(streak(days, '2026-10-21')).toBe(3)
    expect(streak(days, '2026-10-22')).toBe(3)
    expect(streak(days, '2026-10-23')).toBe(0)
    expect(streak(new Set(['2026-02-28', '2026-03-01']), '2026-03-01')).toBe(2)
  })
})

describe('ulid', () => {
  it('starts with the time, so ids sort by creation', () => {
    const a = ulid(1_700_000_000_000, (b) => b.fill(0))
    const b = ulid(1_700_000_000_001, (b) => b.fill(255))
    expect(a).toHaveLength(26)
    expect(a < b).toBe(true)
    expect(a.slice(10)).toBe('0'.repeat(16))
  })
})

let counter = 0
function event(type: StudyEvent['type'], word: string, ts: string, grade?: Grade): StudyEvent {
  const review = grade
    ? { shown_at: ts, ready_at: ts, answered_at: ts, answer: 'know' as const, undo: false, score: 0, hints: [],
        active_ms: 0, grade }
    : undefined
  return { id: `E${String(counter++).padStart(4, '0')}`, type, word_id: word, ts, deck_version: 'v', app_version: 'v',
    ...(review ? { review } : {}) }
}

describe('scheduler', () => {
  const f = scheduler()

  it('equals a full replay when applied one event at a time', () => {
    const events = [
      event('intro', 'a', '2026-10-01T08:00:00.000Z'),
      event('review', 'a', '2026-10-01T08:05:00.000Z', Rating.Good),
      event('known', 'b', '2026-10-01T08:06:00.000Z'),
      event('review', 'a', '2026-10-01T08:20:00.000Z', Rating.Good),
      event('review', 'a', '2026-10-04T09:00:00.000Z', Rating.Again),
      event('suspend', 'b', '2026-10-05T09:00:00.000Z'),
      event('reset', 'c', '2026-10-05T09:00:00.000Z'),
    ]
    const incremental = new Map<string, WordState>()
    for (const e of events) incremental.set(e.word_id, step(incremental.get(e.word_id), e, f))
    expect(replay([...events].reverse(), f)).toEqual(incremental) // replay sorts by time
    expect(replay(events, f)).toEqual(replay(events, f)) // and fuzz is seeded: same events, same dates
  })

  it('makes Kenne ich schon a first Easy rating', () => {
    const states = replay([event('known', 'b', '2026-10-01T08:00:00.000Z')], f)
    expect(states.get('b')!.card.state).toBe(State.Review)
    expect(states.get('b')!.card.reps).toBe(1)
    expect(isKnown(states.get('b'))).toBe(true)
  })

  it('resets to a new card and keeps suspension separate', () => {
    const events = [event('known', 'b', '2026-10-01T08:00:00.000Z'), event('suspend', 'b', '2026-10-02T08:00:00.000Z')]
    const suspended = replay(events, f).get('b')!
    expect(suspended.suspended).toBe(true)
    expect(suspended.card.state).toBe(State.Review)
    const reset = replay([...events, event('reset', 'b', '2026-10-03T08:00:00.000Z')], f).get('b')!
    expect(reset).toMatchObject({ introduced: false, suspended: false, first: null })
    expect(reset.card.state).toBe(State.New)
  })

  it('orders events by time, then id', () => {
    const a = { ...event('intro', 'a', '2026-10-01T08:00:00.000Z'), id: 'B' }
    const b = { ...event('intro', 'a', '2026-10-01T08:00:00.000Z'), id: 'A' }
    expect([a, b].sort(byTime).map((e) => e.id)).toEqual(['A', 'B'])
  })
})

describe('queue', () => {
  const f = scheduler()
  const words = deckWords(8) // a … h
  const id = (letter: string) => `${letter}#noun#1`
  const now = at('2026-10-10T10:00:00')
  const base = (states: Map<string, WordState>, extra: Partial<QueueInput> = {}): QueueInput => ({
    words, states, now, n: Infinity, newLeft: 15, learnAheadMs: 20 * 60_000, ...extra,
  })

  function states(events: StudyEvent[]) {
    return replay(events, f)
  }

  it('takes learning cards due now, then reviews oldest first, then new words by rank', () => {
    const s = states([
      // c and d: reviews overdue, c the older; all times local, like `now`
      event('known', id('c'), '2026-09-01T08:00:00'),
      event('known', id('d'), '2026-09-15T08:00:00'),
      // e: relearning, due a minute after its lapse
      event('known', id('e'), '2026-09-01T08:00:00'),
      event('review', id('e'), '2026-10-10T09:40:00', Rating.Again),
    ])
    const picks: string[] = []
    let current = new Map(s)
    for (let i = 0; i < 4; i++) {
      const pick = nextCard(base(current))!
      picks.push(`${pick.kind}:${pick.word.lemma}`)
      // pretend it was answered well: move it out of today
      current = new Map(current).set(pick.word.id, step(current.get(pick.word.id), event('known', pick.word.id, '2026-10-10T10:00:00'), f))
      current.get(pick.word.id)!.card.due = at('2026-12-01T00:00:00')
    }
    expect(picks).toEqual(['learning:e', 'review:c', 'review:d', 'new:a'])
  })

  it('stops new words at the daily limit and counts what is left', () => {
    const s = states([event('known', id('c'), '2026-09-01T08:00:00')])
    expect(nextCard(base(s, { newLeft: 0 }))!.kind).toBe('review')
    expect(counts(base(s, { newLeft: 2 }))).toMatchObject({ due: 1, fresh: 2 })
    expect(counts(base(new Map(), { newLeft: 15, n: 5 })).fresh).toBe(5) // only the top n
  })

  it('takes words left from an Intro (before D53) first, as checks', () => {
    const s = states([event('intro', id('c'), '2026-10-10T09:59:00')])
    expect(nextCard(base(s))).toMatchObject({ kind: 'check', word: { lemma: 'c' } })
    expect(counts(base(s, { newLeft: 0 })).due).toBe(1)
  })

  it('shows a learning card early only when nothing else is left, within the window', () => {
    const lapse = [event('known', id('a'), '2026-09-01T08:00:00'), event('review', id('a'), '2026-10-10T09:59:00', Rating.Again)]
    const s = states(lapse) // due 10 minutes after the lapse
    expect(nextCard(base(s))!.kind).toBe('new')
    expect(nextCard(base(s, { newLeft: 0 }))).toMatchObject({ kind: 'early', word: { lemma: 'a' } })
    expect(nextCard(base(s, { newLeft: 0, learnAheadMs: 0 }))).toBeNull()
    expect(counts(base(s, { newLeft: 0, learnAheadMs: 0 })).nextDue).toEqual(s.get(id('a'))!.card.due)
  })

  it('does not repeat the card just finished while another is there', () => {
    const s = states([event('intro', id('a'), '2026-10-10T09:00:00'), event('intro', id('b'), '2026-10-10T09:00:00')])
    expect(nextCard(base(s, { last: id('a'), newLeft: 0 }))!.word.lemma).toBe('b')
    expect(nextCard(base(states([event('intro', id('a'), '2026-10-10T09:00:00')]), { last: id('a'), newLeft: 0 }))!.word.lemma).toBe('a')
  })

  it('skips suspended words', () => {
    const s = states([event('suspend', id('a'), '2026-10-10T09:00:00')])
    expect(nextCard(base(s))!.word.lemma).toBe('b')
  })
})

describe('sentence choice', () => {
  it('prefers the sentence with the most known words, then fewer unknown ones, then deck order', () => {
    const word = deckWord('Hand#noun#1', 1, {
      sentences: [
        sentence('first', ['Hand#noun#1', 'x#noun#1', 'y#noun#1']),
        sentence('known', ['Hand#noun#1', 'ich#pron#1', 'x#noun#1'], 2),
        sentence('shorter', ['Hand#noun#1', 'ich#pron#1'], 1),
      ],
    })
    expect(chooseSentence(word, () => false)!.id).toBe('first') // the word itself never counts
    expect(chooseSentence(word, (id) => id === 'ich#pron#1')!.id).toBe('shorter')
    expect(chooseSentence(deckWord('a#noun#1', 1), () => true)).toBeUndefined()
  })
})
