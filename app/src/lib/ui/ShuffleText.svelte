<script lang="ts">
  import { frame, plan } from '../engine/shuffle'

  // Text that runs the card's reveal shuffle whenever it changes (the score, a
  // hint's deduction); the first text just appears.
  let { text, staggerMs = 50 }: { text: string; staggerMs?: number } = $props()
  let shown = $state('')
  let first = true

  $effect(() => {
    const target = text
    const shuffle = plan(target, staggerMs)
    if (first || !shuffle.duration || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      first = false
      shown = target
      return
    }
    const start = performance.now()
    let lastSwap = -Infinity
    let raf = 0
    const tick = (now: number) => {
      const elapsed = now - start
      if (elapsed >= shuffle.duration) {
        shown = target
        return
      }
      if (now - lastSwap >= 40) {
        shown = frame(target, shuffle, elapsed)
        lastSwap = now
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  })
</script>

<span>{shown}</span>
