# Phase 5 report: core study loop

2026-10-22. The app now schedules with FSRS, keeps every answer in IndexedDB, and backs up to `Documents/Karteikasten/` (D52, your choice).

**After your first phone test.** "Pressing Bereit shows the word with its meaning" was the spec's Intro for new words (D16). Your history was empty, so every card was new, and the scored, word-only checks only began after the fourth new word. Nothing had crashed. You chose to test new words like reviews instead (D53): Bereit shows only the word, and your answer is its first FSRS rating. Words you already ran through the Intro on the phone get their scored check first. Walking the same flow in the browser, from an empty history and again after the change, turned up no other fault.

**Needs you:**

1. **Install and use it daily for a week.** That is the one done criterion only you can check. Each day, a few things to look at:
   - New words show only the word, like reviews. One you know is done for days; one you don't comes back within minutes.
   - Fällig, Neu, Serie and Abdeckung look right.
   - Nothing you answered is missing the next day.
2. **Export → wipe → import on the phone:**
   1. Optionen → Exportieren. The file lands in `Documents/Karteikasten/`.
   2. Clear the app's storage in Android's settings.
   3. Optionen → Importieren, and pick the file.
   The status bar should show the same Heute, Gesamt, Serie and Abdeckung as before, and the same cards should be due. The same round trip passes in the tests.

## Done criteria

| Criterion | Result |
| --- | --- |
| Vitest covers decay, penalties, bands, undo, pause, queue and replay | Yes: 58 tests. Decay, penalties and bands were already covered; new tests cover undo, pause, the queue, the 04:00 day, the replay (one event at a time equals all at once, fuzz included), new words as scored cards and the session through to Feierabend. |
| Export → wipe → import restores identical state | Yes in the tests: the events, settings and replayed card states are equal after a wipe, and a second import adds nothing. Still to do on the phone (above). |
| A week of real daily use loses nothing | Your week starts with this APK. An answer is saved the moment you give it, so closing the app before Weiter loses nothing either. |

## How it works

- **Events.** Every answer is an append-only review event in IndexedDB, in the spec's shape: a ULID, the word, the time, both versions, and its times, answer, undo, score, hints, active time and grade. The replay also reads the spec's other types (`known`, `suspend`, `unsuspend`, `reset`, and `intro` from before D53).
- **Card state.** FSRS-6 through ts-fsrs 5.4: retention 0.9, fuzz on, learning steps 1 m and 10 m, relearning 10 m. Each word's state is replayed from its events. Fuzz is seeded from the card, so a replay gives the same due dates.
  - The `cards` store is a cache of that replay, rewritten from it at every start.
  - A new word's first answer is its first rating; Kenne ich schon (a Wörter action, Phase 6) will be a first rating of Easy.
- **Answers not yet closed.** An answered review is kept in `meta` until Weiter writes it; undo changes it there. If the app closes first, the next start writes it as it stood.
- **The queue**, in order:
  1. Words left from an Intro (before D53) and never rated.
  2. Learning and relearning cards due now.
  3. Reviews due before 04:00 tomorrow, oldest first.
  4. New words by rank, up to 15 a day. A word counts on the day of its first answer.

  With nothing else left: a learning card due within 20 minutes; after that, Feierabend. Feierabend checks every 5 seconds for a card that has come due, and a new day brings new words.
- **The card flow.** Every card, new or not, runs Bereit → word → score → answer → Weiter (D53): decay, hints, "war doch falsch" until Weiter. Weiter into Feierabend turns the card over too.
- **Sentence choice (D12).** The card shows the word's sentence with the most words you know, then the one with fewer unknown words, then the deck's order.
- **Status bar.** Every field is real now:
  - Heute and Gesamt count reviews (since 04:00 / ever).
  - Fällig is checks, learning cards and reviews still due today; Neu is the new words left today.
  - Serie is days in a row with a review, counting from yesterday while today has none.
  - Abdeckung sums the token share of words in FSRS Review.
- **Settings.** The new-word limit, n, retention, every score number, audio after answering, haptics and the learn-ahead window live in IndexedDB with defaults and travel in exports. The Optionen screen for them comes in Phase 6.
- **Export and import (D52).**
  - Optionen → Exportieren writes `Documents/Karteikasten/karteikasten-YYYY-MM-DD.json`: every event and the settings, language and theme included.
  - Importieren takes a file from the system picker, merges events by id, and asks whether to take the backup's settings too.
  - Android 11 and newer need no permission; for 9 and 10 the manifest asks for the old storage access.

## Left for Phase 6

These need the Phase 6 screens:
- Feierabend's full summary; Phase 5 shows today's reviews and when the next card is due.
- The word of the day.
- Optionen beyond backup.
- Wörter's Pausieren and Zurücksetzen. The events and replay already handle them.

## Amendments

- **D52 · Export target.** Your choice: `Documents/Karteikasten/` through `@capacitor/filesystem`, without asking each time. Replaces "Export downloads".
- **D53 · New words.** Your choice after the first phone test: a new word runs like a review, and its first answer is its first FSRS rating. No Intro, no Kenne ich schon on the card, no separate check. Replaces D16's Intro; the 15 new words a day stay.

`docs/SPEC.md` has D52 and D53, and the queue, pending-answer and cache details under Scheduling. Phase 5's line now names the language button (D35) instead of the old EN/DE toggle.

## Tests

- **Vitest:** 58 pass.
  - The engine tests pass in four time zones (UTC, India, Los Angeles, Kiritimati), so the 04:00 rollover does not depend on the machine's zone.
  - The storage tests run on fake-indexeddb, an in-memory IndexedDB; the store, export and import code is the app's own.
- **In the browser** (Vite, the real deck):
  - a word left from an Intro comes back as a word-only check;
  - a brand-new word shows only the word, with the score running;
  - the answer is saved as pending and becomes a review event on Weiter;
  - Heute, Fällig and Neu count correctly afterwards;
  - the Options sheet shows the backup section.
- **`npm run check`:** clean.
