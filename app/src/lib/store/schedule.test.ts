import { describe, expect, it } from 'vitest'
import { describeSchedule, nextRun, parseSchedule, SCHEDULE_EXAMPLES, ScheduleError, upcomingRuns } from './schedule'

const say = (expression: string) => describeSchedule(parseSchedule(expression))

describe('schedule', () => {
  it('reads every example Options offers', () => {
    expect(SCHEDULE_EXAMPLES.map(say)).toEqual(['Every day at 00:00', 'On Mondays at 00:00', 'On Sundays at 21:00'])
    expect(['Mon..Fri 08:00', '*:0/30'].map(say)).toEqual(['On weekdays at 08:00', 'Every 30 minutes'])
  })

  it('describes the shorthands', () => {
    expect(say('daily')).toBe('Every day at 00:00')
    expect(say('weekly')).toBe('On Mondays at 00:00')
    expect(say('hourly')).toBe('Every hour, on the hour')
    expect(say('monthly')).toBe('On the 1st of every month at 00:00')
    expect(say('quarterly')).toBe('On the 1st of January, April, July and October at 00:00')
    expect(say('minutely')).toBe('Every minute')
  })

  it('describes weekdays, dates and times in plain words', () => {
    expect(say('Mon..Fri 08:00')).toBe('On weekdays at 08:00')
    expect(say('Sat,Sun 10:30')).toBe('At weekends at 10:30')
    expect(say('Tue..Thu 07:15')).toBe('Tuesday to Thursday at 07:15')
    expect(say('Mon,Thu 08,20:00')).toBe('On Mondays and Thursdays at 08:00 and 20:00')
    expect(say('*-*-01,15 09:00')).toBe('On the 1st and 15th of every month at 09:00')
    expect(say('*-12-24 18:00')).toBe('On the 24th of December at 18:00')
    expect(say('*:0/15')).toBe('Every 15 minutes')
    expect(say('Mon..Fri *:00')).toBe('Every hour, on the hour, on weekdays')
    expect(say('9..17:30')).toBe('Every hour from 09:30 to 17:30')
    expect(say('0/6:00')).toBe('Every 6 hours from 00:00')
    expect(say('03:00')).toBe('Every day at 03:00')
  })

  it('finds the next run, strictly after now', () => {
    const daily = nextRun(parseSchedule('daily'), new Date(2026, 10, 17, 20, 30))
    expect([daily!.getDate(), daily!.getHours(), daily!.getMinutes()]).toEqual([18, 0, 0])
    const at = nextRun(parseSchedule('Mon..Fri 08:00'), new Date(2026, 10, 20, 9, 0)) // Friday 09:00
    expect([at!.getDay(), at!.getDate(), at!.getHours()]).toEqual([1, 23, 8]) // Monday the 23rd, 08:00
    const now = new Date(2026, 10, 17, 3, 0, 0)
    expect(nextRun(parseSchedule('03:00'), now)!.getDate()).toBe(18) // exactly now does not count
    expect(nextRun(parseSchedule('*-02-30'), now)).toBeNull() // never
  })

  it('lists upcoming runs in order', () => {
    const runs = upcomingRuns(parseSchedule('*:0/30'), new Date(2026, 10, 17, 10, 10), 3)
    expect(runs.map((t) => new Date(t).getMinutes())).toEqual([30, 0, 30])
  })

  it('says what is wrong with an expression', () => {
    expect(() => parseSchedule('')).toThrow(ScheduleError)
    expect(() => parseSchedule('Funday 08:00')).toThrow(/weekday/)
    expect(() => parseSchedule('25:00')).toThrow(/hour "25" is not between 0 and 23/)
    expect(() => parseSchedule('08:00 Mon')).toThrow(/weekdays come first/)
    expect(() => parseSchedule('*-13-01')).toThrow(/month/)
    expect(() => parseSchedule('17..9:00')).toThrow(/backwards/)
    expect(() => parseSchedule('*:*/0')).toThrow(/repetition/)
  })
})
