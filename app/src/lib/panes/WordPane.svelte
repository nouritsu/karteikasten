<script lang="ts">
  import type { StudyEvent } from '../engine/events'
  import { LOCALE, strings } from '../strings'
  import type { Session } from '../session.svelte'
  import { genderClass, headword, keyFormLines } from '../ui/format'
  import Icon from '../ui/Icon.svelte'
  import Pane from '../ui/Pane.svelte'
  import ShuffleText from '../ui/ShuffleText.svelte'
  import { nearClock } from '../ui/when'
  import { statusOf } from '../words'

  // Word (spec: Words): everything the deck has on a word, without a score, and the three
  // actions (D53, D56). Pause and Already know it act at once; Already know it then
  // offers Undo until the pane closes. Reset asks again first, in red.
  let { session, events, id, onClose }: { session: Session; events: StudyEvent[]; id: string; onClose: () => void } = $props()
  const t = strings.words

  const word = $derived(session.words.find((w) => w.id === id))
  const ws = $derived(session.states.get(id))
  const status = $derived(statusOf(ws))
  const head = $derived(word ? headword(word) : { article: '', lemma: '' })
  const glosses = $derived(word ? word.gloss_en : [])

  const reviews = $derived(events.filter((e) => e.word_id === id && e.type === 'review' && e.review))
  const average = $derived(reviews.length ? Math.round(reviews.reduce((sum, e) => sum + e.review!.score, 0) / reviews.length) : null)

  // Already know it on a new word can be taken back by resetting it to new again.
  let markedKnown = $state(false)
  const DISARM_MS = 3000
  let armed = $state(false)
  let disarm = 0

  function act(type: 'known' | 'suspend' | 'unsuspend' | 'reset') {
    session.act(type, id)
  }

  function reset() {
    clearTimeout(disarm)
    if (!armed) {
      armed = true
      disarm = window.setTimeout(() => (armed = false), DISARM_MS)
      return
    }
    armed = false
    markedKnown = false
    act('reset')
  }
</script>

<Pane title={t.word} icon="style" {onClose}>
  {#if word}
    <p class="head">
      {#if head.article}<span class="g-{genderClass(word)}">{head.article}</span>{' '}{/if}<strong>{head.lemma}</strong>
      <span class="muted">· #{word.rank} · {strings.pos[word.pos] ?? word.pos}</span>
    </p>
    {#if word.ipa || word.cognate_en}
      <p class="muted">{[word.ipa, word.cognate_en && `≈ ${word.cognate_en}`].filter(Boolean).join(' · ')}</p>
    {/if}
    {#each glosses as gloss, i (i)}
      <p lang="en">{#if glosses.length > 1}<span class="muted">{i + 1}.</span>{' '}{/if}{gloss.text}</p>
    {/each}
    {#each keyFormLines(word, strings) as line (line)}<p class="muted">{line}</p>{/each}
    <hr class="split" />
    {#if status === 'new' && !ws?.introduced}
      <p class="muted">{t.notYet}</p>
    {:else if ws}
      <p>
        {#if !ws.suspended}{t.due(nearClock(ws.card.due, new Date(session.now)))}{' · '}{/if}{t.reviews(reviews.length)}{#if average !== null}{' · '}{t.average(
            average,
          )}{/if}
      </p>
      <p>
        {t.stability(ws.card.stability.toLocaleString(LOCALE, { maximumFractionDigits: 0 }))} · <span class:muted={ws.card.lapses === 0}
          >{t.lapses(ws.card.lapses)}</span
        > · {strings.words.states[status]}
      </p>
    {/if}
    <hr class="split" />
    <div class="actions">
      {#if markedKnown}
        <button type="button" class="word" onclick={() => ((markedKnown = false), act('reset'))}
          ><span class="icon" aria-hidden="true"><Icon name="undo" /></span>{t.undo}</button
        >
      {:else if status === 'new' && !ws?.introduced}
        <button type="button" class="word" onclick={() => ((markedKnown = true), act('known'))}
          ><span class="icon" aria-hidden="true"><Icon name="check" /></span>{t.known}</button
        >
      {/if}
      {#if ws?.suspended}
        <button type="button" class="word" onclick={() => act('unsuspend')}
          ><span class="icon" aria-hidden="true"><Icon name="play_arrow" /></span>{t.resume}</button
        >
      {:else}
        <button type="button" class="word" onclick={() => act('suspend')}
          ><span class="icon" aria-hidden="true"><Icon name="pause" /></span>{t.pause}</button
        >
      {/if}
      {#if ws?.introduced && !markedKnown}
        <button type="button" class="word quit" class:flash={armed} onclick={reset}
          ><span class="icon" aria-hidden="true"><Icon name="restart_alt" /></span><ShuffleText text={armed ? t.resetConfirm : t.reset} /></button
        >
      {/if}
    </div>
  {/if}
</Pane>

<style>
  p {
    margin: 0.2em 0;
  }

  .head {
    font-size: 1.15em;
  }

  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.2em 2ch;
    margin-left: -0.3ch;
  }

  /* What resets: its icon in red, and its words too once armed. */
  .word.quit .icon {
    color: var(--bad);
  }

  .word.flash {
    color: var(--bad);
  }
</style>
