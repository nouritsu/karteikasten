// The translate button's animation: after a language switch, every piece of UI
// text that changed runs the reveal shuffle into its new wording. German content
// (the word, forms, sentences) does not change, so it stays still.

import { frame, plan } from '../engine/shuffle'

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
