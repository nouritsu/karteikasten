<script lang="ts">
  import type { Snippet } from 'svelte'
  import { i18n } from '../i18n/index.svelte'
  import Block from './Block.svelte'

  let { title, onClose, children }: { title: string; onClose: () => void; children: Snippet } = $props()

  function keydown(event: KeyboardEvent) {
    if (event.key === 'Escape') onClose()
  }
</script>

<svelte:window onkeydown={keydown} />

<div class="backdrop" role="presentation" onclick={(e) => e.target === e.currentTarget && onClose()}>
  <div class="sheet" role="dialog" aria-modal="true" aria-label={title}>
    <Block {title}>
      <div class="content">{@render children()}</div>
      <button type="button" class="close" onclick={onClose}>{i18n.t.close}</button>
    </Block>
  </div>
</div>

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    z-index: 10;
    display: flex;
    align-items: flex-end;
    background: color-mix(in srgb, var(--bg) 55%, transparent);
    padding: calc(1.2em + var(--inset-top)) 0.6em calc(0.6em + var(--inset-bottom));
  }

  .sheet {
    width: 100%;
    max-height: 85dvh;
    display: flex;
    background: var(--bg);
  }

  .sheet :global(.block) {
    flex: 1;
    max-height: 85dvh;
  }

  .content {
    overflow-y: auto;
    padding-top: 0.3em;
  }

  .close {
    margin-top: 0.8em;
    align-self: flex-end;
  }
</style>
