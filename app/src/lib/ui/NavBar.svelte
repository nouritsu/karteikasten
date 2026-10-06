<script module lang="ts">
  export type Screen = 'options' | 'theme' | 'lang' | 'stats' | 'words' | 'search' | 'info'
</script>

<script lang="ts">
  import { i18n } from '../i18n/index.svelte'
  import type { Theme } from '../theme'
  import Block from './Block.svelte'

  let { theme, onOpen }: { theme: Theme; onOpen: (screen: Screen) => void } = $props()

  // One row of square icon buttons; their names are for screen readers. The
  // symbols come from the app font (nix/app-assets.nix; ⏾ ☼ 🕮 from Noto
  // Sans Symbols 2). Theme and language
  // show the current mode: moon for Mocha, sun for Latte; de or en.
  const ITEMS = $derived<{ id: Screen; icon: string }[]>([
    { id: 'options', icon: '⛭' },
    { id: 'theme', icon: theme === 'mocha' ? '⏾' : '☼' },
    { id: 'lang', icon: i18n.lang },
    { id: 'stats', icon: '▥' },
    { id: 'words', icon: '🕮' },
    { id: 'search', icon: '⌕' },
    { id: 'info', icon: 'ⓘ' },
  ])
</script>

<Block title={i18n.t.nav.title} class="nav">
  <div class="row">
    {#each ITEMS as item (item.id)}
      <button type="button" aria-label={i18n.t.nav[item.id]} title={i18n.t.nav[item.id]} onclick={() => onOpen(item.id)}>
        <span class="icon" aria-hidden="true">{item.icon}</span>
      </button>
    {/each}
  </div>
</Block>

<style>
  .row {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 0.6ch;
  }

  .row button {
    aspect-ratio: 1;
    padding: 0;
    display: grid;
    place-items: center;
    font-size: 1.3em;
    white-space: nowrap;
  }

  .row .icon {
    margin: 0;
  }
</style>
