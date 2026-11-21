import { describe, expect, it } from 'vitest'
import { carries, lockAxis, resist, stepsAt } from './drag'

describe('drag', () => {
  it('stays a tap within the slop, then commits to the larger axis', () => {
    expect(lockAxis(4, 5)).toBeNull()
    expect(lockAxis(14, 5)).toBe('x')
    expect(lockAxis(-3, -20)).toBe('y')
  })

  it('resists past an end', () => {
    expect(resist(90, false)).toBe(90)
    expect(resist(90, true)).toBe(30)
  })

  it('carries through when far enough or flicked the same way', () => {
    expect(carries(-120, 375, 0)).toBe(true) // past a quarter
    expect(carries(-40, 375, -0.8)).toBe(true) // short but fast
    expect(carries(-40, 375, 0.8)).toBe(false) // flicked back
    expect(carries(-40, 375, -0.1)).toBe(false)
    expect(carries(0, 375, 1)).toBe(false)
  })

  it('counts whole steps towards zero', () => {
    expect(stepsAt(59, 28)).toBe(2)
    expect(stepsAt(-30, 28)).toBe(-1)
    expect(stepsAt(10, 28)).toBe(0)
  })
})
