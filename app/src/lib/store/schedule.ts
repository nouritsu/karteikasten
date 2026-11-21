// When regular exports run (D62), in systemd's calendar event notation, in local time:
// https://www.freedesktop.org/software/systemd/man/latest/systemd.time.html
// Supported: the shorthands and "[weekdays] [[year-]month-day] [hour:minute[:second]]".
// From fast-track.

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
const two = (n: number) => String(n).padStart(2, '0')

export interface Field {
  values: number[] // sorted, all the values it matches
  any: boolean // every value of its range
  step?: { from: number; by: number } // written as from/by
  range?: [number, number] // written as a..b
}

export interface Calendar {
  weekdays: Field // 0 Monday … 6 Sunday
  years: Field
  months: Field // 1–12
  days: Field // 1–31
  hours: Field
  minutes: Field
  seconds: Field
}

const SHORTHANDS: Record<string, string> = {
  minutely: '*-*-* *:*:00',
  hourly: '*-*-* *:00:00',
  daily: '*-*-* 00:00:00',
  weekly: 'Mon *-*-* 00:00:00',
  monthly: '*-*-01 00:00:00',
  quarterly: '*-01,04,07,10-01 00:00:00',
  semiannually: '*-01,07-01 00:00:00',
  yearly: '*-01-01 00:00:00',
  annually: '*-01-01 00:00:00',
}

const WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

export class ScheduleError extends Error {}

/** Schedules Options offers to tap, simplest first. */
export const SCHEDULE_EXAMPLES = ['daily', 'weekly', 'Sun 21:00']

const range = (from: number, to: number) => Array.from({ length: to - from + 1 }, (_, i) => from + i)

/** One field: comma-separated parts, each *, n, a..b, n/step or * /step. `name` reads
 *  a word as a number (weekdays). */
function parseField(text: string, min: number, max: number, what: string, name?: (word: string) => number | null): Field {
  const read = (word: string): number => {
    const n = /^\d+$/.test(word) ? Number(word) : (name?.(word) ?? NaN)
    if (!Number.isInteger(n) || n < min || n > max) throw new ScheduleError(`${what} "${word}" is not between ${min} and ${max}`)
    return n
  }
  const values = new Set<number>()
  const parts = text.split(',')
  let step: Field['step']
  let span: Field['range']
  for (const part of parts) {
    if (!part) throw new ScheduleError(`an empty ${what} in "${text}"`)
    const [base, by] = part.split('/')
    let from = min
    let to = max
    if (base !== '*') {
      const ends = base.includes('..') ? base.split('..') : name && base.includes('-') ? base.split('-') : [base]
      if (ends.length > 2) throw new ScheduleError(`"${base}" is not a ${what}`)
      from = read(ends[0])
      to = ends.length === 2 ? read(ends[1]) : by === undefined ? from : max
      if (to < from) throw new ScheduleError(`the ${what} range "${base}" runs backwards`)
      if (ends.length === 2 && parts.length === 1 && by === undefined) span = [from, to]
    }
    const stride = by === undefined ? 1 : Number(by)
    if (!Number.isInteger(stride) || stride < 1) throw new ScheduleError(`"/${by}" is not a repetition`)
    if (by !== undefined && parts.length === 1) step = { from, by: stride }
    for (let v = from; v <= to; v += stride) values.add(v)
  }
  const sorted = [...values].sort((a, b) => a - b)
  return { values: sorted, any: sorted.length === max - min + 1, step, range: span }
}

const ANY = (min: number, max: number): Field => ({ values: range(min, max), any: true })

function weekday(word: string): number | null {
  const w = word.toLowerCase()
  const i = WEEKDAYS.findIndex((d) => d === w || (w.length === 3 && d.startsWith(w)))
  return i < 0 ? null : i
}

/** Reads an expression; throws ScheduleError saying what is wrong. */
export function parseSchedule(expression: string): Calendar {
  let text = expression.trim().toLowerCase()
  if (!text) throw new ScheduleError('it is empty')
  text = (SHORTHANDS[text] ?? text).toLowerCase()
  const tokens = text.split(/\s+/)
  if (tokens.length > 3) throw new ScheduleError('it has more than weekdays, a date and a time')
  const cal: Calendar = {
    weekdays: ANY(0, 6),
    years: ANY(1970, 2199),
    months: ANY(1, 12),
    days: ANY(1, 31),
    hours: { values: [0], any: false },
    minutes: { values: [0], any: false },
    seconds: { values: [0], any: false },
  }
  let seen = ''
  for (const token of tokens) {
    if (token.includes(':')) {
      if (seen.includes('t')) throw new ScheduleError('it has two times')
      const parts = token.split(':')
      if (parts.length < 2 || parts.length > 3) throw new ScheduleError(`"${token}" is not a time`)
      cal.hours = parseField(parts[0], 0, 23, 'hour')
      cal.minutes = parseField(parts[1], 0, 59, 'minute')
      cal.seconds = parts[2] === undefined ? { values: [0], any: false } : parseField(parts[2], 0, 59, 'second')
      seen += 't'
    } else if (/^[a-z]/.test(token)) {
      if (seen) throw new ScheduleError('weekdays come first')
      cal.weekdays = parseField(token, 0, 6, 'weekday', weekday)
      seen += 'w'
    } else if (token.includes('-')) {
      if (seen.includes('d') || seen.includes('t')) throw new ScheduleError('the date comes before the time')
      const parts = token.split('-')
      if (parts.length < 2 || parts.length > 3) throw new ScheduleError(`"${token}" is not a date`)
      const [y, m, d] = parts.length === 3 ? parts : ['*', ...parts]
      cal.years = parseField(y, 1970, 2199, 'year')
      cal.months = parseField(m, 1, 12, 'month')
      cal.days = parseField(d, 1, 31, 'day')
      seen += 'd'
    } else {
      throw new ScheduleError(`"${token}" is not a weekday, date or time`)
    }
  }
  return cal
}

