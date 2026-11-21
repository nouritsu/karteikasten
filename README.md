# Karteikasten

Flashcards for the 2,000 most common German words, for English speakers, offline on Android, drawn like a terminal.

## About

- **Words**: the 2,000 most frequent German words, ranked from film subtitles and news and web text. Each card has the word and its article in its gender's colour, IPA, syllables and a recording from Wikimedia Commons. Below them sit the English meanings, the forms (plurals, cases, conjugations), and sentences from Tatoeba with their translations.
- **Cards**: a card starts at Ready!; tap it and the word shuffles in while the score starts counting down. Audio, Forms, Sentence and Cognate help, at a cost in points. Answer Know it or Don't know; the score grades your answer for FSRS spaced repetition, so the words you know come back rarely and the ones you don't come back soon.
- **Your level**: start at A1.1 to B1.2 and the words below it come as quick checks, 20 a day, while new words start past it. When your checks go well, Done for today suggests the next level.
- **Stats**: over 30 days, 90 days, a year, all time or any range, against the span before: history, score, recall, coverage by rank, a 12-week grid of days, your study rhythm, records and the words you keep forgetting. Tap or drag across a chart to read it; reorder the blocks or put some away.
- **Words**: search by German word or English meaning (ae finds ä), filter by status, type and gender, and mark a word known, pause it or reset it.
- **Reminder**: a notification at the time you set, on days with cards due that you haven't studied yet.
- **Your data**: export and import JSON backups (a file a day, or one file kept up to date), and schedule regular exports, which run with the app closed.
- **Looks**: [Catppuccin](https://catppuccin.com) Mocha or Latte, or whichever your phone is in, with the accent and gender colours you pick; the Iosevka font, boxes drawn with lines, Material icons. Text size, motion, haptics and the clock can follow the phone.
- **Private**: no network permission, no account, no ads, no analytics.

## Installation

### F-Droid repository

Open [fdroid.nouritsu.com](https://fdroid.nouritsu.com) on your phone and tap **Add to F-Droid**, or scan its QR code. To add it by hand in F-Droid, Droid-ify or Neo Store, use:

- Address: `https://fdroid.nouritsu.com/repo`
- Fingerprint: `1C7F39DD34C841BE845D3B47EF5A5FB3CBDB9A28748D8862183AB0FEC867E971`

Updates then arrive like any other app's.

### GitHub releases

Download `karteikasten-<version>.apk` from the [latest release](https://github.com/nouritsu/karteikasten/releases/latest), then check it with either of:

```sh
sha256sum -c SHA256SUMS
gh attestation verify karteikasten-<version>.apk --repo nouritsu/karteikasten
```

The APK is signed with certificate SHA-256 `85a63ccd2f83e254da9e920d6fdaa8df8a2ffad4557332cdbbb581adbeebaaa5`, the same key as the F-Droid repo's APKs, so you can switch between the two.

### Build from source

The build needs [Nix](https://nixos.org/download) with flakes, on x86_64 Linux.

```sh
git clone https://github.com/nouritsu/karteikasten
cd karteikasten
nix build .#apk                    # unsigned APK, with the pinned deck, in result/
nix run .#apk -- --install         # sign with your debug key, then adb install
nix run .#apk-debug -- --install   # the same, as Karteikasten (debug) beside the release app
```

A build signed with your own key can't update one from a release, and the reverse is also true. Export your progress (Options → Backup) and uninstall before switching, then import it; or install the debug build, which has its own id and storage and sits beside the release app.

To work on the app:

- `nix develop --no-pure-eval`, or `direnv allow`, enters the dev shell.
- `nix build .#app-assets -o app/public/generated` builds the font subset and icons.
- `cd app && npm ci && npm run dev` runs it in a browser; it needs a deck in `app/public/deck/`.
- `nix flake check --no-pure-eval` runs everything CI runs.

## The deck

The deck is built by the pipeline in `pipeline/` from openly licensed sources, pinned in `sources.lock.json`. CI can't rebuild it, since the sources are gigabytes of snapshots, so each release bundles a deck that `nix/deck.json` pins by URL and hash, uploaded as a GitHub release of its own.

| Source | Used for | Licence |
| --- | --- | --- |
| [Wiktionary](https://www.wiktionary.org), through [Kaikki](https://kaikki.org) | Meanings, forms, pronunciation, etymology | CC BY-SA 4.0 and GFDL |
| [Tatoeba](https://tatoeba.org) | Sentences and their translations | CC BY 2.0 FR (some CC0) |
| [Wikimedia Commons](https://commons.wikimedia.org) | Recordings | Each file's own (CC BY-SA, CC BY or public domain) |
| [Leipzig Corpora Collection](https://wortschatz.uni-leipzig.de) | Word counts | CC BY 4.0 |
| [FrequencyWords](https://github.com/hermitdave/FrequencyWords) (OpenSubtitles 2018) | Word counts | CC BY-SA 4.0 |
| [Universal Dependencies](https://universaldependencies.org) German GSD and HDT | Word-type ratios | CC BY-SA 4.0 |

The app's Info → Sources credits every recording and sentence by name.

## Privacy and permissions

Your progress stays on the phone. The app can't go online, and nothing leaves the phone unless you export it. Android's cloud backup skips the app's data unless you turn it on in **Options → Privacy**. A direct transfer to a new phone carries the data either way (needs Android 9+).

| Permission | Why |
| --- | --- |
| `POST_NOTIFICATIONS` | The study reminder |
| `SCHEDULE_EXACT_ALARM` | The reminder and regular exports on time; without it they run a little late |
| `RECEIVE_BOOT_COMPLETED` | Sets those alarms again after a restart |
| `VIBRATE` | Haptic feedback |
| `WRITE_EXTERNAL_STORAGE` | Exports to `Documents/Karteikasten/` on Android 10 and older |

## Releasing

1. Build a public deck if the sources changed: `nix run .#build -- --profile public`, then `nix run .#deck-release` uploads it and pins it in `nix/deck.json`.
2. Bump the version in `app/package.json` (the version code follows it), add `fastlane/metadata/android/en-US/changelogs/<versionCode>.txt`, and commit.
3. Tag the commit on `main` as `v<version>` and push the tag. The release workflow checks, builds, signs and publishes the APK, then asks the F-Droid repo to rebuild.

## Attributions

- Colours: [Catppuccin](https://github.com/catppuccin/catppuccin) Mocha and Latte (MIT).
- Font: [Iosevka](https://github.com/be5invis/Iosevka) (SIL OFL 1.1).
- Icons: [Material Icons](https://fonts.google.com/icons) (Apache-2.0).
- Scheduling: [ts-fsrs](https://github.com/open-spaced-repetition/ts-fsrs) (MIT).
- Built with [Svelte](https://svelte.dev) and [Capacitor](https://capacitorjs.com).

[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) lists everything the app bundles. The app shows the same list under Info → third-party notices.

## License

The app: [GPL-3.0-or-later](LICENSE). The deck: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), each item under its own licence as credited in the app.
