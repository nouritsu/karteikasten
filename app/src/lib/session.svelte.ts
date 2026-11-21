// One study session: the queue, the card flow and the events it writes
// (spec: Card flow and score; Scheduling, storage and sync).
//
// Every card: Bereit -> Enthüllen -> Läuft -> Beantwortet -> Bereit. A new word runs
// the same way (D53): its first answer is its first FSRS rating.
// Nothing left: Feierabend

import { ActiveClock } from './engine/clock'
import { dayKey, dayStart, streak } from './engine/day'
import { ulid, type ReviewDetail, type StudyEvent } from './engine/events'
import { counts, nextCard, type Pick, type QueueInput } from './engine/queue'
import { isKnown, replay, scheduler, step, type WordState } from './engine/scheduler'
import { grade, score, type Hint } from './engine/score'
import { chooseSentence } from './engine/sentence'
import type { Settings } from './store/settings'
import type { DeckWord, Sentence } from './types'

export type Phase = 'ready' | 'reveal' | 'running' | 'answered' | 'done'
export type Answer = 'know' | 'dont_know'

/** Where events go: IndexedDB in the app, an array in tests. */
export interface Sink {
  add(event: StudyEvent, state: WordState): Promise<void>
  /** The answered review, saved until Weiter closes it (null: closed). */
  pending(event: StudyEvent | null): Promise<void>
}

export interface SessionOptions {
  words: DeckWord[]
  deckVersion: string
  settings: Settings
  events: StudyEvent[]
  sink: Sink
  now?: number
}

const iso = (ms: number) => new Date(ms).toISOString()

export class Session {
  readonly words: DeckWord[]
  readonly deckVersion: string
  readonly startedAt: number
  settings = $state.raw<Settings>(undefined!)
  states = $state.raw(new Map<string, WordState>())
  pick = $state.raw<Pick | null>(null)
  phase = $state<Phase>('ready')
  answer = $state<Answer | null>(null)
  undone = $state(false)
  hints = $state<Hint[]>([])
  sentence = $state.raw<Sentence | undefined>(undefined)
  now = $state(Date.now())
  scores = $state<number[]>([]) // this session's scored reviews
  total = $state(0) // reviews all time
  daily = $state.raw(new Map<string, number>()) // reviews per learning day
  #scoreByDay = new Map<string, number>() // the reviews' scores summed per learning day
  #events: StudyEvent[] = [] // every event so far, for the coverage at the start of a day
  #coverageAtStart: [string, number] | null = null
  error = $state<string | null>(null)
  #newByDay = new Map<string, number>() // words first studied per learning day
  #clock = new ActiveClock()
  #frozen = 0
  #shownAt = 0
  #readyAt = 0
  #draft: StudyEvent | null = null
  #fsrs
  #sink: Sink

  /** Abdeckung: the share of running text the known words cover. */
  readonly coverage = $derived.by(() =>
    this.words.reduce((sum, w) => (isKnown(this.states.get(w.id)) ? sum + w.token_share : sum), 0),
  )

  constructor(options: SessionOptions) {
    this.words = [...options.words].sort((a, b) => a.rank - b.rank)
    this.deckVersion = options.deckVersion
    this.settings = options.settings
    this.#sink = options.sink
    this.#fsrs = scheduler(options.settings.retention)
    this.startedAt = options.now ?? Date.now()
    this.now = this.startedAt
    this.load(options.events, this.startedAt)
  }

  /** States and counts from every event (at start, and after an import). */
  load(events: StudyEvent[], now = Date.now()): void {
    this.states = replay(events, this.#fsrs)
    this.#events = [...events]
    this.#coverageAtStart = null
    const daily = new Map<string, number>()
    this.#scoreByDay = new Map()
    let total = 0
    for (const event of events) {
      if (event.type !== 'review') continue
      total++
      const day = dayKey(event.ts)
      daily.set(day, (daily.get(day) ?? 0) + 1)
      this.#scoreByDay.set(day, (this.#scoreByDay.get(day) ?? 0) + (event.review?.score ?? 0))
    }
    this.daily = daily
    this.total = total
    this.#countNew()
    if (this.phase === 'ready' || this.phase === 'done') this.advance(now)
  }

  /** New words per learning day, from the states. */
  #countNew(): void {
    this.#newByDay = new Map()
    for (const state of this.states.values()) {
      if (state.first) {
        const day = dayKey(state.first)
        this.#newByDay.set(day, (this.#newByDay.get(day) ?? 0) + 1)
      }
    }
  }