/** The first moment after `from` the calendar matches, or null within the next five years. */
export function nextRun(cal: Calendar, from: Date): Date | null {
  const day = new Date(from.getFullYear(), from.getMonth(), from.getDate())
  for (let i = 0; i < 366 * 5; i++, day.setDate(day.getDate() + 1)) {
    if (
      !cal.years.values.includes(day.getFullYear()) ||
      !cal.months.values.includes(day.getMonth() + 1) ||
      !cal.days.values.includes(day.getDate()) ||
      !cal.weekdays.values.includes((day.getDay() + 6) % 7)
    )
      continue
    for (const h of cal.hours.values)
      for (const m of cal.minutes.values)
        for (const s of cal.seconds.values) {
          const at = new Date(day.getFullYear(), day.getMonth(), day.getDate(), h, m, s)
          if (at > from) return at
        }
  }
  return null
}

/** The next `count` runs after `from`, as epoch ms. */
export function upcomingRuns(cal: Calendar, from: Date, count: number): number[] {
  const runs: number[] = []
  let at: Date | null = from
  while (runs.length < count && (at = nextRun(cal, at))) runs.push(at.getTime())
  return runs
}

// Plain English ----------------------------------------------------------------

/** "a", "a and b", "a, b and c". */
export function listed(words: string[]): string {
  return words.length < 2 ? (words[0] ?? '') : `${words.slice(0, -1).join(', ')} and ${words.at(-1)}`
}

const ordinal = (n: number) => {
  const tens = n % 100
  const suffix = tens >= 11 && tens <= 13 ? 'th' : (['th', 'st', 'nd', 'rd'][n % 10] ?? 'th')
  return `${n}${suffix}`
}

const dayName = (i: number) => WEEKDAYS[i][0].toUpperCase() + WEEKDAYS[i].slice(1)
const same = (a: number[], b: number[]) => a.length === b.length && a.every((v, i) => v === b[i])

function whenOfDay(cal: Calendar): string {
  const { hours: h, minutes: m, seconds: s } = cal
  const sec = s.values.length === 1 && s.values[0] === 0 ? '' : s.values.length === 1 ? `:${two(s.values[0])}` : ''
  const clock = (hh: number, mm: number) => `${two(hh)}:${two(mm)}${sec}`
  if (m.any && h.any) return 'every minute'
  if (h.any && m.step) return `every ${m.step.by} minutes${m.step.from ? ` from :${two(m.step.from)}` : ''}`
  if (h.any && m.values.length === 1) return m.values[0] === 0 ? 'every hour, on the hour' : `every hour at :${two(m.values[0])}`
  if (h.step && m.values.length === 1) return `every ${h.step.by} hours from ${clock(h.step.from, m.values[0])}`
  if (h.range && m.values.length === 1)
    return `every hour from ${clock(h.range[0], m.values[0])} to ${clock(h.range[1], m.values[0])}`
  if (h.values.length * m.values.length <= 4) return `at ${listed(h.values.flatMap((hh) => m.values.map((mm) => clock(hh, mm))))}`
  return `at minute ${listed(m.values.map(String))} of hour ${listed(h.values.map(String))}`
}

function whichDays(cal: Calendar): string {
  const { weekdays: w, days: d, months: mo, years: y } = cal
  const parts: string[] = []
  if (!w.any) {
    if (same(w.values, [0, 1, 2, 3, 4])) parts.push('on weekdays')
    else if (same(w.values, [5, 6])) parts.push('at weekends')
    else if (w.range) parts.push(`${dayName(w.range[0])} to ${dayName(w.range[1])}`)
    else parts.push(`on ${listed(w.values.map((i) => `${dayName(i)}s`))}`)
  }
  if (!d.any) {
    const days = d.step && d.step.by > 1 ? `every ${d.step.by} days from the ${ordinal(d.step.from)}` : `on the ${listed(d.values.map(ordinal))}`
    parts.push(`${days} of ${mo.any ? 'every month' : listed(mo.values.map((m) => MONTHS[m - 1]))}`)
  } else if (!mo.any) {
    parts.push(`in ${listed(mo.values.map((m) => MONTHS[m - 1]))}`)
  }
  if (!y.any) parts.push(`in ${listed(y.values.map(String))}`)
  return parts.join(' ')
}

/** The calendar in a sentence: "On weekdays at 08:00", "Every 15 minutes". */
export function describeSchedule(cal: Calendar): string {
  const time = whenOfDay(cal)
  const days = whichDays(cal)
  const joined = days ? `${time.includes(',') ? ',' : ''} ${days}` : ''
  const sentence = time.startsWith('every') ? `${time}${joined}` : `${days || 'every day'} ${time}`
  return sentence[0].toUpperCase() + sentence.slice(1)
}
