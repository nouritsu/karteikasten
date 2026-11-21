// Stats' layout (D60): the blocks below Overview, which always comes first since it
// holds the span, in the user's order and without the ones put away; and the spans.

export const STAT_PANES = ['history', 'score', 'retention', 'coverage', 'days', 'rhythm', 'records', 'leeches'] as const
export type StatPane = (typeof STAT_PANES)[number]

/** What Overview's span covers: the last 30 or 90 days, a year, all time, or a range picked by day. */
export const SPANS = ['30d', '90d', '1y', 'all', 'range'] as const
export type Span = (typeof SPANS)[number]

/** Learning days (YYYY-MM-DD), both ends included. */
export interface DayRange {
  from: string
  to: string
}

/** `v` as an order of every one of `all`: the known ones in their saved order, then any
 *  it lacks (one a later version added) in their default place at the end. */
export function toOrder<T extends string>(v: unknown, all: readonly T[]): T[] {
  const saved = Array.isArray(v) ? v.filter((x, i): x is T => all.includes(x as T) && v.indexOf(x) === i) : []
  return [...saved, ...all.filter((x) => !saved.includes(x))]
}

/** `v` as a set of the ones in `allowed`, without repeats. */
export const toSubset = <T extends string>(v: unknown, allowed: readonly T[]): T[] =>
  Array.isArray(v) ? allowed.filter((x) => v.includes(x)) : []

/** Moves `id` one place along `order`, towards the start for -1; at an end it stays. */
export function moveIn<T>(order: readonly T[], id: T, by: -1 | 1): T[] {
  const from = order.indexOf(id)
  const to = from + by
  if (from < 0 || to < 0 || to >= order.length) return [...order]
  const next = [...order]
  ;[next[from], next[to]] = [next[to], next[from]]
  return next
}
