# Phase 6 report: screens, in fast-track's design language

2026-11-21. The app has fast-track's shell and controls, and the Phase 6 screens are built in them. The decisions are D54–D66, your choices from this session; `docs/mockups.md` draws every page and pane.

**After your review.** You asked for an English-only UI, aimed at English speakers learning German, written as plain English rather than translated from the German.
- **One language (D66).** One `strings.ts` replaces the German and English string files. The language row in Display and the shuffle between languages are gone.
- **Meanings.** The card always shows the English meanings and, once answered, the sentence's translation. The German definitions stay in the deck but no longer show.
- **Wording.** Labels read as English: "I was wrong" for the undo, Score, Cognate, Already know it, and "Done for today!".
- **Schedules.** Regular exports read English schedules only, as in fast-track.

You also asked for fixes to the spacing, mostly on Stats:
- **Overview** sets its values two to a line, each with its label and its change. The span before breaks only between its parts.
- **The range words** sit apart and clear of the corner; the range itself is a calendar icon instead of "…".
- **Recall and Coverage** draw each share as a meter, in three columns: label, bar, number.
- **Score** draws its answers as one bar across the block, with a legend that keeps each square beside its name.
- **Days** is a grid of squares, deeper in the accent the more reviews a day had, with today outlined.
- **Charts** stand on a baseline.
- **Elsewhere:**
  - A block's steppers now line up (the label could shrink before).
  - Words sets the type and status apart.
  - Info puts each source's licence on its own line.
  - Score's summary and a word's credits break only between their parts.

**Needs you:**

0. **The APK has not been built yet.** cache.nixos.org kept dropping the download of Gradle 8.14.4 here, and the APK needs it. The web build passes in Nix, but the new Java (the `Native` and `SystemPrefs` plugins, the alarm receiver, the backup agent) has not been through a compiler. If the cache misbehaves for you too, `NIX_CONFIG="substituters = https://cache.nixos.org"` skips the unreachable attic cache; don't use `--fallback`, which starts rebuilding the compilers from source.
1. **Install the debug build beside your real app** and try it, so your review history stays untouched:

   ```
   nix run .#apk-debug -- --install
   ```

   It shows up as "Karteikasten (debug)", with its own storage. To try it on your own history, export from the real app and import into the debug one.
2. **On the phone, check what the browser cannot:**
   - Options → Reminder on: Android asks once for notifications. The reminder comes at the time set, with the app closed too, and goes away when you open the app.
   - Options → Backup → Export on a schedule, with a time a few minutes ahead: the file lands in `Documents/Karteikasten/`, and the block's last line says so.
   - Options → Display set to System: Text size, Motion, Haptics and Clock follow Android's settings.
   - The new icon: on the home screen, and in its themed (monochrome) form if you use themed icons.
3. **Then install it as the real app** (`nix run .#apk -- --install`) once you're happy. It updates in place and keeps your history.

## What changed

The spec keeps its German names for screens and buttons (Karte, Bereit, Feierabend); the app shows them in English (D66), and this list uses the app's words.

- **Pages (D54).** Card │ Stats │ Words │ Options │ Info along the bottom, switched by a tap or a swipe; the Menü row is gone and the card takes its room. While you are on another page, the card's clock is paused, as when the app is in the background.
- **Panes (D54).** Forms, Word and Licences rise from below and push their page up. Close them with Close, Escape, a tap on what is left of the page, or a drag down.
- **Status (D55).** The block above the card is titled Status. Dashed fields now show every dash; Iosevka used to join three into a line.
- **Controls (D56)** come from fast-track:
  - buttons set into a block's border;
  - `[ on ]` words that read muted when off;
  - `< >` steppers that repeat while held and follow a drag;
  - red for what closes or resets, and Reset asks twice.
