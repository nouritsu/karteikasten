<script lang="ts" module>
  export type Tone = '' | 'ok' | 'warn' | 'bad'
</script>

<script lang="ts">
  import type { Snippet } from 'svelte'
  import Icon, { type IconName } from './Icon.svelte'
  import ShuffleText from './ShuffleText.svelte'

  // A ratatui-style block: a rounded 1px border with titles set into its top edge, the
  // left one after its `icon` (a Material icon, D57) if it has one.
  // `heading` replaces the left title when it needs markup (the live score);
  // `titleEnd` slides the left title to the right edge (the card flip, D38).
  // `headingRight` replaces the right title when it needs markup (a live value, a
  // pane's Close); with `shuffle`, a right title that changes runs the letter shuffle.
  // `actions` are buttons set into the bottom edge, the way the titles sit in the top one (D56).
  let {
    title = '',
    icon,
    titleRight = '',
    titleEnd = false,
    shuffle = false,
    heading,
    headingRight,
    actions,
    children,
    class: className = '',
  }: {
    title?: string
    icon?: IconName
    titleRight?: string
    titleEnd?: boolean
    shuffle?: boolean
    heading?: Snippet
    headingRight?: Snippet
    actions?: Snippet
    children: Snippet
    class?: string
  } = $props()
</script>

<section class="block {className}" class:with-actions={actions}>
  {#if heading}
    <h2 class="title left" class:end={titleEnd}>{@render heading()}</h2>
  {:else if title}
    <h2 class="title left" class:end={titleEnd}>
      {#if icon}<span class="mark" aria-hidden="true"><Icon name={icon} /></span>{/if}{title}
    </h2>
  {/if}
  {#if headingRight}
    <span class="title right">{@render headingRight()}</span>
  {:else if titleRight}
    <span class="title right">{#if shuffle}<ShuffleText text={titleRight} />{:else}{titleRight}{/if}</span>
  {/if}
  {@render children()}
  {#if actions}<div class="actions">{@render actions()}</div>{/if}
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

  /* Room above the bottom edge for the buttons set into it. */
  .block.with-actions {
    padding-bottom: 1.3em;
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

  .mark {
    margin-right: 0.6ch;
  }

  .right {
    right: 1ch;
  }

  /* The bottom edge's buttons: a row centred on the border line, each cutting the
     line with the page's background like a title. Their tap area reaches above and
     below the line. */
  .actions {
    position: absolute;
    left: 0.4ch;
    right: 0.4ch;
    bottom: 0;
    transform: translateY(50%);
    display: flex;
    justify-content: space-between;
    align-items: center;
    pointer-events: none;
  }

  .actions > :global(*) {
    pointer-events: auto;
  }
</style>
