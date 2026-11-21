import { describe, expect, it } from 'vitest'
import { strings } from './strings'
import { planReminders, type ReminderSource } from './reminder'

const T0 = new Date(2026, 10, 21, 10, 0).getTime() // Saturday 10:00
const source = (over: Partial<ReminderSource> = {}): ReminderSource => ({
  countsAt: () => ({ due: 31, fresh: 15 }),
  reviewsOn: () => 0,
  streak: 12,
  ...over,
})

describe('study reminder', () => {
  it('plans a week at the time set, today first while it is still to come', () => {
    const items = planReminders(source(), 19 * 60, T0, strings.reminder)
    expect(items).toHaveLength(7)
    expect(new Date(items[0].at).getDate()).toBe(21)
    expect(new Date(items[0].at).getHours()).toBe(19)
    expect(items[0].text).toBe("31 cards due · 15 new words · 12-day streak\nYou haven't studied today.")
    // Days after tomorrow can only follow a day without study: the streak is gone.
    expect(items[2].text).toBe("31 cards due · 15 new words\nYou haven't studied today.")
  })

  it('skips today once studied, and carries the streak into tomorrow', () => {
    const items = planReminders(source({ reviewsOn: () => 5 }), 19 * 60, T0, strings.reminder)
    expect(new Date(items[0].at).getDate()).toBe(22)
    expect(items[0].text).toContain('12-day streak')
  })

  it('skips a time already past today, and days with nothing due', () => {
    const late = planReminders(source(), 8 * 60, T0, strings.reminder)
    expect(new Date(late[0].at).getDate()).toBe(22)
    const none = planReminders(source({ countsAt: () => ({ due: 0, fresh: 0 }) }), 19 * 60, T0, strings.reminder)
    expect(none).toEqual([])
  })

  it('says one card and one word in the singular', () => {
    const items = planReminders(source({ countsAt: () => ({ due: 1, fresh: 1 }), streak: 0 }), 19 * 60, T0, strings.reminder)
    expect(items[0].text).toBe("1 card due · 1 new word\nYou haven't studied today.")
  })
})
