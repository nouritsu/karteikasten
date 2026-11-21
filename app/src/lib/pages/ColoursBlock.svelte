<script lang="ts">
  import { accentName, COLOR_KEYS, DEFAULT_COLORS, sameColors, stepAccent, type ColorKey, type Colors } from '../colors'
  import { strings } from '../strings'
  import Block from '../ui/Block.svelte'
  import Icon from '../ui/Icon.svelte'
  import ShuffleText from '../ui/ShuffleText.svelte'
  import Stepper from '../ui/Stepper.svelte'

  // Colours (D58): the accent and each gender colour, from Catppuccin's accents. `<` `>`
  // step a row through them, round the ends, and each step applies at once. It unfolds
  // below Options' Theme block, and Close, in its top edge, folds it away.
  let { colors, onChange, onClose }: { colors: Colors; onChange: (colors: Colors) => void; onClose: () => void } = $props()
  const t = strings.options

  // A name shuffles into place on a tap, and just changes while a hold or a drag steps
  // fast, which would only flicker.
  let fast = $state(false)

  function step(key: ColorKey, direction: -1 | 1, repeating: boolean) {
    fast = repeating
    onChange({ ...colors, [key]: stepAccent(colors[key], direction) })
  }

  function reset() {
    fast = false
    onChange({ ...DEFAULT_COLORS })
  }
</script>

{#snippet close()}
  <button type="button" class="edge quit" onclick={onClose}
    ><span class="icon" aria-hidden="true"><Icon name="close" /></span>{strings.close}</button
  >
{/snippet}

{#snippet edge()}
  <span></span>
  <button type="button" class="edge" disabled={sameColors(colors, DEFAULT_COLORS)} onclick={reset}
    ><span class="icon" aria-hidden="true"><Icon name="restart_alt" /></span>{t.defaults}</button
  >
{/snippet}

<Block title={t.colors} icon="palette" headingRight={close} actions={edge}>
  {#each COLOR_KEYS as key (key)}
    <Stepper label={t.colorNames[key]} labelWidth={7} width={14} onStep={(direction, repeating) => step(key, direction, repeating)}>
      <span style:color="var(--ctp-{colors[key]})" aria-hidden="true">████</span>
      <ShuffleText text={accentName(colors[key])} plain={fast} />
    </Stepper>
  {/each}
</Block>
