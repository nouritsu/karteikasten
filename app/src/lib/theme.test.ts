import { afterEach, describe, expect, it, vi } from 'vitest'
import { revealFrames, savedChoice, shownTheme, THEME_CHOICES } from './theme'

const scale = (frame: Keyframe) => Number(/^scale\((.+)\)$/.exec(String(frame.transform))?.[1])

describe('theme choice', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('cycles through Mocha, Latte and System', () => {
    expect(THEME_CHOICES).toEqual(['mocha', 'latte', 'system'])
  })

  it('shows the chosen theme, and System as the device is', () => {
    expect(shownTheme('mocha', false)).toBe('mocha')
    expect(shownTheme('latte', true)).toBe('latte')
    expect(shownTheme('system', true)).toBe('mocha')
    expect(shownTheme('system', false)).toBe('latte')
  })

  it.each([
    [null, 'mocha'],
    ['mocha', 'mocha'],
    ['latte', 'latte'],
    ['system', 'system'],
    ['dark', 'mocha'],
  ])('reads %s back as %s', (saved, choice) => {
    vi.stubGlobal('localStorage', { getItem: () => saved })
    expect(savedChoice()).toBe(choice)
  })

  it('falls back to Mocha without storage', () => {
    vi.stubGlobal('localStorage', {
      getItem: () => {
        throw new Error('blocked')
      },
    })
    expect(savedChoice()).toBe('mocha')
  })
})

describe('theme reveal', () => {
  it.each([
    ['grows', true, 0, 1],
    ['shrinks', false, 1, 0],
  ])('%s the circle from start to end', (_, grow, first, last) => {
    const { circle } = revealFrames(grow)
    expect([circle[0].offset, scale(circle[0])]).toEqual([0, first])
    expect([circle.at(-1)!.offset, scale(circle.at(-1)!)]).toEqual([1, last])
    circle.slice(1).forEach((frame, i) => expect(frame.offset!).toBeGreaterThan(circle[i].offset!))
  })

  it.each([true, false])('keeps the view inside the circle in place (grow: %s)', (grow) => {
    const { circle, view } = revealFrames(grow)
    circle.forEach((frame, i) => {
      expect(view[i].offset).toBe(frame.offset)
      if (scale(frame) >= 0.001) expect(scale(frame) * scale(view[i])).toBeCloseTo(1, 9)
    })
  })
})
