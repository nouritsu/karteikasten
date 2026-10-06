// The reveal animation: every letter cycles random letters of its own case
// (umlauts and ß included), every digit random digits, and each locks in place
// from left to right. The card's word and the score use it.

const UPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ'
const LOWER = 'abcdefghijklmnopqrstuvwxyzäöüß'
const DIGITS = '0123456789'
const MARKS = "_|/\\()',.-`" // what ASCII art is drawn with

export interface ShufflePlan {
  lockAt: number[] // ms after the start at which each character is final
  duration: number
}

/** What a character cycles through, or nothing for spaces and punctuation. */
function pool(ch: string): string | null {
  if (DIGITS.includes(ch)) return DIGITS
  if (ch.toLowerCase() === ch.toUpperCase()) return null
  return ch === ch.toLowerCase() ? LOWER : UPPER
}

/** What a character scrambles through as the card flip's scan line passes it:
 *  letters and digits as in the reveal, ASCII-art marks among themselves. */
export function sweepPool(ch: string): string | null {
  return pool(ch) ?? (MARKS.includes(ch) ? MARKS : null)
}

/** Characters lock `staggerMs` apart, compressed so the whole text takes at most `maxMs`. */
export function plan(text: string, staggerMs = 50, maxMs = 700): ShufflePlan {
  const chars = [...text]
  const moving = chars.filter(pool).length
  const stagger = moving ? Math.min(staggerMs, maxMs / moving) : 0
  let locked = 0
  const lockAt = chars.map((ch) => (pool(ch) ? stagger * ++locked : 0))
  return { lockAt, duration: stagger * moving }
}

/** The text as shown `elapsed` ms into the animation. */
export function frame(
  text: string,
  shuffle: ShufflePlan,
  elapsed: number,
  random: () => number = Math.random,
  pick: (ch: string) => string | null = pool,
): string {
  return [...text]
    .map((ch, i) => {
      const chars = pick(ch)
      if (!chars || elapsed >= shuffle.lockAt[i]) return ch
      return chars[Math.floor(random() * chars.length)]
    })
    .join('')
}
