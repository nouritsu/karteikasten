import { describe, expect, it } from 'vitest'
import type { StudyEvent } from './engine/events'
import { State } from './engine/scheduler'
import { Rating } from './engine/score'
import { Session, type Sink } from './session.svelte'
import { DEFAULT_SETTINGS, type Settings } from './store/settings'
import { deckWord, deckWords } from './testing'

const T0 = new Date('2026-10-10T10:00:00').getTime()

class Recorder implements Sink {
  events: StudyEvent[] = []
  open: StudyEvent | null = null
  async add(event: StudyEvent) {
    this.events.push(event)
  }
  async pending(event: StudyEvent | null) {
    this.open = event
  }
}

function session(events: StudyEvent[] = [], settings: Partial<Settings> = {}, words = 6, now = T0) {
  const sink = new Recorder()
  const s = new Session({ words: deckWords(words), deckVersion: 'v1', settings: { ...DEFAULT_SETTINGS, ...settings }, events, sink, now })
  return { s, sink }
}

/** Bereit -> Enthüllen -> Läuft at time `at`. */
function open(s: Session, at: number) {
  s.start()
  s.revealed(at)
}

/** One card answered and closed with Weiter. */
function answer(s: Session, how: 'know' | 'dont_know', at: number) {
  open(s, at)
  s.respond(how, at + 1000)
  s.next(at + 2000)
}

describe('new words (D53)', () => {
  it('run like reviews: word only, scored, and the answer is their first rating', () => {
    const { s, sink } = session()
    expect(s.phase).toBe('ready')
    expect(s.word?.lemma).toBe('a')
    expect(s.pick?.kind).toBe('new')
    open(s, T0)
    expect(s.phase).toBe('running')
    expect(s.use('sentence')).toBe(true) // hints cost points, as on any card
    s.respond('know', T0 + 1000)
    expect(s.phase).toBe('answered')
    s.next(T0 + 2000)
    expect(sink.events.map((e) => [e.type, e.review?.grade])).toEqual([['review', Rating.Good]]) // 80 with Satz
    expect(s.states.get('a#noun#1')!.introduced).toBe(true)
    expect(s.word?.lemma).toBe('b')
  })

  it('finish a known word in one card and bring an unknown one back in minutes', () => {
    const { s } = session([], {}, 3)
    answer(s, 'know', T0) // a: Easy, a review in days
    expect(s.states.get('a#noun#1')!.card.state).toBe(State.Review)
    expect(s.coverage).toBeCloseTo(0.01)
    answer(s, 'dont_know', T0 + 10_000) // b: Again, learning
    expect(s.states.get('b#noun#1')!.card.state).toBe(State.Learning)
    expect(s.word?.lemma).toBe('c')
    answer(s, 'know', T0 + 20_000)
    // nothing new left: b comes back early, within the learn-ahead window
    expect(s.pick).toMatchObject({ kind: 'early', word: { lemma: 'b' } })
  })

  it('stop at the daily limit and start again after 04:00', () => {
    const { s } = session([], { newPerDay: 2 }, 6)
    answer(s, 'know', T0)
    answer(s, 'know', T0 + 10_000)
    expect(s.phase).toBe('done')
    expect(s.counts.fresh).toBe(0)
    const tomorrow = new Date('2026-10-11T04:00:00').getTime()
    s.advance(tomorrow)
    expect(s.phase).toBe('ready')
    expect(s.word?.lemma).toBe('c')
  })
})

