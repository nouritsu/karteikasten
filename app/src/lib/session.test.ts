import { describe, expect, it } from 'vitest'
import { Rating } from './engine/score'
import { Session } from './session.svelte'
import type { DeckWord } from './types'

function deck(...ids: string[]): DeckWord[] {
  return ids.map((id, i) => ({
    id, rank: i + 1, lemma: id, pos: 'noun', gender: null, article: null, token_share: 0.01, coverage_cum: 0,
    ipa: null, syllables: null, stress_syllable: null, cognate_en: null, flags: [], key_forms: {}, tables: {},
    gloss_en: [], gloss_de: [], audio: null, image: null, emoji: null, is_concrete: null, sentences: [],
  }))
}

function running(session: Session, at: number) {
  session.start()
  session.revealed(at)
}

describe('session', () => {
  it('runs Bereit, reveal, running, answered and back', () => {
    const s = new Session()
    s.words = deck('a', 'b')
    expect(s.phase).toBe('ready')
    s.start()
    expect(s.phase).toBe('reveal')
    s.revealed(1000)
    expect(s.phase).toBe('running')
    s.respond('know', 2000)
    expect(s.phase).toBe('answered')
    s.next()
    expect(s.phase).toBe('ready')
    expect(s.word?.id).toBe('b')
  })

  it('freezes the score on "Weiß ich" and grades it', () => {
    const s = new Session()
    s.words = deck('a')
    running(s, 0)
    s.respond('know', 5000) // 3 s after the grace period: two steps
    s.now = 60_000
    expect(s.score).toBe(90)
    s.next()
    expect(s.reviews[0]).toMatchObject({ score: 90, grade: Rating.Easy })
  })

  it('charges hints once and only while running', () => {
    const s = new Session()
    s.words = deck('a')
    expect(s.use('audio')).toBe(false)
    running(s, 0)
    expect(s.use('audio')).toBe(true)
    expect(s.use('audio')).toBe(false)
    s.now = 0
    expect(s.score).toBe(90)
    s.respond('know', 0)
    expect(s.use('picture')).toBe(false)
  })

  it('makes "Weiß ich nicht" and the undo score 0 and Again', () => {
    const s = new Session()
    s.words = deck('a', 'b')
    running(s, 0)
    s.respond('dont_know', 1000)
    expect(s.score).toBe(0)
    s.next()
    running(s, 0)
    s.respond('know', 1000)
    expect(s.score).toBe(100)
    s.undo()
    expect(s.score).toBe(0)
    s.next()
    expect(s.reviews.map((r) => r.grade)).toEqual([Rating.Again, Rating.Again])
    expect(s.known).toEqual([])
  })

  it('pauses the clock while the page is hidden', () => {
    const s = new Session()
    s.words = deck('a')
    running(s, 0)
    s.visibility(true, 3000)
    s.visibility(false, 600_000)
    s.respond('know', 601_000)
    expect(s.activeMs).toBe(4000)
    expect(s.score).toBe(95) // 4 s active: one step after the grace period, not 600 s of decay
  })
})
