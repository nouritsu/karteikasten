<script lang="ts">
  import { untrack } from 'svelte'
  import { frame, plan } from '../engine/shuffle'
  import { reducedMotion } from './motion'

  // Text that runs the card's reveal shuffle whenever it changes (the score, a hint's
  // deduction, a live value); the first text just appears, unless `intro` shuffles it in
  // too. While `plain`, a change just appears: for a value that changes too fast to
  // shuffle (a held stepper).
  let {
    text,
    staggerMs = 50,
    intro = false,
    plain = false,
  }: { text: string; staggerMs?: number; intro?: boolean; plain?: boolean } = $props()
  let shown = $state('')
  let first = true
  // The text as a value, so only a change of the text itself shuffles.
  const current = $derived(text)

  $effect(() => {
    const target = current
    const shuffle = plan(target, untrack(() => staggerMs))
    if ((first && !intro) || untrack(() => plain) || !shuffle.duration || reducedMotion()) {
      first = false
      shown = target
      return
    }
    if (first) shown = frame(target, shuffle, 0) // an intro starts scrambled, not blank
    first = false
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