describe('reviews', () => {
  // a went through an Intro before D53: its first scored check is due straight away.
  const introduced: StudyEvent[] = [
    { id: '01', type: 'intro', word_id: 'a#noun#1', ts: '2026-10-09T10:00:00.000Z', deck_version: 'v1', app_version: '0' },
  ]

  it('freezes the score on Weiß ich, grades it and writes the event on Weiter', () => {
    const { s, sink } = session(introduced, { newPerDay: 0 })
    expect(s.word?.lemma).toBe('a')
    open(s, T0)
    s.respond('know', T0 + 5000) // 3 s past the grace period: two steps
    s.now = T0 + 60_000
    expect(s.score).toBe(90)
    expect(sink.open?.review).toMatchObject({ score: 90, grade: Rating.Easy, undo: false }) // saved until Weiter
    s.next(T0 + 61_000)
    expect(sink.open).toBeNull()
    const review = sink.events.at(-1)!
    expect(review).toMatchObject({ type: 'review', word_id: 'a#noun#1', deck_version: 'v1' })
    expect(review.review).toMatchObject({ answer: 'know', score: 90, grade: Rating.Easy, active_ms: 5000 })
    expect(s.today).toBe(1)
    expect(s.total).toBe(1)
    expect(s.average).toBe(90)
    expect(s.streak).toBe(1)
  })

  it('charges hints once and only while running', () => {
    const { s } = session(introduced, { newPerDay: 0 })
    expect(s.use('audio')).toBe(false)
    open(s, T0)
    expect(s.use('audio')).toBe(true)
    expect(s.use('audio')).toBe(false)
    s.now = T0
    expect(s.score).toBe(90)
    s.respond('know', T0)
    expect(s.use('cognate')).toBe(false)
  })

  it('makes Weiß ich nicht and war doch falsch score 0 and Again', () => {
    const both: StudyEvent[] = [...introduced, { ...introduced[0], id: '02', word_id: 'b#noun#1' }]
    const { s, sink } = session(both, { newPerDay: 0 })
    open(s, T0)
    s.respond('dont_know', T0 + 1000)
    expect(s.score).toBe(0)
    s.next(T0 + 2000)
    open(s, T0 + 3000)
    s.respond('know', T0 + 4000)
    expect(s.score).toBe(100)
    s.undo()
    expect(s.score).toBe(0)
    expect(sink.open?.review).toMatchObject({ undo: true, score: 0, grade: Rating.Again })
    s.next(T0 + 5000)
    expect(sink.events.slice(-2).map((e) => [e.review!.grade, e.review!.undo])).toEqual([
      [Rating.Again, false],
      [Rating.Again, true],
    ])
  })

  it('pauses the clock while the page is hidden', () => {
    const { s, sink } = session(introduced, { newPerDay: 0 })
    open(s, T0)
    s.visibility(true, T0 + 3000)
    s.visibility(false, T0 + 600_000)
    s.respond('know', T0 + 601_000)
    expect(s.activeMs).toBe(4000)
    expect(s.score).toBe(95) // 4 s active: one step past the grace period, not 600 s of decay
    expect(sink.open?.review?.active_ms).toBe(4000)
  })

  it('brings a lapsed card back once it is due', () => {
    const { s } = session(introduced, { newPerDay: 0, learnAheadMin: 0 })
    open(s, T0)
    s.respond('dont_know', T0 + 1000)
    s.next(T0 + 2000)
    expect(s.phase).toBe('done')
    expect(s.counts.due).toBe(1)
    const due = s.counts.nextDue!.getTime()
    s.advance(due)
    expect(s.phase).toBe('ready')
    expect(s.pick?.kind).toBe('learning')
  })

  it('replays the same state from the events it wrote', () => {
    const { s, sink } = session(introduced, { newPerDay: 3 })
    for (let i = 0; i < 6 && s.phase !== 'done'; i++) answer(s, i % 2 ? 'know' : 'dont_know', T0 + i * 10_000)
    const again = session([...introduced, ...sink.events], { newPerDay: 3 }).s
    expect(again.states).toEqual(s.states)
    expect(again.total).toBe(s.total)
  })
})

describe('level (D67)', () => {
  const words = [deckWord('x#noun#1', 50), deckWord('y#noun#1', 99), deckWord('z#noun#1', 150), deckWord('w#noun#1', 300)]
  const levelSession = (settings: Partial<Settings>) =>
    new Session({ words, deckVersion: 'v1', settings: { ...DEFAULT_SETTINGS, ...settings }, events: [], sink: new Recorder(), now: T0 })

  it('checks words up to the level under their own limit, and starts new words after it', () => {
    const s = levelSession({ level: 'a1.1', checksPerDay: 1, newPerDay: 1 })
    expect(s.counts.fresh).toBe(2) // one check and one new word left today
    expect([s.pick?.kind, s.word?.lemma]).toEqual(['level', 'x'])
    answer(s, 'know', T0)
    expect([s.pick?.kind, s.word?.lemma]).toEqual(['new', 'z']) // the day's check is used; y waits
    answer(s, 'know', T0 + 10_000)
    expect(s.phase).toBe('done')
  })

  it('runs as before at Beginner', () => {
    const s = levelSession({ level: 'beginner', newPerDay: 15 })
    expect([s.pick?.kind, s.word?.lemma]).toEqual(['new', 'x'])
  })

  it('suggests the next level once the checks went well', () => {
    const many = deckWords(55)
    const events = many.slice(0, 50).map((w, i) => {
      const ts = new Date(T0 - 86_400_000 + i * 60_000).toISOString()
      const review = { shown_at: ts, ready_at: ts, answered_at: ts, answer: 'know' as const, undo: false, score: 100, hints: [], active_ms: 1000, grade: Rating.Easy }
      return { id: `L${String(i).padStart(3, '0')}`, type: 'review' as const, word_id: w.id, ts, deck_version: 'v1', app_version: 'v', review }
    })
    const s = new Session({ words: many, deckVersion: 'v1', settings: { ...DEFAULT_SETTINGS, level: 'a1.1' }, events, sink: new Recorder(), now: T0 })
    expect(s.levelNudge()).toMatchObject({ known: 50, total: 50, next: { id: 'a1.2' } })
    s.settings = { ...s.settings, level: 'beginner' }
    expect(s.levelNudge()).toMatchObject({ next: { id: 'a1.1' } }) // from Beginner too
    s.settings = { ...s.settings, level: 'b1.2' }
    expect(s.levelNudge()).toBeNull() // nothing above
  })
})
