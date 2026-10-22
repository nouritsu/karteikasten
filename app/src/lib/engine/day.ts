// The learning day rolls over at 04:00 local time (spec: Scheduling): a review at
// 01:30 still counts for the day before.

export const ROLLOVER_HOUR = 4

/** Start of the learning day that contains `at`. */
export function dayStart(at: Date | number, hour = ROLLOVER_HOUR): Date {
  const date = new Date(at)
  const start = new Date(date.getFullYear(), date.getMonth(), date.getDate(), hour)
  if (date < start) start.setDate(start.getDate() - 1)
  return start
}

/** When the learning day that contains `at` ends. */
export function nextRollover(at: Date | number, hour = ROLLOVER_HOUR): Date {
  const start = dayStart(at, hour)
  start.setDate(start.getDate() + 1) // calendar arithmetic, so a DST change keeps 04:00
  return start
}

const pad = (n: number) => String(n).padStart(2, '0')

function key(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

/** The learning day of `at` as YYYY-MM-DD. */
export function dayKey(at: Date | number | string, hour = ROLLOVER_HOUR): string {
  return key(dayStart(new Date(at), hour))
}

/** The calendar date of `at` as YYYY-MM-DD (for file names). */
export function dateKey(at: Date | number): string {
  return key(new Date(at))
}

function previous(day: string): string {
  const [y, m, d] = day.split('-').map(Number)
  return key(new Date(y, m - 1, d - 1))
}

/** Days in a row with at least one review, counting back from today, or from
 *  yesterday while today has none yet (spec: Serie). */
export function streak(days: ReadonlySet<string>, today: string): number {
  let day = days.has(today) ? today : previous(today)
  let count = 0
  while (days.has(day)) {
    count++
    day = previous(day)
  }
  return count
}
