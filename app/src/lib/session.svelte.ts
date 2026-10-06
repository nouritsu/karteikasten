// One study session over the loaded words (Phase 2: no storage or scheduling yet;
// the queue simply cycles through the deck).
//
// Bereit -> Enthüllen (letter shuffle) -> Läuft (clock and score) -> Beantwortet -> Bereit

import { ActiveClock } from './engine/clock'
import { grade, score, type Grade, type Hint } from './engine/score'
import type { DeckWord } from './types'

export type Phase = 'ready' | 'reveal' | 'running' | 'answered'
export type Answer = 'know' | 'dont_know'

export interface Review {
  id: string
  score: number
  grade: Grade
  hints: Hint[]
  activeMs: number
}

export class Session {
  words = $state<DeckWord[]>([])
  index = $state(0)
  phase = $state<Phase>('ready')
  answer = $state<Answer | null>(null)
  undone = $state(false)
  hints = $state<Hint[]>([])
  now = $state(Date.now())
  reviews = $state<Review[]>([])
  known = $state<string[]>([])
  readonly startedAt = Date.now()
  #clock = new ActiveClock()
  #frozen = 0

  get word(): DeckWord | undefined {
    return this.words[this.index]
  }

  /** The score shown in the score bar: decaying while the clock runs, frozen afterwards. */
  get score(): number {
    if (this.phase === 'running') return score(this.#clock.elapsed(this.now), this.hints)
    if (this.phase === 'answered') return this.undone || this.answer === 'dont_know' ? 0 : this.#frozen
    return 100
  }

  get activeMs(): number {
    return this.#clock.elapsed(this.now)
  }

  get average(): number | null {
    if (!this.reviews.length) return null
    return Math.round(this.reviews.reduce((sum, r) => sum + r.score, 0) / this.reviews.length)
  }

  get coverage(): number {
    const known = new Set(this.known)
    return this.words.filter((w) => known.has(w.id)).reduce((sum, w) => sum + w.token_share, 0)
  }

  start(): void {
    if (this.phase === 'ready') this.phase = 'reveal'
  }

  /** The shuffle has locked its last letter: the clock starts now. */
  revealed(now: number): void {
    if (this.phase !== 'reveal') return
    this.#clock.reset()
    this.#clock.start(now)
    this.now = now
    this.phase = 'running'
  }

  /** Charges a hint once per review, and only before answering. Returns whether it cost points. */
  use(hint: Hint): boolean {
    if (this.phase !== 'running' || this.hints.includes(hint)) return false
    this.hints = [...this.hints, hint]
    return true
  }

  respond(answer: Answer, now: number): void {
    if (this.phase !== 'running') return
    this.#frozen = score(this.#clock.elapsed(now), this.hints)
    this.#clock.pause(now)
    this.now = now
    this.answer = answer
    this.phase = 'answered'
  }

  /** "war doch falsch": available after "Weiß ich" until "Weiter". */
  undo(): void {
    if (this.phase === 'answered' && this.answer === 'know') this.undone = true
  }

  next(): void {
    const word = this.word
    if (this.phase !== 'answered' || !word || !this.answer) return
    const final = this.score
    this.reviews = [
      ...this.reviews,
      { id: word.id, score: final, grade: grade(this.answer, final, this.undone), hints: this.hints, activeMs: this.activeMs },
    ]
    const knows = this.answer === 'know' && !this.undone
    this.known = knows ? [...new Set([...this.known, word.id])] : this.known.filter((id) => id !== word.id)
    this.index = (this.index + 1) % this.words.length
    this.phase = 'ready'
    this.answer = null
    this.undone = false
    this.hints = []
    this.#clock.reset()
  }

  /** The clock only counts while the page is visible. */
  visibility(hidden: boolean, now: number): void {
    if (this.phase !== 'running') return
    if (hidden) this.#clock.pause(now)
    else this.#clock.start(now)
    this.now = now
  }
}
