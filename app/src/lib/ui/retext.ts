// Text animations over a whole part of the page. The translate button's: after a
// language switch, every piece of UI text that changed runs the reveal shuffle
// into its new wording; German content (the word, forms, sentences) does not
// change, so it stays still. The card flip's: characters scramble in behind its
// scan line.

import { frame, plan, sweepPool, type ShufflePlan } from '../engine/shuffle'

function textNodes(root: Node): Text[] {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  const nodes: Text[] = []
  while (walker.nextNode()) {
    const node = walker.currentNode as Text
    if (node.data.trim()) nodes.push(node)
  }
  return nodes
}

/** The text under `root` now, to compare against after the switch. */
export function snapshot(root: Node): Map<Text, string> {
  return new Map(textNodes(root).map((node) => [node, node.data]))
}

/** Shuffles every text node that is new or changed since `before`. A node the app
 *  rewrites meanwhile (a ticking clock) is left to the app. */
export function shuffleChanged(root: Node, before: Map<Text, string>, staggerMs = 25, maxMs = 500): void {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  const moving = textNodes(root)
    .filter((node) => before.get(node) !== node.data)
    .map((node) => ({ node, target: node.data, shuffle: plan(node.data, staggerMs, maxMs), written: node.data }))
  if (!moving.length) return
  const start = performance.now()
  let lastSwap = -Infinity
  const tick = (now: number) => {
    const elapsed = now - start
    const swap = now - lastSwap >= 40
    if (swap) lastSwap = now
    let running = false
    for (const item of moving) {
      if (item.node.data !== item.written) continue // the app has written it since
      const done = elapsed >= item.shuffle.duration
      if (done || swap) {
        item.written = done ? item.target : frame(item.target, item.shuffle, elapsed)
        item.node.data = item.written
      }
      if (!done) running = true
    }
    if (running) requestAnimationFrame(tick)
  }
  requestAnimationFrame(tick)
}

/** The card flip's scan line (D38) runs across `root` in `sweepMs`, from the left
 *  or from the right, between `reach` px in from either edge: each character
 *  scrambles from the start and settles `scrambleMs` after the line has passed
 *  it. The flip clips away what the line has not reached yet. */
export function sweepIn(root: HTMLElement, sweepMs: number, scrambleMs: number, fromRight = false, reach = 0): void {
  const box = root.getBoundingClientRect()
  const span = box.width - 2 * reach
  if (span <= 0) return
  const range = document.createRange()
  const moving = textNodes(root).map((node) => {
    const lockAt: number[] = []
    let offset = 0
    for (const ch of node.data) {
      range.setStart(node, offset)
      range.setEnd(node, offset + ch.length)
      const rect = range.getBoundingClientRect()
      const x = Math.min(1, Math.max(0, (rect.left + rect.width / 2 - box.left - reach) / span))
      lockAt.push((fromRight ? 1 - x : x) * sweepMs + scrambleMs)
      offset += ch.length
    }
    const shuffle: ShufflePlan = { lockAt, duration: sweepMs + scrambleMs }
    return { node, target: node.data, shuffle, written: node.data }
  })
  const start = performance.now()
  let lastSwap = -Infinity
  const tick = (now: number) => {
    const elapsed = now - start
    const done = elapsed >= sweepMs + scrambleMs
    if (!done && now - lastSwap < 40) return void requestAnimationFrame(tick)
    lastSwap = now
    for (const item of moving) {
      if (item.node.data !== item.written) continue // the app has written it since
      item.written = done ? item.target : frame(item.target, item.shuffle, elapsed, Math.random, sweepPool)
      item.node.data = item.written
    }
    if (!done) requestAnimationFrame(tick)
  }
  tick(start)
}
