<script lang="ts">
  import type { Hint } from '../engine/score'
  import { i18n } from '../i18n/index.svelte'
  import type { Session } from '../session.svelte'
  import type { Sentence } from '../types'
  import Block from './Block.svelte'
  import HintBar from './HintBar.svelte'
  import ShuffleWord from './ShuffleWord.svelte'
  import TypeText from './TypeText.svelte'
  import { genderClass, headword, keyFormLines } from './format'

  let { session, onHint }: { session: Session; onHint: (hint: Hint) => boolean } = $props()

  const t = $derived(i18n.t)
  const word = $derived(session.word)
  const answered = $derived(session.phase === 'answered')
  const head = $derived(word ? headword(word) : { article: '', lemma: '' })
  const colour = $derived(word && genderClass(word) ? `g-${genderClass(word)}` : '')
  let settled = $state(false) // IPA and syllables fade in once the shuffle is done

  // The sentence the card shows: the deck stores up to five, best first. (Phase 5
  // picks the one with the most words the learner already knows.)
  const sentence = $derived<Sentence | undefined>(word?.sentences[0])
  // The meaning follows the UI language: English glosses, or German definitions.
  const glosses = $derived(word ? (i18n.lang === 'en' ? word.gloss_en : word.gloss_de) : [])
  const showSentence = $derived(answered || session.hints.includes('sentence'))
  const showCognate = $derived(session.hints.includes('cognate') || (answered && !!word?.cognate_en))

  function revealed() {
    settled = true
    session.revealed(Date.now())
  }

  $effect(() => {
    if (session.phase === 'ready') settled = false
  })
</script>

<Block title={t.card.title} class="card">
  <!-- While the card runs, the word holds the middle and what a hint opens
       appears below it without moving it. Once answered, all of it flows from
       the top. -->
  <div class="face" class:answered>
    {#if session.phase === 'ready'}
      <!-- The whole face is the button, so Bereit! is easy to hit. -->
      <button type="button" class="ready" onclick={() => session.start()}>{t.card.ready}</button>
    {/if}
    <div class="center">
      {#if session.phase !== 'ready' && word}
        {#key word.id}
          <ShuffleWord
            article={head.article}
            lemma={head.lemma}
            articleClass={colour}
            animate={session.phase === 'reveal'}
            onDone={revealed}
          />
        {/key}
        <div class="sound" class:visible={settled || session.phase !== 'reveal'}>
          {#if word.ipa}<p class="ipa">{word.ipa}</p>{/if}
          {#if word.syllables && word.syllables.length > 1}
            <p class="syllables">
              {#each word.syllables as syllable, i (i)}{#if i > 0}<span class="dot">·</span>{/if}<span
                  class:stressed={i === word.stress_syllable}>{syllable}</span
                >{/each}
            </p>
          {/if}
        </div>
      {/if}
    </div>

    {#if word && session.phase !== 'ready'}
      <div class="below">
        {#if answered}
          <ol class="glosses" lang={i18n.lang}>
            {#each glosses as gloss, i (i)}
              <li>
                {#if glosses.length > 1}<span class="muted">{i + 1}.</span>{/if}
                {gloss.text}{#if gloss.tags.length}<span class="muted"> ({gloss.tags.join(', ')})</span>{/if}
              </li>
            {/each}
          </ol>
          {#each keyFormLines(word, t) as line (line)}<p class="form">{line}</p>{/each}
        {/if}

        {#if showCognate && word.cognate_en}
          <p class="cognate">≈ {t.cognate.english} <b>{word.cognate_en}</b></p>
        {/if}

        {#if showSentence && sentence}
          <div class="sentence">
            <p lang="de"><TypeText text={sentence.de} hl={sentence.hl} animate={!answered} /></p>
            {#if answered && i18n.lang === 'en' && sentence.en}
              <p class="muted" lang="en">{sentence.en}</p>
            {/if}
          </div>
        {/if}
      </div>
    {/if}
  </div>
  <hr />
  <HintBar phase={session.phase} {word} used={session.hints} {onHint} />
</Block>

<style>
  /* Three rows, the outer two always equal, so the word in the middle stays put
     whatever opens below it; past the bottom edge the card scrolls. */
  .face {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    container-type: inline-size;
    display: grid;
    grid-template-rows: minmax(0, 1fr) auto minmax(0, 1fr);
    grid-template-columns: minmax(0, 1fr);
  }

  .center {
    grid-row: 2;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .below {
    grid-row: 3;
    align-self: start;
    display: flex;
    flex-direction: column;
    gap: 0.15em;
    padding-top: 0.6em;
  }

  /* Answered: the word keeps its size and the rest follows it, centred while it fits
     and starting at the top once it does not. */
  .face.answered {
    display: flex;
    flex-direction: column;
  }

  .answered .center {
    margin-top: auto;
  }

  .answered .below {
    align-self: stretch;
    margin-bottom: auto;
  }

  .ready {
    grid-row: 1 / -1;
    grid-column: 1;
    width: 100%;
    height: 100%;
    font-size: 2.5em;
    color: var(--accent);
    background: none;
    border: none;
    padding: 0;
  }

  .center :global(.word) {
    width: 100%;
  }

  .sound {
    text-align: center;
    opacity: 0;
    transition: opacity 0.4s ease;
  }

  .sound.visible {
    opacity: 1;
  }

  .ipa,
  .syllables {
    margin: 0;
  }

  .syllables .dot {
    color: var(--muted);
  }

  .stressed {
    text-decoration: underline;
    text-underline-offset: 0.2em;
  }

  .glosses {
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .form,
  .cognate,
  .sentence p {
    margin: 0;
  }

  .sentence {
    margin-top: 0.6em;
    text-align: center;
  }

  hr {
    border: 0;
    border-top: 1px solid var(--border);
    margin: 0.4em -1ch 0;
  }

  @media (prefers-reduced-motion: reduce) {
    .sound {
      transition: none;
    }
  }
</style>
