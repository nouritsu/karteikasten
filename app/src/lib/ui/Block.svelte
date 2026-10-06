<script lang="ts">
  import type { Snippet } from 'svelte'

  // A ratatui-style block: rounded 1px border with titles set into the top edge.
  // `heading` replaces the left title when it needs markup (the live score).
  let {
    title = '',
    titleRight = '',
    heading,
    children,
    class: className = '',
  }: { title?: string; titleRight?: string; heading?: Snippet; children: Snippet; class?: string } = $props()
</script>

<section class="block {className}">
  {#if heading}
    <h2 class="title left">{@render heading()}</h2>
  {:else if title}
    <h2 class="title left">{title}</h2>
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

  .left {
    left: 1ch;
  }

  .right {
    right: 1ch;
  }
</style>
