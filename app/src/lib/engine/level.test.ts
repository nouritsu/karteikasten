import { describe, expect, it } from 'vitest'
import { levelOf, nudge, stepLevel } from './level'

describe('level (D67)', () => {
  it('steps through the sub-levels and stops at either end', () => {
    expect(stepLevel('beginner', -1)).toBe('beginner')
    expect(stepLevel('beginner', 1)).toBe('a1.1')
    expect(stepLevel('a1.2', 1)).toBe('a2.1')
    expect(stepLevel('b1.2', 1)).toBe('b1.2')
    expect(levelOf('a1.2').rank).toBe(250)
  })

  it('suggests the next level when 48 of the last 50 first answers were known', () => {
    const known = (n: number, missed: number) => [...Array(n - missed).fill(4), ...Array(missed).fill(1)]
    expect(nudge(known(50, 2), 'a1.2')).toMatchObject({ known: 48, total: 50, next: { id: 'a2.1' } })
    expect(nudge(known(50, 3), 'a1.2')).toBeNull()
    expect(nudge([...Array(10).fill(1), ...known(50, 0)], 'a1.2')).toMatchObject({ known: 50 }) // only the last 50 count
    expect(nudge(known(49, 0), 'a1.2')).toBeNull() // too few yet
    expect(nudge(known(50, 0), 'b1.2')).toBeNull() // nothing above
  })
})