  // -- what the views show ------------------------------------------------------------------

  get word(): DeckWord | undefined {
    return this.pick?.word
  }

  /** The score in the score bar: decaying while the clock runs, frozen afterwards. */
  get score(): number {
    if (this.phase === 'running') return score(this.#clock.elapsed(this.now), this.hints, this.settings.score)
    if (this.phase === 'answered') return this.undone || this.answer === 'dont_know' ? 0 : this.#frozen
    return this.settings.score.start
  }

  get activeMs(): number {
    return this.#clock.elapsed(this.now)
  }

  get today(): number {
    return this.daily.get(dayKey(this.now)) ?? 0
  }

  get streak(): number {
    return streak(new Set(this.daily.keys()), dayKey(this.now))
  }

  /** Today's reviews' mean score, for Feierabend. */
  get averageToday(): number | null {
    const day = dayKey(this.now)
    const n = this.daily.get(day) ?? 0
    return n ? Math.round((this.#scoreByDay.get(day) ?? 0) / n) : null
  }

  /** Words studied for the first time today. */
  get newToday(): number {
    return this.#newByDay.get(dayKey(this.now)) ?? 0
  }

  /** The coverage as today began (04:00), from the events before it; once a day. */
  coverageAtStart(): number {
    const day = dayKey(this.now)
    if (this.#coverageAtStart?.[0] === day) return this.#coverageAtStart[1]
    const start = dayStart(this.now).toISOString()
    const before = replay(
      this.#events.filter((e) => e.ts < start),
      this.#fsrs,
    )
    const coverage = this.words.reduce((sum, w) => (isKnown(before.get(w.id)) ? sum + w.token_share : sum), 0)
    this.#coverageAtStart = [day, coverage]
    return coverage
  }

  get average(): number | null {
    if (!this.scores.length) return null
    return Math.round(this.scores.reduce((sum, s) => sum + s, 0) / this.scores.length)
  }

  /** Cards still due today, new words left today, and when the next learning card is due. */
  get counts(): { due: number; fresh: number; nextDue: Date | null } {
    return counts(this.#queue(this.now))
  }

  /** The same counts at another time, as they will be if nothing is studied till then
   *  (the study reminder, D63). */
  countsAt(at: number): { due: number; fresh: number; nextDue: Date | null } {
    return counts(this.#queue(at))
  }

  /** Reviews answered on the learning day of `at`. */
  reviewsOn(at: number): number {
    return this.daily.get(dayKey(at)) ?? 0
  }

  // -- the queue ------------------------------------------------------------------------------

  #queue(now: number, last?: string): QueueInput {
    const today = dayKey(now)
    return {
      words: this.words,
      states: this.states,
      now: new Date(now),
      n: this.settings.n ?? Infinity,
      newLeft: this.settings.newPerDay - (this.#newByDay.get(today) ?? 0),
      last,
      learnAheadMs: this.settings.learnAheadMin * 60_000,
    }
  }

  /** The next card, or Feierabend. Also called while Feierabend shows, for a learning
   *  card that has come due or a new day. */
  advance(now = Date.now(), last?: string): void {
    const pick = nextCard(this.#queue(now, last))
    this.now = now
    if (!pick) {
      this.pick = null
      this.phase = 'done'
      return
    }
    this.pick = pick
    this.phase = 'ready'
    this.answer = null
    this.undone = false
    this.hints = []
    this.#clock.reset()
    this.#draft = null
    this.#shownAt = now
    this.sentence = chooseSentence(pick.word, (id) => isKnown(this.states.get(id)))
  }

  // -- the card flow ----------------------------------------------------------------------

  start(): void {
    if (this.phase === 'ready') this.phase = 'reveal'
  }

  /** The shuffle has locked its last letter: the clock starts. */
  revealed(now: number): void {
    if (this.phase !== 'reveal') return
    this.now = now
    this.#readyAt = now
    this.#clock.reset()
    this.#clock.start(now)
    this.phase = 'running'
  }

  /** Charges a hint once per review, and only before answering. Returns whether it cost points. */
  use(hint: Hint): boolean {
    if (this.phase !== 'running' || this.hints.includes(hint)) return false
    this.hints = [...this.hints, hint]
    return true
  }

  respond(answer: Answer, now: number): void {
    if (this.phase !== 'running' || !this.word) return
    this.#frozen = score(this.#clock.elapsed(now), this.hints, this.settings.score)
    this.#clock.pause(now)
    this.now = now
    this.answer = answer
    this.phase = 'answered'
    const value = answer === 'know' ? this.#frozen : 0
    const review: ReviewDetail = {
      shown_at: iso(this.#shownAt),
      ready_at: iso(this.#readyAt),
      answered_at: iso(now),
      answer,
      undo: false,
      score: value,
      hints: [...this.hints],
      active_ms: this.#clock.elapsed(now),
      grade: grade(answer, value, false, this.settings.score),
    }
    this.#draft = this.#event('review', this.word.id, now, review)
    this.#save(this.#sink.pending(this.#draft))
  }

  /** "war doch falsch": available after "Weiß ich" until "Weiter". */
  undo(): void {
    if (this.phase !== 'answered' || this.answer !== 'know' || !this.#draft?.review) return
    this.undone = true
    this.#draft = { ...this.#draft, review: { ...this.#draft.review, undo: true, score: 0, grade: grade('know', 0, true) } }
    this.#save(this.#sink.pending(this.#draft))
  }

  /** Weiter after a review: the event is written and the next card comes up. */
  next(now = Date.now()): void {
    if (this.phase !== 'answered' || !this.#draft?.review) return
    const event = this.#draft
    this.#commit(event)
    this.#save(this.#sink.pending(null))
    this.scores = [...this.scores, event.review!.score]
    this.advance(now, event.word_id)
  }

  /** A Wörter action on a word (spec: Wörter): Kenne ich schon, Pausieren, Fortsetzen or
   *  Zurücksetzen. A card waiting at Bereit or Feierabend is picked again, since the
   *  action may have taken it out of the queue or put one in. */
  act(type: 'known' | 'suspend' | 'unsuspend' | 'reset', wordId: string, now = Date.now()): void {
    this.#commit(this.#event(type, wordId, now))
    this.#countNew()
    if (this.phase === 'ready' || this.phase === 'done') this.advance(now)
  }

  /** The clock only counts while the page is visible. */
  visibility(hidden: boolean, now: number): void {
    if (this.phase !== 'running') return
    if (hidden) this.#clock.pause(now)
    else this.#clock.start(now)
    this.now = now
  }

  // -- events -----------------------------------------------------------------------------

  #event(type: StudyEvent['type'], wordId: string, now: number, review?: ReviewDetail): StudyEvent {
    return {
      id: ulid(now),
      type,
      word_id: wordId,
      ts: iso(now),
      deck_version: this.deckVersion,
      app_version: __APP_VERSION__,
      ...(review ? { review } : {}),
    }
  }

  #commit(event: StudyEvent): void {
    this.#events.push(event)
    const before = this.states.get(event.word_id)
    const state = step(before, event, this.#fsrs)
    this.states = new Map(this.states).set(event.word_id, state)
    if (!before?.introduced && state.first) {
      const day = dayKey(state.first)
      this.#newByDay.set(day, (this.#newByDay.get(day) ?? 0) + 1)
    }
    if (event.type === 'review') {
      this.total++
      const day = dayKey(event.ts)
      this.daily = new Map(this.daily).set(day, (this.daily.get(day) ?? 0) + 1)
      this.#scoreByDay.set(day, (this.#scoreByDay.get(day) ?? 0) + (event.review?.score ?? 0))
    }
    this.#save(this.#sink.add(event, state))
  }

  #save(write: Promise<void>): void {
    write.catch((error: unknown) => (this.error = String(error)))
  }
}
