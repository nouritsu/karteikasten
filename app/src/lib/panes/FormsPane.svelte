<script lang="ts">
  import { strings } from '../strings'
  import type { DeckWord } from '../types'
  import FormsView from '../ui/FormsView.svelte'
  import Pane from '../ui/Pane.svelte'

  // Forms (D32, D54): the word's forms, hung below Card once the hint's deduction has shown.
  let { word, onClose }: { word: DeckWord; onClose: () => void } = $props()
</script>

<Pane title={strings.forms.title} icon="table_chart" {onClose}>
  <FormsView {word} />
</Pane>
