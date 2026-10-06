<script lang="ts">
  import { onMount } from 'svelte'
  import { frame, plan } from '../engine/shuffle'

  let {
    article = '',
    lemma,
    articleClass = '',
    animate = false,
    onDone,
  }: { article?: string; lemma: string; articleClass?: string; animate?: boolean; onDone?: () => void } = $props()

  const text = $derived(article ? `${article} ${lemma}` : lemma)
  let shown = $state('')

  onMount(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (!animate || reduced) {
      shown = text
      onDone?.()
      return
    }
    const shuffle = plan(text)
    const start = performance.now()
    let lastSwap = -Infinity
    let raf = 0
    const tick = (now: number) => {
      const elapsed = now - start
      if (elapsed >= shuffle.duration) {
        shown = text
        onDone?.() // the clock starts when the last letter locks
        return
      }
      if (now - lastSwap >= 40) {
        shown = frame(text, shuffle, elapsed)
        lastSwap = now
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  })
</script>

<span class="word" style:--chars={text.length}>
  {#if article}<span class={articleClass}>{shown.slice(0, article.length)}</span>{shown.slice(article.length)}{:else}{shown}{/if}
</span>

<style>
  .word {
    display: block;
    text-align: center;
    white-space: nowrap;
    font-weight: 700;
    line-height: 1.15;
    /* Auto-fit to the card width, between 1.5x and 3x the base size. */
    font-size: clamp(1.5rem, calc(100cqi / (var(--chars) * 0.56)), 3rem);
  }
</style>
