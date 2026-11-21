<script lang="ts">
  import type { Snippet } from 'svelte'
  import { strings } from '../strings'
  import { drag, stepsAt } from './drag'
  import { tick } from './haptics'
  import { hold } from './hold'
  import ShuffleText from './ShuffleText.svelte'

  // A field set with < > instead of typing, TUI style (D56): a label, the value at a
  // fixed width (or `children`, when it needs markup), and the two glyph buttons, which
  // repeat while held. A sideways swipe across the row scrubs it: a step every STEP_PX,
  // right for more, with a tick. `onStep` is told when a step is one of a repeat or a
  // scrub, not a tap. `stacked`, it is one of a row of them: its label over < value >.
  const STEP_PX = 28
  let {
    label,
    value = '',
    children,
    labelWidth = 5,
    width = 10,
    onStep,
    atStart = false,
    atEnd = false,
    words = [strings.step.less, strings.step.more],
    stacked = false,
  }: {
    label: string
    value?: string
    children?: Snippet // in place of `value`
    labelWidth?: number // the label's width in characters
    width?: number // the value's width in characters, so nothing moves as it changes
    onStep: (direction: -1 | 1, repeating: boolean) => void
    atStart?: boolean
    atEnd?: boolean
    words?: [string, string] // what the < and > buttons do, for their names: "weniger", "mehr"
    stacked?: boolean
  } = $props()

  // A tapped step shuffles the value into place; a held or scrubbed one just shows it,
  // as a shuffle at that pace would only flicker.
  let quick = $state(false)
  function step(direction: -1 | 1, repeating: boolean) {
    quick = repeating
    onStep(direction, repeating)
  }

  let taken = 0 // steps the scrub has applied so far
  const scrub = {
    axis: 'x' as const,
    onStart: () => (taken = 0),
    onMove: (dx: number) => {
      const want = stepsAt(dx, STEP_PX)
      while (taken !== want) {
        const direction = want > taken ? 1 : -1
        if ((direction > 0 && atEnd) || (direction < 0 && atStart)) return
        step(direction, true)
        taken += direction
        tick()
      }
    },
    onEnd: () => (taken = 0),
  }
</script>

{#snippet shown()}<span class="setting" style:min-width="{width}ch"
    >{#if children}{@render children()}{:else}<ShuffleText text={value} plain={quick} />{/if}</span
  >{/snippet}

{#snippet earlier()}<button
    type="button"
    class="glyph"
    aria-label="{label} {words[0]}"
    title="{label} {words[0]}"
    disabled={atStart}
    use:hold={(repeating) => step(-1, repeating)}>&lt;</button
  >{/snippet}

{#snippet later()}<button
    type="button"
    class="glyph"
    aria-label="{label} {words[1]}"
    title="{label} {words[1]}"
    disabled={atEnd}
    use:hold={(repeating) => step(1, repeating)}>&gt;</button
  >{/snippet}

{#if stacked}
  <div class="stepper stacked" use:drag={scrub}>
    <span class="label">{label}</span>
    <span class="dial">{@render earlier()}{@render shown()}{@render later()}</span>
  </div>
{:else}
  <div class="stepper" use:drag={scrub}>
    <span class="label" style:width="{labelWidth}ch">{label}</span>{@render shown()}{@render earlier()}{@render later()}
  </div>
{/if}

<style>
  .stepper {
    touch-action: pan-y;
    display: flex;
    align-items: center;
    gap: 1ch;
    margin: 0.25em 0;
  }

  /* The label keeps its width, so the values of a block's steppers line up. */
  .label {
    flex: none;
  }

  .setting {
    flex: 1;
    white-space: pre;
    color: var(--accent);
  }

  /* Stacked, one of a row (Steppers): the label over < value >, all centred. */
  .stacked {
    flex-direction: column;
    gap: 0;
    margin: 0;
  }

  .dial {
    display: flex;
    align-items: center;
  }

  .stacked .setting {
    flex: none;
    text-align: center;
  }

  .stacked .glyph {
    min-width: 1.8em;
  }
</style>
