// Active review time: runs from the moment the word is revealed and stops while
// the page is hidden. Time is passed in, so the clock is easy to test.

export class ActiveClock {
  #since: number | null = null
  #accumulated = 0

  get running(): boolean {
    return this.#since !== null
  }

  start(now: number): void {
    if (this.#since === null) this.#since = now
  }

  pause(now: number): void {
    if (this.#since !== null) {
      this.#accumulated += now - this.#since
      this.#since = null
    }
  }

  elapsed(now: number): number {
    return this.#accumulated + (this.#since === null ? 0 : now - this.#since)
  }

  reset(): void {
    this.#since = null
    this.#accumulated = 0
  }
}
