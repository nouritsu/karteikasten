<script lang="ts">
  import type { Hint } from '../engine/score'
  import type { Answer, Session } from '../session.svelte'
  import Card from '../ui/Card.svelte'
  import ScoreBar from '../ui/ScoreBar.svelte'
  import StatusBar from '../ui/StatusBar.svelte'

  // Card (D54): the study screen as before, less the Menü. Status, card and score share
  // the page 20/60/10; the card takes what the others leave, and the two never shrink
  // below their content.
  let {
    session,
    onHint,
    onAnswer,
    onNext,
  }: {
    session: Session
    onHint: (hint: Hint) => boolean
    onAnswer: (answer: Answer) => void
    onNext: () => void
  } = $props()
</script>

<div class="study">
  <StatusBar {session} />
  <Card {session} {onHint} />
  <ScoreBar {session} {onAnswer} {onNext} />
</div>

<style>
  .study {
    height: 100%;
    display: grid;
    grid-template-rows: minmax(min-content, 20fr) 60fr minmax(min-content, 10fr);
    gap: 1em;
  }
</style>
