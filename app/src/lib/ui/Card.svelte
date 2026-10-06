<script lang="ts">
  import { tick, untrack } from 'svelte'
  import type { Hint } from '../engine/score'
  import { i18n } from '../i18n/index.svelte'
  import type { Phase, Session } from '../session.svelte'
  import type { DeckWord, Sentence } from '../types'
  import Block from './Block.svelte'
  import { flips, HOLD_MS, mirrored, NAME_ART, REACH_CH, SCRAMBLE_MS, SWEEP_MS } from './flip'
  import HintBar from './HintBar.svelte'
  import ShuffleText from './ShuffleText.svelte'
  import ShuffleWord from './ShuffleWord.svelte'
  import TypeText from './TypeText.svelte'
  import { genderClass, headword, keyFormLines } from './format'
  import { sweepIn } from './retext'

  let { session, onHint }: { session: Session; onHint: (hint: Hint) => boolean } = $props()

  type Face = { phase: Phase; word: DeckWord | undefined }
  const current = (): Face => ({ phase: session.phase, word: session.word })

  // What the face shows. It follows the session, except that answering and Weiter
  // turn the card over first (D38): the old front stays until the back covers it.
  let face = $state.raw<Face>(current())
  let back = $state(false) // the back of the card lies over the face
  let scanning = $state(false) // the scan line is crossing
  let titleEnd = $state(false) // the title sits at the right edge, mirrored
  let flipping = false
  let faceEl: HTMLElement | undefined = $state()
  let backEl: HTMLElement | undefined = $state()
  let scanEl: HTMLElement | undefined = $state()
  let animations: Animation[] = []

  const t = $derived(i18n.t)
  const word = $derived(face.word)
  const answered = $derived(face.phase === 'answered')
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
    if (face.phase === 'ready') settled = false
  })

  $effect(() => {
    current() // follow the session
    untrack(sync)
  })

  /** Brings the face up to the session: a flip, or at once. A running flip lands on
   *  the latest state itself and calls this again when it is done. */
  function sync() {
    if (flipping) return
    const next = current()
    if (flips(face.phase, next.phase) && !matchMedia('(prefers-reduced-motion: reduce)').matches) flip()
    else face = next
  }

  async function flip() {
    flipping = true
    try {
      back = true
      titleEnd = true
      await tick()
      await sweep(backEl, 'cover')
      // The line stopped under the K; the back now covers the card edge to edge.
      for (const animation of animations) animation.cancel()
      scanning = false
      await new Promise((resolve) => setTimeout(resolve, HOLD_MS))
      face = current()
      titleEnd = false
      await tick()
      await sweep(faceEl, 'uncover')
    } catch {
      // cancelled: land on the session as it is
      face = current()
      titleEnd = false
    } finally {
      // Filled animations would outlive the flip and stack up (as the Thema reveal's did).
      for (const animation of animations) animation.cancel()
      animations = []
      back = false
      scanning = false
      flipping = false
    }
    sync()
  }

  /** One pass of the scan line, travelling under the title's K: left to right, the
   *  back comes in behind it ('cover'); right to left, the back peels away and
   *  shows the new front ('uncover'). The side coming in scrambles into place as
   *  the line passes. */
  async function sweep(incoming: HTMLElement | undefined, mode: 'cover' | 'uncover') {
    if (!incoming || !backEl || !scanEl) return
    for (const animation of animations) animation.cancel()
    scanning = true
    const cover = mode === 'cover'
    const reach = REACH_CH * 0.5 * parseFloat(getComputedStyle(backEl).fontSize)
    sweepIn(incoming, SWEEP_MS, SCRAMBLE_MS, !cover, reach)
    const timing: KeyframeAnimationOptions = { duration: SWEEP_MS, easing: 'linear', fill: 'forwards' }
    // The back covers the card from its left edge up to the line.
    const clip = [
      { clipPath: `inset(0 calc(100% - ${reach}px) 0 0)` },
      { clipPath: `inset(0 ${reach}px 0 0)` },
    ]
    const line = [{ left: `${reach}px` }, { left: `calc(100% - ${reach}px)` }]
    animations = [
      backEl.animate(cover ? clip : clip.reverse(), timing),
      scanEl.animate(cover ? line : line.reverse(), timing),
    ]
    await Promise.all(animations.map((animation) => animation.finished))
    scanning = false
  }
</script>

<Block class="card" {titleEnd}>
  {#snippet heading()}<ShuffleText text={titleEnd ? mirrored(t.card.title) : t.card.title} staggerMs={80} />{/snippet}
  <!-- While the card runs, the word holds the middle and what a hint opens
       appears below it without moving it. Once answered, all of it flows from
       the top. Mid-flip the back of the card lies over it. -->
  <div class="turn">
    <div class="face" class:answered bind:this={faceEl}>
      {#if face.phase === 'ready'}
        <!-- The whole face is the button, so Bereit! is easy to hit. -->
        <button type="button" class="ready" onclick={() => session.start()}>{t.card.ready}</button>
      {:else}
        <div class="center">
          {#if word}
            {#key word.id}
              <ShuffleWord
                article={head.article}
                lemma={head.lemma}
                articleClass={colour}
                animate={face.phase === 'reveal'}
                onDone={revealed}
              />
            {/key}
            <div class="sound" class:visible={settled || face.phase !== 'reveal'}>
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

        {#if word}
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
      {/if}
    </div>
    {#if back}
      <div class="back" bind:this={backEl}>
        <pre class="name" role="img" aria-label="nouritsu">{NAME_ART}</pre>
      </div>
    {/if}
    <div class="scan" class:scanning bind:this={scanEl}></div>
  </div>
  <hr />
  <HintBar phase={session.phase} word={session.word} used={session.hints} {onHint} />
</Block>

<style>
  /* Three rows, the outer two always equal, so the word in the middle stays put
     whatever opens below it; past the bottom edge the card scrolls. */
  .turn {
    position: relative;
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
  }

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

  /* The back of the card: the author's name, 41 columns fitted to the width
     (Iosevka's characters are half an em wide), in a Catppuccin rainbow from
     the top left to the bottom right. */
  /* The side margins keep the name inside the line's reach (REACH_CH), so all of
     it comes in behind the line. */
  .back {
    position: absolute;
    inset: 0;
    padding-inline: 1.6ch;
    display: grid;
    place-items: center;
    background: var(--bg);
    container-type: inline-size;
  }

  .name {
    margin: 0;
    font: inherit;
    font-size: min(1em, calc(100cqi / 21.4));
    line-height: 1.15;
    background: linear-gradient(
      to bottom right,
      var(--ctp-red),
      var(--ctp-peach),
      var(--ctp-yellow),
      var(--ctp-green),
      var(--ctp-sapphire),
      var(--ctp-blue),
      var(--ctp-mauve)
    );
    background-clip: text;
    -webkit-background-clip: text;
    color: transparent;
  }

  /* The scan line: a bright bar in the accent colour, glowing. It reaches up to
     the title on the border, which travels with it. */
  .scan {
    position: absolute;
    top: -0.15em;
    bottom: 0;
    left: 0;
    width: 0.5ch;
    transform: translateX(-50%);
    background: var(--accent);
    box-shadow: 0 0 0.8em var(--accent);
    pointer-events: none;
    visibility: hidden;
  }

  .scan.scanning {
    visibility: visible;
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
