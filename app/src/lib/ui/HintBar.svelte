<script lang="ts">
  import { DEFAULT_SCORE, type Hint } from '../engine/score'
  import { i18n } from '../i18n/index.svelte'
  import type { Phase } from '../session.svelte'
  import type { DeckWord } from '../types'
  import ShuffleText from './ShuffleText.svelte'

  let {
    phase,
    word,
    used,
    onHint,
  }: { phase: Phase; word: DeckWord | undefined; used: Hint[]; onHint: (hint: Hint) => boolean } = $props()

  // Unicode symbols drawn by the app font (nix/app-assets.nix keeps them in the subset).
  const ICONS: Record<Hint, string> = {
    audio: '♪',
    forms: '▦',
    sentence: '¶',
    cognate: '⚯',
  }
  const ORDER: Hint[] = ['audio', 'forms', 'sentence', 'cognate']
  // Buttons show no costs. A press that costs points shuffles the label into its
  // deduction and back; later presses, and presses after answering, are free.
  const FLASH_MS = 900
  let flashing = $state<Hint[]>([])

  function available(hint: Hint): boolean {
    if (!word) return false
    switch (hint) {
      case 'audio':
        return word.audio !== null
      case 'forms':
        return Object.keys(word.key_forms).length > 0 || Object.keys(word.tables).length > 0
      case 'sentence':
        return word.sentences.length > 0
      case 'cognate':
        return word.cognate_en !== null
    }
  }

  function press(hint: Hint) {
    if (!onHint(hint)) return
    flashing = [...flashing, hint]
    setTimeout(() => (flashing = flashing.filter((h) => h !== hint)), FLASH_MS)
  }
</script>

<div class="hints">
  {#each ORDER as hint (hint)}
    <button
      type="button"
      class:used={used.includes(hint)}
      class:flash={flashing.includes(hint)}
      disabled={phase === 'ready' || phase === 'reveal' || !available(hint)}
      onclick={() => press(hint)}
    >
      <!-- Keyed by language: a language switch swaps the label at once; only the
           deduction shuffles. -->
      <span class="icon" aria-hidden="true">{ICONS[hint]}</span>{#key i18n.lang}<ShuffleText
          text={flashing.includes(hint) ? `-${DEFAULT_SCORE.penalties[hint]}` : i18n.t.hints[hint]}
        />{/key}
    </button>
  {/each}
</div>

<style>
  .hints {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.45em 0.6ch;
    padding-top: 0.6em;
  }

  .hints button {
    padding-inline: 0.5ch;
    white-space: nowrap;
    overflow: hidden;
    transition: color 0.3s ease;
  }

  .used {
    border-style: dashed;
  }

  .flash {
    color: var(--band-hard);
  }
</style>
