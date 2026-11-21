// The card flip's text animation (D38): characters scramble in behind its scan line.

import { frame, plan, sweepPool, type ShufflePlan } from '../engine/shuffle'
import { reducedMotion } from './motion'

function textNodes(root: Node): Text[] {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  const nodes: Text[] = []
  while (walker.nextNode()) {
    const node = walker.currentNode as Text
    if (node.data.trim()) nodes.push(node)
  }
  return nodes
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
