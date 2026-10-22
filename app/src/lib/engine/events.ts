// Study events (spec: Scheduling, storage and sync). They are append-only: card
// state is derived from them, and an import merges them by id.

import type { Grade, Hint } from './score'

export type EventType = 'review' | 'intro' | 'known' | 'suspend' | 'unsuspend' | 'reset'

export interface ReviewDetail {
  shown_at: string // the card face came up (Bereit)
  ready_at: string // the word was revealed and the clock started
  answered_at: string
  answer: 'know' | 'dont_know'
  undo: boolean // "war doch falsch"
  score: number
  hints: Hint[]
  active_ms: number
  grade: Grade
}

export interface StudyEvent {
  id: string // ULID
  type: EventType
  word_id: string
  ts: string // ISO time; for a review, when it was answered
  deck_version: string
  app_version: string
  review?: ReviewDetail
}

/** Replay order: by time, then by id, so every device replays the same way. */
export function byTime(a: StudyEvent, b: StudyEvent): number {
  if (a.ts !== b.ts) return a.ts < b.ts ? -1 : 1
  return a.id < b.id ? -1 : a.id > b.id ? 1 : 0
}

const ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ' // Crockford base 32

/** A ULID: 48 bits of time in ms, then 80 random bits; sorts by creation time. */
export function ulid(
  now = Date.now(),
  random: (bytes: Uint8Array<ArrayBuffer>) => void = (b) => crypto.getRandomValues(b),
): string {
  let time = ''
  for (let t = now, i = 0; i < 10; i++, t = Math.floor(t / 32)) time = ALPHABET[t % 32] + time
  const bytes = new Uint8Array(new ArrayBuffer(16))
  random(bytes)
  let rest = ''
  for (const byte of bytes) rest += ALPHABET[byte % 32] // 256 is a multiple of 32: uniform
  return time + rest
}