- **Icons (D57).** Material Icons as inline SVG. The paths are fast-track's, plus 16 taken from the Material Icons font in nixpkgs with fontTools. The Noto Sans Symbols subset is gone.
- **Theme and colours (D58).** Flavour steps through Mocha, Latte and System; the circle still grows from the button you press. Colours unfolds under Theme, with the accent and the four gender colours from Catppuccin's fourteen.
- **Display (D59).** Text size, Motion, Haptics and Clock. System reads Android through a small `SystemPrefs` plugin, as in fast-track.
  - The old haptics on/off becomes System or Off.
  - Every animation now follows Motion, not only the browser's reduced-motion flag.
- **Stats (D60).** Overview with the span (30d 90d 1y all, or a range from the calendar icon) and ▲ ▼ against the span before. Then History, Score, Recall, Coverage, Days, Rhythm, Records and Trouble words.
  - History, Score and Rhythm are SVG charts: tap or drag to read a bar, kept from turning the page.
  - ⇅ Arrange moves blocks or puts them away.
  - A single replay of the events gives each review the state its card was in, so Recall counts only cards already learnt and splits young from mature.
- **Words.** Search that folds umlauts and ß, finding lemmas first and then English meanings; filters for status, type and gender. A tap opens the Word pane, with Already know it (undo while the pane is open), Pause/Resume, and Reset.
- **Info (D61).** The adjective endings (weak, mixed, strong), Sources with every source's licence and, for a word you search for, its own audio and sentence credits, and About. The Licences pane shows the new `THIRD_PARTY_NOTICES.md`, which `nix/app.nix` bundles.
- **Done for today.** The full summary:
  - today's reviews and their average;
  - new words and the streak;
  - the coverage since 04:00;
  - the next learning card's time, or tomorrow's count.
- **Backup and privacy (D62).** Keep one file writes `karteikasten.json` instead of a dated file.
  - Export on a schedule takes a systemd OnCalendar expression (`daily`, `Mon..Fri 08:00`) and describes it back in plain words.
  - The study events live in IndexedDB, which Android's side cannot read. So the app saves a fresh backup to its own storage each time it goes to the background, and an alarm copies it to `Documents/Karteikasten/` on schedule, app closed or not.
  - Cloud backup is off by default; a backup agent from fast-track honours it, and a direct transfer to a new phone works either way.
- **Reminder (D63).** When the app goes to the background it plans the next week's reminders, each with its count: "31 cards due · 15 new words · 12-day streak". Days already studied, and days with nothing due, get none. An alarm posts each one. There is no new npm or Gradle dependency: the notification uses AndroidX, which the app already ships.
- **Debug build (D64).** `nix run .#apk-debug` builds `com.nouritsu.karteikasten.debug`, labelled "Karteikasten (debug)".
- **Icon (D65).** fast-track's block with the translate glyph; a monochrome twin for themed icons, and `ic_stat_study` for the reminder.

## Done criteria

| Criterion | Result |
| --- | --- |
| Every string is in one place | Yes: every page, pane, chart reading, reminder and Feierabend line is in `strings.ts` (D66). |
| Every screen works one-handed | The tabs, the answer and hint buttons, and every control sit in the lower two thirds or scroll there; panes rise from the bottom. Checked in a 390 × 844 browser window; still to check on the phone. |
| Attribution is complete | Info → Sources lists every source and, per word, every recording and sentence credit from `attribution.json`; Licences lists the app's components. |

## Tests and checks

- **Vitest:** 92 pass (58 before), with new tests for the schedule parser, the reminder planner, Stats' numbers, the Words search, the theme choice and drags.
- **`svelte-check`:** clean.
- **In the browser** (390 × 844, with six weeks of made-up reviews in the browser's own database):
  - Every page renders in English, and the tabs and the Forms and Word panes work.
  - Colours steps the accent, Flavour switches the theme, and Stats draws and reads its charts.
  - Words finds "strasse" as Straße, and Sources lists Hand's credits.
  - An answered card shows the English meaning and the sentence's translation.
- **Nix:** the web build (`karteikasten-app`) and the debug APK's evaluation pass, and alejandra is clean; the APK itself is not built (above).
- **Not yet checked:** anything only Android does (the plugins, alarms, notifications, the backup agent and the icons), and the day's summary on a real day's end.
- **Not built:** the word of the day, which has no design yet.
