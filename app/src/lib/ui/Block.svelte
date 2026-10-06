<script lang="ts">
  import type { Snippet } from 'svelte'

  // A ratatui-style block: rounded 1px border with titles set into the top edge.
  // `heading` replaces the left title when it needs markup (the live score).
  // `titleEnd` slides the left title to the right edge (the card flip, D38).
  let {
    title = '',
    titleRight = '',
    titleEnd = false,
    heading,
    children,
    class: className = '',
  }: {
    title?: string
    titleRight?: string
    titleEnd?: boolean
    heading?: Snippet
    children: Snippet
    class?: string
  } = $props()
</script>

<section class="block {className}">
  {#if heading}
    <h2 class="title left" class:end={titleEnd}>{@render heading()}</h2>
  {:else if title}
    <h2 class="title left" class:end={titleEnd}>{title}</h2>
  {/if}
  {#if titleRight}<span class="title right">{titleRight}</span>{/if}
  {@render children()}
</section>

<style>
  .block {
    position: relative;
    min-height: 0;
    display: flex;
    flex-direction: column;
    /* --block-border lets a block take another colour (the score's band). */
    border: 1px solid var(--block-border, var(--border));
    border-radius: var(--radius);
    padding: 0.7em 1ch 0.4em;
    transition: border-color 0.8s ease;
  }

  .title {
    position: absolute;
    top: -0.62em;
    margin: 0;
    padding: 0 0.6ch;
    background: var(--bg);
    color: var(--accent);
    font: inherit;
    line-height: 1.2;
    white-space: nowrap;
  }

  /* Linear and 0.4 s, so the title moves with the card flip's scan line (SWEEP_MS). */
  .left {
    left: 1ch;
    transition:
      left 0.4s linear,
      transform 0.4s linear;
  }

  .left.end {
    left: calc(100% - 1ch);
    transform: translateX(-100%);
  }

  .right {
    right: 1ch;
  }
</style>
