// FSRS-6 through ts-fsrs (D15). A word's state is a fold over its events; the cache
// in IndexedDB must always equal this replay. Fuzz is seeded from the card itself,
// so replaying the same events gives the same due dates.

import { createEmptyCard, fsrs, generatorParameters, Rating, State, type Card, type FSRS } from 'ts-fsrs'
import { byTime, type StudyEvent } from './events'

export { State }

export interface WordState {
  card: Card
  introduced: boolean // studied: a first review, Kenne ich schon, or an Intro (before D53)
  suspended: boolean
  first: string | null // when the word was first studied: counts toward that day's new words
}

export function scheduler(retention = 0.9): FSRS {
  return fsrs(generatorParameters({ request_retention: retention, enable_fuzz: true, enable_short_term: true }))
}

function fresh(at: Date): WordState {
  return { card: createEmptyCard(at), introduced: false, suspended: false, first: null }
}

/** The state after one event. */
export function step(state: WordState | undefined, event: StudyEvent, f: FSRS): WordState {
  const at = new Date(event.ts)
  const s = state ?? fresh(at)
  const introduced = { introduced: true, first: s.first ?? event.ts }
  switch (event.type) {
    case 'intro':
      return { ...s, ...introduced }
    case 'known': // Kenne ich schon: a first rating of Easy, no check
      return { ...s, ...introduced, card: f.next(s.card, at, Rating.Easy).card }
    case 'review':
      return { ...s, ...introduced, card: f.next(s.card, at, event.review!.grade).card }
    case 'reset':
      return fresh(at)
    case 'suspend':
      return { ...s, suspended: true }
    case 'unsuspend':
      return { ...s, suspended: false }
  }
}

/** Every word's state from all events, in replay order. */
export function replay(events: Iterable<StudyEvent>, f: FSRS): Map<string, WordState> {
  const states = new Map<string, WordState>()
  for (const event of [...events].sort(byTime)) states.set(event.word_id, step(states.get(event.word_id), event, f))
  return states
}

/** Known for coverage: FSRS state Review, which Kenne ich schon also reaches (spec: Abdeckung). */
export function isKnown(state: WordState | undefined): boolean {
  return state?.card.state === State.Review
}

/** Introduced by an Intro (before D53) but never rated: its first scored check is due. */
export function awaitingCheck(state: WordState | undefined): boolean {
  return !!state && state.introduced && state.card.state === State.New
}
