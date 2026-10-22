<script lang="ts">
  import { band } from '../engine/score'
  import { i18n } from '../i18n/index.svelte'
  import type { Answer, Session } from '../session.svelte'
  import Block from './Block.svelte'
  import ShuffleText from './ShuffleText.svelte'

  let {
    session,
    onAnswer,
    onNext,
  }: { session: Session; onAnswer: (answer: Answer) => void; onNext: () => void } = $props()
  const t = $derived(i18n.t.score)
  // No score before the clock starts, or on Feierabend.
  const waiting = $derived(['ready', 'reveal', 'done'].includes(session.phase))
  // The score sits in the title and shuffles on every change; the number and the
  // border fade to the colour of its band (the grade "Weiß ich" would give).
  const value = $derived(waiting ? '--' : String(session.score))
  const tone = $derived(waiting ? '' : `band-${band(session.score, session.settings.score)}`)
  const canUndo = $derived(session.phase === 'answered' && session.answer === 'know' && !session.undone)
</script>

<Block class="score {tone}">
  {#snippet heading()}{t.title}: <span class="value"><ShuffleText text={value} staggerMs={120} /></span>{/snippet}
  <div class="row">
    {#if session.phase === 'answered'}
      {#if canUndo}
        <button type="button" onclick={() => session.undo()}>{t.undo}</button>
      {/if}
      <button type="button" class="primary" onclick={() => onNext()}>{t.next}</button>
    {:else if session.phase === 'done'}
      <!-- Feierabend: nothing to answer -->
    {:else}
      <button type="button" disabled={session.phase !== 'running'} onclick={() => onAnswer('dont_know')}>{t.dontKnow}</button>
      <button type="button" class="primary" disabled={session.phase !== 'running'} onclick={() => onAnswer('know')}>{t.know}</button>
    {/if}
  </div>
</Block>

<style>
  :global(.score.band-easy) {
    --block-border: var(--band-easy);
  }

  :global(.score.band-good) {
    --block-border: var(--band-good);
  }

  :global(.score.band-hard) {
    --block-border: var(--band-hard);
  }

  .value {
    color: var(--block-border, var(--accent));
    font-weight: 700;
    transition: color 0.8s ease;
  }

  .row {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 1ch;
  }

  .row button {
    flex: 1;
    white-space: nowrap;
  }
</style>
