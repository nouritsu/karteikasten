<script lang="ts">
  import { typingDelay, typingPieces } from '../engine/typing'

  // A sentence typed out left to right (the Satz hint), its highlighted word kept.
  let { text, hl, animate = true }: { text: string; hl: [number, number]; animate?: boolean } = $props()
  let typed = $state(0)

  $effect(() => {
    const length = text.length
    if (!animate || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      typed = length
      return
    }
    typed = 0
    const delay = typingDelay(length)
    const start = performance.now()
    let raf = 0
    const tick = (now: number) => {
      typed = Math.min(length, Math.floor((now - start) / delay))
      if (typed < length) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  })

  const pieces = $derived(typingPieces(text, hl, typed))
</script>

{#each pieces as piece, i (i)}{#if piece.mark}<mark class={piece.state}>{piece.text}</mark>{:else}<span
      class={piece.state}>{piece.text}</span
    >{/if}{/each}

<style>
  mark {
    background: none;
    color: inherit;
    font-weight: 700;
    text-decoration: underline;
  }

  .untyped {
    visibility: hidden;
  }

  .cursor {
    background: var(--accent);
    color: transparent;
  }
</style>
