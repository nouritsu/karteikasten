// The Satz hint types its sentence out left to right. Characters not yet typed
// stay in the layout, invisible, so lines never rewrap while it types; the next
// one shows as the cursor.

export interface Piece {
  text: string
  mark: boolean // part of the highlighted word
  state: 'typed' | 'cursor' | 'untyped'
}

/** Milliseconds per character: `perCharMs`, faster for long text so it takes at most `maxMs`. */
export function typingDelay(length: number, perCharMs = 30, maxMs = 1000): number {
  return length ? Math.min(perCharMs, maxMs / length) : 0
}

/** `text` after `typed` characters, cut so the highlight [start, end) stays whole. */
export function typingPieces(text: string, hl: [number, number], typed: number): Piece[] {
  const cuts = [...new Set([0, hl[0], hl[1], typed, typed + 1, text.length])]
    .filter((i) => i >= 0 && i <= text.length)
    .sort((a, b) => a - b)
  const pieces: Piece[] = []
  for (let i = 0; i + 1 < cuts.length; i++) {
    const [from, to] = [cuts[i], cuts[i + 1]]
    const state = to <= typed ? 'typed' : from === typed ? 'cursor' : 'untyped'
    pieces.push({ text: text.slice(from, to), mark: hl[0] < hl[1] && from >= hl[0] && to <= hl[1], state })
  }
  return pieces
}
