// One short vibration on Weiß ich, a double one on Weiß ich nicht (D40). The Vibration
// API works in Android's WebView; the manifest asks for VIBRATE. Haptics can turn it off,
// or leave it to the phone's touch feedback (D59, display.ts).

let enabled = true

export function setHaptics(on: boolean): void {
  enabled = on
}

export function buzz(kind: 'ok' | 'bad'): void {
  if (enabled) navigator.vibrate?.(kind === 'ok' ? 30 : [30, 70, 30])
}

/** The faintest tick, once per step while scrubbing a value. */
export function tick(): void {
  if (enabled) navigator.vibrate?.(8)
}
