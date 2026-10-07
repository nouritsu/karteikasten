import { describe, expect, it } from 'vitest'
import { ActiveClock } from './clock'
import { band, DEFAULT_SCORE, grade, Rating, score } from './score'
import { frame, plan, sweepPool } from './shuffle'
import { typingDelay, typingPieces } from './typing'

describe('score', () => {
  it('stays full during the grace period', () => {
    expect(score(0, [])).toBe(100)
    expect(score(2000, [])).toBe(100)
    expect(score(3499, [])).toBe(100)
  })

  it('loses a step per full interval after the grace period', () => {
    expect(score(3500, [])).toBe(95)
    expect(score(5000, [])).toBe(90)
    expect(score(2000 + 1500 * 14, [])).toBe(30)
    expect(score(2000 + 1500 * 20, [])).toBe(0)
  })

  it('charges each hint once', () => {
    expect(score(0, ['audio'])).toBe(90)
    expect(score(0, ['audio', 'audio', 'forms'])).toBe(75)
    expect(score(0, ['picture', 'cognate'])).toBe(20)
  })

  it('never drops below zero', () => {
    expect(score(60_000, ['picture'])).toBe(0)
    expect(score(0, ['audio', 'forms', 'sentence', 'picture', 'cognate'])).toBe(0)
  })

  it('takes its numbers from the settings', () => {
    const quick = { ...DEFAULT_SCORE, graceMs: 0, intervalMs: 1000, step: 5 }
    expect(score(2500, [], quick)).toBe(90)
  })
})

describe('grade', () => {
  it('maps the bands', () => {
    expect(grade('know', 0)).toBe(Rating.Hard)
    expect(grade('know', 39)).toBe(Rating.Hard)
    expect(grade('know', 40)).toBe(Rating.Good)
    expect(grade('know', 84)).toBe(Rating.Good)
    expect(grade('know', 85)).toBe(Rating.Easy)
    expect(grade('know', 100)).toBe(Rating.Easy)
  })

  it('makes "Weiß ich nicht" and the undo Again', () => {
    expect(grade('dont_know', 100)).toBe(Rating.Again)
    expect(grade('know', 100, true)).toBe(Rating.Again)
  })

  it('names the band the score bar colours', () => {
    expect([100, 85, 84, 40, 39, 0].map((value) => band(value))).toEqual(['easy', 'easy', 'good', 'good', 'hard', 'hard'])
    expect(band(50, { ...DEFAULT_SCORE, bands: { good: 60, easy: 90 } })).toBe('hard')
  })
})

describe('active clock', () => {
  it('counts only while running', () => {
    const clock = new ActiveClock()
    expect(clock.elapsed(1000)).toBe(0)
    clock.start(1000)
    expect(clock.elapsed(4000)).toBe(3000)
    clock.pause(4000)
    expect(clock.elapsed(60_000)).toBe(3000)
    clock.start(60_000)
    expect(clock.elapsed(61_500)).toBe(4500)
  })

  it('ignores a second start and a pause while stopped', () => {
    const clock = new ActiveClock()
    clock.pause(10)
    clock.start(100)
    clock.start(500)
    expect(clock.elapsed(600)).toBe(500)
  })
})

describe('letter shuffle', () => {
  it('locks letters 50 ms apart, left to right', () => {
    const p = plan('die Hand')
    expect(p.lockAt).toEqual([50, 100, 150, 0, 200, 250, 300, 350])
    expect(p.duration).toBe(350)
  })

  it('compresses long words to at most 700 ms', () => {
    const p = plan('die Geschwindigkeitsbegrenzung')
    expect(p.duration).toBeCloseTo(700)
    expect(Math.max(...p.lockAt)).toBeCloseTo(700)
  })

  it('cycles letters of the same case and keeps spaces', () => {
    const shown = frame('Äb ß', plan('Äb ß'), 0, () => 0.99)
    expect(shown).toBe('Üß ß')
    expect(frame('die Hand', plan('die Hand'), 10_000)).toBe('die Hand')
  })

  it('cycles digits through digits, for the score', () => {
    const p = plan('100', 120)
    expect(p.lockAt).toEqual([120, 240, 360])
    expect(frame('100', p, 0, () => 0.99)).toBe('999')
    expect(frame('100', p, 130, () => 0)).toBe('100')
    expect(frame('100', p, 250, () => 0.5)).toBe('105')
  })
})

describe('flip sweep scramble', () => {
  it('scrambles letters, digits and ASCII-art marks, but not spaces', () => {
    expect(sweepPool('a')).toContain('z')
    expect(sweepPool('7')).toBe('0123456789')
    expect(sweepPool('_')).toContain('|')
    expect(sweepPool(' ')).toBeNull()
  })

  it('keeps art marks among themselves until each settles', () => {
    const art = String.raw`|_\/`
    const shuffle = { lockAt: [0, 100, 100, 100], duration: 100 }
    const shown = frame(art, shuffle, 50, () => 0, sweepPool)
    expect(shown[0]).toBe('|')
    expect([...shown.slice(1)].every((ch) => sweepPool('_')!.includes(ch))).toBe(true)
    expect(frame(art, shuffle, 100, Math.random, sweepPool)).toBe(art)
  })
})

describe('sentence typing', () => {
  it('types 30 ms a character, faster when a sentence is long', () => {
    expect(typingDelay(20)).toBe(30)
    expect(typingDelay(50)).toBe(20)
    expect(typingDelay(0)).toBe(0)
  })

  it('keeps untyped text in place, invisible, and the highlight whole', () => {
    const text = 'Gib mir deine Hand.'
    const hl: [number, number] = [14, 18]
    expect(typingPieces(text, hl, 0)).toEqual([
      { text: 'G', mark: false, state: 'cursor' },
      { text: 'ib mir deine ', mark: false, state: 'untyped' },
      { text: 'Hand', mark: true, state: 'untyped' },
      { text: '.', mark: false, state: 'untyped' },
    ])
    expect(typingPieces(text, hl, 15)).toEqual([
      { text: 'Gib mir deine ', mark: false, state: 'typed' },
      { text: 'H', mark: true, state: 'typed' },
      { text: 'a', mark: true, state: 'cursor' },
      { text: 'nd', mark: true, state: 'untyped' },
      { text: '.', mark: false, state: 'untyped' },
    ])
    expect(typingPieces(text, hl, text.length).map((piece) => piece.state)).toEqual(['typed', 'typed', 'typed'])
  })
})
