<script lang="ts">
  import type { Hint } from '../engine/score'
  import { strings } from '../strings'
  import type { Phase } from '../session.svelte'
  import type { DeckWord } from '../types'
  import Icon, { type IconName } from './Icon.svelte'
  import ShuffleText from './ShuffleText.svelte'

  let {
    phase,
    word,
    used,
    penalties,
    onHint,
  }: {
    phase: Phase
    word: DeckWord | undefined
    used: Hint[]
    penalties: Record<Hint, number>
    onHint: (hint: Hint) => boolean
  } = $props()

  // Material Icons (D57).
  const ICONS: Record<Hint, IconName> = {
    audio: 'volume_up',
    forms: 'table_chart',
    sentence: 'notes',
    cognate: 'link',
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
      disabled={phase === 'ready' || phase === 'reveal' || phase === 'done' || !available(hint)}
      onclick={() => press(hint)}
    >
      <span class="icon" aria-hidden="true"><Icon name={ICONS[hint]} /></span><ShuffleText
          text={flashing.includes(hint) ? `-${penalties[hint]}` : strings.hints[hint]}
        />
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
