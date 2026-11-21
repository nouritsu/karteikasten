<script lang="ts">
  import type { Snippet } from 'svelte'
  import { strings } from '../strings'
  import Block from './Block.svelte'
  import Icon, { type IconName } from './Icon.svelte'

  // A pane as tall as its content, hung just below its page (D54): App slides the page up
  // by the pane's height to bring it in, pushing as much of the page as it needs off the
  // top, and back down to put it away. Taller than the page, it scrolls inside.
  // Close is set into its top edge on the right; `action`, the pane's own button (an
  // edge button), into its bottom edge on the right. Escape closes it too.
  let {
    title,
    icon,
    onClose,
    children,
    action,
  }: { title: string; icon?: IconName; onClose: () => void; children: Snippet; action?: Snippet } = $props()

  // Content taller than the pane scrolls natively; otherwise a vertical drag on it
  // pulls the pane down (App's .hang).
  let content = $state<HTMLElement>()
  let scrolls = $state(false)

  $effect(() => {
    const el = content
    if (!el) return
    const measure = () => (scrolls = el.scrollHeight > el.clientHeight + 1)
    const observer = new ResizeObserver(measure)
    observer.observe(el)
    measure()
    return () => observer.disconnect()
  })

  function keydown(event: KeyboardEvent) {
    if (event.key === 'Escape') onClose()
  }
</script>

<svelte:window onkeydown={keydown} />

{#snippet close()}
  <button type="button" class="edge quit" onclick={onClose}
    ><span class="icon" aria-hidden="true"><Icon name="close" /></span>{strings.close}</button
  >
{/snippet}

<!-- The pane's own button, at the right of the bottom edge. -->
{#snippet edge()}
  <span></span>{@render action?.()}
{/snippet}

<div class="pane" role="dialog" aria-modal="true" aria-label={title}>
  <Block {title} {icon} headingRight={close} actions={action ? edge : undefined}>
    <div class="content scroller" class:scrolls bind:this={content}>{@render children()}</div>
  </Block>
</div>

<style>
  /* The page's own padding: room for the title above and the buttons below. Within
     App's .hang it shrinks to the page's height at most, its content scrolling. */
  .pane {
    min-height: 0;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
    padding: 1em 0.6em 1.3em;
  }

  .content {
    touch-action: none;
  }

  .content.scrolls {
    touch-action: pan-y;
  }
</style>
