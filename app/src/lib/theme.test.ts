import { describe, expect, it } from 'vitest'
import { revealFrames } from './theme'

const scale = (frame: Keyframe) => Number(/^scale\((.+)\)$/.exec(String(frame.transform))?.[1])

describe('Thema reveal', () => {
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
