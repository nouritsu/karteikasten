# Karteikasten — Project Spec v1.0 (frozen)

Oct 6, 2026 · @nouritsu

## How to use this spec

Build Karteikasten phase by phase (see Phases), stop at each phase's acceptance criteria, and report before continuing.

- Decisions D1–D22 are frozen. If reality contradicts the spec (usually Phase 1 data), stop and propose an amendment as D23+; never deviate silently.
- Hard rule: no language model generates linguistic content. That means no glosses, forms, translations, sentences, pronunciations, images or audio. Missing data stays missing and shows up in the coverage report.
- Human corrections go through `overrides/` and carry provenance `manual`.
- Every datum carries provenance. Every media file and sentence carries source, author and licence.
- Environment: NixOS, a plain flake with a devenv dev shell (D47), direnv (`use flake . --no-pure-eval`), comma for one-off tools. Never install anything globally.
- Shell is fish. Write glue scripts in fish or Python, never bash-only syntax. Use `rg` and `fd` in docs and examples; coreutils are uutils.
- Be polite to every upstream: descriptive User-Agent with contact, rate limits, caching, retries with backoff.
- Never commit `data/` or any DeReWo file.

## Product summary

Karteikasten is a phone-only Android app (D40) that teaches the top n German words (default 2,000) with homely, ratatui-styled flashcards built only from openly licensed data.

- Frequency: a spoken-weighted blend of subtitle and news/web corpora, lemmatized with Wiktionary.
- Per word: type, gender, IPA with syllables and stress, audio, key forms and full tables, meaning (English and German, toggle), example sentences, English cognate hint. No pictures (D46).
- Look: monospace text, box borders with inset titles, Material icons drawn as SVG (D57). It is rendered in HTML/CSS, not a terminal grid, so the word can be large.
- Learning: two buttons (Weiß ich / Weiß ich nicht), a decaying score with hint penalties, and the score mapped to an FSRS-6 grade.
- Scope: personal use now, data kept release-ready. The desktop runs the data pipeline and the curation tool and builds the APK (D42).
- "Karteikasten" is a working title; rename freely.

## Decision log (frozen)

All 22 decisions are final; D19 was not answered, so it takes the recommended default.

| ID | Topic | Decision |
| --- | --- | --- |
| D1 | Target device | Phones only, portrait, OS-agnostic PWA. No tablet or desktop layouts, no desktop study client. |
| D2 | Audience | Personal now, possible public release later. Keep licence metadata; a `public` build profile drops NC/ND items. |
| D3 | App stack | PWA in TypeScript with Svelte 5 + Vite; the TUI look is done in DOM/CSS. |
| D4 | Pipeline | Python + DuckDB, packages from nixpkgs. |
| D5 | Curation tool | Rust + ratatui in a desktop terminal. |
| D6 | Frequency | Blend of spoken (subtitles) and written (news/web) counts, spoken weight 0.7 (config). |
| D7 | Lemmatizing | Wiktionary form→lemma map + Universal Dependencies treebank ratios; no statistical taggers. |
| D8 | Meaning | English glosses and German definitions, toggled on the answer view. |
| D9 | Function words, particles | Included, with word-type-specific card content. |
| D10 | Missing audio | No audio (IPA only), plus own recordings made in the curation tool. |
| D11 | Images | Emoji/OpenMoji + ARASAAC; concreteness pre-filter + manual approval; concrete nouns only. |
| D12 | Sentences | Tatoeba + Wiktionary candidates; the app shows the one with the most already-known words. |
| D13 | Extras now | Cognate hint, syllables + stress, gender colours. The rest goes to the backlog. |
| D14 | Reveal flow | Weiß ich freezes the score and reveals, with a "war doch falsch" undo; Weiß ich nicht reveals with score 0. |
| D15 | Scheduler | FSRS-6 via ts-fsrs, grade derived from the score. |
| D16 | New words | Intro view without score, "Kenne ich schon" skip, 15 new words per day. |
| D17 | Score and start | Score table below, 2 s grace. Every card starts at a Bereit! gate with all status-bar fields dashed; tapping it reveals the word with a letter-shuffle animation. |
| D18 | Status bar | Today, all-time, rank, type, gender, plus due/new, streak, coverage %, session time, average score. |
| D19 | Layout | 20/50/10/20 (status/card/score/nav) by default; ratios and the score/nav order are settings. |
| D20 | UI language | German and English with a toggle; German is the default. |
| D21 | Homely touches | Rounded borders, warm default theme, time-of-day greeting, "Feierabend!" summary, word of the day, haptics where supported. No mascot. |
| D22 | Backup and sync | Manual export/import file now; Syncthing later, so the format merges as a union of events. |

### Amendments

D23–D26 were accepted after Phase 1 on 2026-10-06 (evidence in `reports/phase1-coverage.md`); D27–D39 come from your Phase 2 review on 2026-10-07; D40–D45 from your request for an APK the same day; D46 from your request on 2026-10-15; D47 records your Nix choices, the plain flake and alejandra from Phase 0 on 2026-10-06 and the devenv shell from 2026-10-19; D48–D50 are your choices in Phase 3 on 2026-10-22, D51 your choice at the start of Phase 4 the same day, D52 your choice at the start of Phase 5, and D53 your choice after its first phone test; D54–D65 are your choices on 2026-11-21, bringing over fast-track's design language and features, with the screens drawn in `docs/mockups.md`, D66 your choice after reviewing them the same day, and D67 your idea after using the APK, also that day. The sections below are amended where they apply and marked with the decision's id.

| ID | Topic | Decision |
| --- | --- | --- |
| D23 | Kaikki English edition | Kaikki deprecated the per-language German file. Fetch the full raw dump (`raw-wiktextract-data.jsonl.gz`) and extract the German entries once per snapshot. |
| D24 | Audio speaker | Prefer the Commons author (any project, Lingua Libre or not) who covers most of the deck. Words they lack fall through to the author with the next most coverage, and so on. Regional files stay last; own recordings still win. |
| D25 | Separable verbs | Besides scaling particle verbs up, discount each base verb by its UD share of tokens that head a separated particle, and each particle by its UD share of separated-particle (PTKVZ) uses, so split uses are not counted twice. |
| D26 | Köper norms are CC BY-NC-SA | `personal` is the development build and uses the whole data set, including `is_concrete` derived from the norms. `public` ships `is_concrete` only where a human approved or rejected an image; there the norms stay a build-time filter for candidates. |
| D27 | Icons | Monochrome Unicode symbols drawn by the app font replace the emoji icons (table under App layout and look). None of them has an emoji form, so no phone swaps in colour emoji. |
| D28 | Greeting | No greeting on the card: Bereit shows only its button. Amends D21; its other homely touches stay. |
| D29 | Score display | The score sits in the score block's title ("Punkte: 70") instead of inside the block. Each change runs the letter shuffle on its digits, and the number and the block's border fade to the colour of its band (Easy green, Good yellow, Hard red). The nav block is titled "Menü". |
| D30 | Themes | Catppuccin Latte (light) and Mocha (dark) with mauve as the accent replace Stube, Kachelofen, Nord and Phosphor. Thema switches between them; Mocha is the default. Plural-only nouns are pink, because purple is the accent. |
| D31 | Layout | The Menü is one row of square icon buttons, as tall as it needs; their names are for screen readers. The card takes the space it frees: status, card and score share the rest 20/60/10. The card's hint buttons sit three to a row. Amends D19. |
| D32 | Hints | Hint buttons show no costs. A press that costs points shuffles the button's label into the deduction ("-10") and back; the Formen and Bild sheets open once it has shown. Satz types its sentence out left to right, centred, and what a hint opens appears below the word without moving it. |
| D33 | Status block | Titled "Statistik", with the weekday and time on its right edge; Heute and Gesamt move into the block. Amends how D18's fields are laid out, not the fields. |
| D34 | Bereit | Bereit! is plain text at twice its former size, without a button border; the whole card face is its button. |
| D35 | Language | A language button in the Menü, showing the current language as de or en, switches the whole UI between German and English, and the card's meaning with it: English glosses and sentence translations, or German definitions. UI text that changes shuffles into the other language; the German word, forms and sentences stay German. Replaces the EN/DE toggle on the answer view and the UI language setting in Optionen; amends D8 and D20. |
| D36 | Answered word | The word keeps its size on the answer view; the meaning, forms and sentence follow below it. |
| D37 | Thema animation | The Thema button takes the new theme first; then a Latte circle grows from it, or the Latte view shrinks into it and goes out. Without view transitions, or with reduced motion, the switch is instant. |
| D38 | Card flip | Answering and Weiter turn the card over. A scan line carries the Karte title along the border to the right edge, the title shuffling into its mirror image (etraK); the line stays under the K, from the first letter at the start to the last at the end, and the back comes in behind the line: the author's name in ASCII art, a Catppuccin rainbow from top left to bottom right. Each character scrambles as the line passes. After about 0.4 s the line carries the title back to the left and the new front comes in behind it. The hint buttons stay put. With reduced motion the face changes at once. |
| D39 | Score decay | The score loses 5 points every 1.5 s after the grace period instead of 10 every 3 s: the same rate in smaller, more frequent steps (D17's formula amended). |
| D40 | Distribution | An Android APK replaces the PWA: Capacitor wraps the same Svelte build in a WebView, so nobody installs from a website. `vite-plugin-pwa` and the service worker go. Amends D1 and D3; iOS and desktop are out of scope. |
| D41 | Deck delivery | The deck is bundled in the APK under `/deck/`, so the app is offline from first launch; a new deck ships as a new APK. The Pi module and `deploy-deck` go. |
| D42 | APK build | Nix builds the APK: `packages.apk` runs Gradle offline against a `gradle.fetchDeps` lockfile and the Android SDK from `androidenv`. `nix run .#apk` adds the working tree's deck, signs and optionally installs. |
| D43 | Audience and signing | Sideloaded to your phone and friends' (adb or the file). Signed with this machine's Android debug key (`~/.android/debug.keystore`) outside the Nix store; keep that file, since updates need the same key. The `personal` profile stays (D26). |
| D44 | Application id | `com.nouritsu.karteikasten`. It never changes: another id is another app, with empty progress. |
| D45 | APK versions | versionName is the app version plus the deck version (`0.1.0+2026.10.06-bdc9ce1`); versionCode is the commit count, so a new deck without a new commit needs `--version-code`. |
| D46 | No pictures | The Bild hint and its sheet go: a picture gives the answer away, and approving images noun by noun was manual work for little gain. With them go ARASAAC, OpenMoji with the CLDR annotations, the Köper norms, `is_concrete`, `emoji`, `overrides/images.toml` and the concreteness labels. The four hint buttons that remain sit two to a row. Replaces D11; amends D31; the profiles of D26 stay, without `is_concrete`. |
| D47 | Nix layout | A plain flake replaces flake-parts with the dendritic pattern and import-tree: each package is a `callPackage` file under `nix/`, and `flake.nix` wires the apps, dev shell, checks and formatter itself. alejandra, run by treefmt as `nix fmt`, replaces nixfmt. The dev shell is devenv in flake mode with the house style from `nouritsu/conf-nixos`, so direnv and `nix flake check` need `--no-pure-eval`. The flake targets x86_64-linux only, where androidenv's SDK tools run. |
| D48 | Stage storage | Stage 20 keeps the German entries of both Kaikki editions as JSONL extracts in `data/work/kaikki/`, with byte-offset indexes, and builds the lexicon in Python; DuckDB counts the Leipzig corpora. Stage outputs are cached in `data/work/cache/` under a hash of their inputs (lock hashes, overrides, settings) and of the code that computes them. `deck.sqlite` stays the canonical deck. Replaces stage 20's `lex_*` tables and the parquet stage outputs. |
| D49 | Cognate filter | A cognate hint ships only when the English word the etymology names is among the word's own English glosses (plural, -ed and -ing endings folded): Haus → house stays, schon → pretty goes. `words.toml` `[no_cognate]` drops any wrong hint that remains. This is stage 40's exceptions list. |
| D50 | Modal verbs | Verbs get a fourth class, `modal`, as language teaching does: the six verbs in the English edition's "German modal verbs" category (können, müssen, dürfen, sollen, mögen, wollen); the card says "Modalverb". Other verbs Wiktionary classes as preterite-present (wissen: weiß, wusste, gewusst) are `mixed`, where teaching materials list wissen. |
| D51 | Abbreviations | Abbreviations stay in the deck (they are everyday vocabulary). A word whose only Wiktionary senses are abbreviations takes them as its English glosses ("abbreviation of Doktor") and is flagged `abbreviation`; abbreviated nouns need no gender, plural or genitive, so the noun checks and coverage fields skip them. |
| D52 | Export target | Export writes `Documents/Karteikasten/karteikasten-YYYY-MM-DD.json` on the phone through `@capacitor/filesystem`, without asking each time; a Syncthing folder can sync it later (D22). Android 11 and newer need no permission for files the app creates. Import picks the file with the system file picker. Replaces "Export downloads". |
| D53 | New words | A new word runs like a review: Bereit shows only the word, the score runs, and Weiß ich / Weiß ich nicht give its first FSRS rating. A known word is done in one card (a high score is Easy); an unknown one shows its meaning and comes back within minutes as a learning card. No Intro, no Kenne ich schon on the card, no separate check; Kenne ich schon stays a Wörter action. Words left from an Intro before D53 get their scored check first. Replaces D16's Intro; its 15 new words a day stay. |
| D54 | Pages | Five pages along a bottom tab bar replace the Menü: Karte │ Statistik │ Wörter │ Optionen │ Info, switched by a tap or a swipe, the accent line under the current tab sliding with the page. Suche is Wörter's search field. Formen, Wort and Lizenzen open as panes that hang below their page and push it up, instead of sheets over it. Thema and the language switch move into Optionen; the layout ratios and the score/nav order go. Replaces D31's Menü; amends D19, D35 (a row in Optionen) and D37 (the circle grows from Optionen's Variante button). |
| D55 | Status block | Titled "Status", since a page is now called Statistik. Amends D33. |
| D56 | Controls | fast-track's controls: buttons set into a block's border (Schließen at the right of a pane's top edge, a block's own actions in its bottom edge), word buttons in brackets that read muted when off, `<` `>` steppers that repeat while held and follow a drag, red for whatever closes, resets or deletes, and a second press for Zurücksetzen. The answer and hint buttons stay full buttons inside their blocks. |
| D57 | Icons | Material Icons (Apache 2.0), drawn inline as SVG in the accent, on buttons and before block titles, replace the Unicode symbols; the Noto Sans Symbols 2 subset goes. Replaces D27. |
| D58 | Theme and colours | Variante: Mocha, Latte, or System, which follows the phone's dark mode. The accent and the four gender colours are picked from Catppuccin's fourteen accents; the defaults stay mauve, and blue, red, green and pink. Amends D30. |
| D59 | Display | Schriftgröße (System, Klein, Normal, Groß), Bewegung and Haptik (System, An, Aus) and Uhr (System, 24 h, 12 h). System reads Android's font scale, Remove animations, touch feedback and 24-hour setting through a small native plugin. Replaces the haptics on/off setting. |
| D60 | Statistik | A scrolling column of blocks: Überblick, Verlauf, Punkte, Behalten, Abdeckung, Tage (the 12-week heatmap), Rhythmus, Rekorde and Problemwörter. A span in Überblick's top edge (30 days, 90 days, a year, all, or any range) sets what they cover, set against the span before with ▲ ▼; Rekorde and Problemwörter cover all time. Charts are SVG on the text grid, read by touch; ⇅ Ordnen reorders blocks or puts them away. |
| D61 | Info | Adjektivendungen, Quellen (each source's licence; a search lists a word's own credits from `attribution.json`) and Über with the app and deck versions and the credits; a Lizenzen pane shows the bundled THIRD_PARTY_NOTICES.md. |
| D62 | Backup and privacy | Eine Datei behalten writes `karteikasten.json`, replaced each time, instead of a dated file; regular exports run on an OnCalendar schedule with the app closed. Android's cloud backup of the app's data stays off unless switched on under Privatsphäre. Amends D52; replaces Phase 7's export nudge. |
| D63 | Study reminder | A daily notification at a set time, on days with cards due and no reviews yet. Each time the app goes to the background it schedules the next week's reminders with the counts they will have, so they are right with the app closed. |
| D64 | Debug build | `nix run .#apk-debug -- --install` installs "Karteikasten (debug)" as `com.nouritsu.karteikasten.debug`, with its own storage, beside the release app. D44's id stays the release app's. |
| D65 | Launcher icon | fast-track's icon with Material Icons' translate glyph (文A) in place of its fork and spoon (`app/icon.svg`), a monochrome twin for Android's themed icons, and a status-bar icon for the reminder. |
| D66 | English UI | The app speaks English only, to English speakers learning German: one `strings.ts`, no German UI and no language switch. German is the content: the word, its forms and its sentences. The card's meaning is always the English glosses, and the answer view always adds the sentence's English translation; the German definitions stay in the deck but no longer show. The spec's German names stay as names; the app says Ready!, Know it / Don't know, I was wrong, Next, Done for today!, Score, Cognate, and Card │ Stats │ Words │ Options │ Info. Regular exports read English schedules only. Replaces D20; amends D8, D35 and D54 (no Sprache row). |
| D67 | Level | Options → Study → Level: Beginner, A1.1, A1.2, A2.1, A2.2, B1.1 or B1.2, at ranks 0, 100, 250, 500, 800, 1,200 and 1,600, a first guess at CEFR from frequency. Words up to the level's rank come as quick checks, 20 a day (a setting), under their own limit; new words start after the rank. A check is a scored card like any other (D53): known, it is Easy and back in about a week, then months; missed, it is learnt. When 48 of the last 50 first answers on the words the next level would cover were known, Done for today suggests it; only you change the level. Your export of 2026-11-21 knew 30 of the first 31 words on sight, missing "sich". |

## Implementation defaults

These choices fill gaps the decisions leave open; change any of them without a new decision, but note the change in the commit or PR.

- Package name `karteikasten`, application id `com.nouritsu.karteikasten` (D44); inside the APK the app lives at `/`, deck data at `/deck/`.
- App: Svelte 5 + Vite (no SvelteKit), Capacitor for Android (D40), `idb` for IndexedDB, Vitest, npm with `package-lock.json` (built with `buildNpmPackage`).
- Styling: small hand-rolled CSS components (Block with inset title, Button, Bar, Table). `@webtui/css` is only a visual reference.
- Font: Iosevka (SIL OFL), subset to Latin, Latin Extended-A, IPA Extensions, Spacing Modifier Letters, Combining Diacritical Marks, General Punctuation, Box Drawing and Block Elements, plus ≈ and the icon symbols (D27). No emoji.
- Themes: Catppuccin Mocha (dark, default) and Latte (light), mauve accent (D30).
- Event ids are ULIDs; the day rolls over at 04:00 local time; desired retention is 0.9.
- Audio plays once automatically after answering (setting, on by default).
- Vulgar words stay in the deck, tagged from Wiktionary labels.
- APK: Gradle and the Android SDK from nixpkgs, Maven dependencies pinned in `nix/apk-deps.json` (D42).
- Tooling: alejandra via `nix fmt` (D47), `pytest`, `cargo test` + `clippy`, Python 3.12 or newer.

## Architecture and Nix

The desktop pipeline builds a versioned deck bundle, Nix packs it with the app into an APK (D41), and the phone keeps all progress locally as an append-only review log.

&#91;embedded content: system overview · desktop, phone (the Pi went with D41)\]

Data moves left to right on the desktop and into the phone with each APK; progress only leaves the phone as an export file.

- Pipeline (desktop): Python + DuckDB, run with `nix run .#build`. Its only output contract is the deck bundle.
- App and deck ship together: the web build is a Nix package, and `nix run .#apk` bundles it with a deck from `data/dist/deck/` (D41).
- Phone: progress lives in IndexedDB as review events; card state is derived and cached.
- Curation tool (desktop): reads the curation database and writes `overrides/*.toml`, which the next build applies.

Repo layout:

```
karteikasten/
├─ flake.nix              # inputs, apps, dev shell, checks, formatter (D47)
├─ flake.lock
├─ .envrc                 # use flake . --no-pure-eval
├─ nix/                   # one callPackage file per package (D47)
│  ├─ pipeline.nix        # packages.pipeline, wrapped as apps fetch, build, report
│  ├─ app.nix             # packages.app (static web build)
│  ├─ app-assets.nix      # packages.app-assets (font subsets, icons)
│  ├─ apk.nix             # packages.apk (Capacitor + Gradle)
│  ├─ apk-app.nix         # nix run .#apk (bundle a deck, sign, install)
│  ├─ apk-deps.json       # Gradle dependency lockfile
│  ├─ stub-deck/          # empty deck for checks.apk
│  ├─ curate.nix          # packages.curate (ratatui tool)
├─ config/pipeline.toml   # n_max, blend weight, profile
├─ sources.lock.json      # url, retrieved_at, bytes, sha256 per raw file
├─ pipeline/              # Python package; deps come from Nix
│  ├─ karteikasten_pipeline/{fetch,stages,sql}/
│  └─ tests/
├─ overrides/             # human curation, committed
│  ├─ words.toml
│  ├─ closed_classes.toml
│  ├─ sentences.toml
│  └─ audio/              # own recordings
├─ curate/                # Rust + ratatui
├─ app/                   # Svelte 5 + Vite
│  ├─ android/            # Capacitor's Android project
│  └─ src/lib/{engine,store,stats,pages,panes,ui}/
├─ docs/                  # SPEC.md (export of this doc), sources/*.md
├─ reports/               # coverage and diff reports
└─ data/                  # gitignored
   ├─ raw/                # source snapshots
   ├─ work/               # Kaikki extracts, stage cache, processed audio, curation.sqlite (D48)
   └─ dist/deck/<version>/
```

Nix files (D47):

- `flake.nix`, dev shell: devenv with the `nouritsu/conf-nixos` house style; `python3.withPackages` (duckdb, httpx, pytest, a CoNLL-U reader or a small parser), `duckdb` CLI, `sqlite`, `ffmpeg`, Node.js LTS, qrencode, Rust toolchain (cargo, rustc, clippy, rustfmt, rust-analyzer), Gradle, JDK 21, adb with `ANDROID_HOME`, alejandra.
- `flake.nix`, the rest: the apps; `checks` (formatting, pytest, svelte-check and Vitest, cargo test and clippy, the APK with the stub deck); `formatter`.
- `pipeline.nix`: `packages.pipeline`, the Python CLI; `flake.nix` wraps it in fish via `pkgs.writers.writeFishBin` as `nix run .#fetch`, `.#build`, `.#report`.
- `app.nix`: `packages.app` via `buildNpmPackage`; output is static files. `app-assets.nix` supplies its font subsets and icons.
- `apk.nix`: `packages.apk`, an unsigned release APK with the stub deck; `apk-app.nix` is `nix run .#apk`, which bundles a real deck and signs it (D42, D43).
- `curate.nix`: `packages.curate` via `rustPlatform.buildRustPackage`; `nix run .#curate` wraps it with ffmpeg, ffplay and the pipeline on PATH.

Flake builds only see git-tracked files, and `data/` is gitignored, so the pipeline runs via `nix run` in the working tree. Determinism comes from `sources.lock.json` and `flake.lock`, not from the Nix sandbox.

## Data sources

Nine sources feed the deck, each pinned in `sources.lock.json`; only openly licensed data ships, and DeReWo stays a private cross-check.

| Source | Used for | Licence | Ships? | Where |
| --- | --- | --- | --- | --- |
| FrequencyWords, OpenSubtitles 2018 (de) | Spoken word-form counts | CC BY-SA 4.0 | Derived ranks only | [FrequencyWords](https://github.com/hermitdave/FrequencyWords), `content/2018/de` |
| Leipzig Corpora Collection, German news + web (1M sentences each) | Written counts, case ratios | CC BY (downloads) | Derived ranks only | [Leipzig downloads](https://wortschatz.uni-leipzig.de/en/download/German) |
| DeReWo (IDS Mannheim) | Private sanity check of ranks | Non-commercial; no redistribution without its documentation | Never, and never committed | [DeReWo](https://www.ids-mannheim.de/en/s/corpus-linguistics/projects/methods-of-analysis/corpus-based-lemma-and-word-form-lists/) |
| Universal Dependencies German GSD + HDT | POS ratios for ambiguous forms; separable-verb ratio | Check each repo's LICENSE | Ratios only | github.com/UniversalDependencies |
| Kaikki, English-Wiktionary German dictionary | POS, gender, IPA, English glosses, forms, categories, etymology, examples, audio URLs | CC BY-SA | Yes | [raw-wiktextract-data.jsonl.gz](https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz), German entries extracted (D23) |
| Kaikki, German-Wiktionary extract | German definitions, hyphenation, IPA and forms cross-check | CC BY-SA | Yes | [de-extract.jsonl.gz](https://kaikki.org/dictionary/downloads/de/de-extract.jsonl.gz), about 294 MB |
| Wikimedia Commons | Audio files, per-file author and licence | Per file | Yes | Kaikki `ogg_url`/`mp3_url` + Commons API `imageinfo` `extmetadata` |
| Tatoeba | Sentences, English translations, native-speaker filter | CC BY 2.0 FR (some CC0) | Yes | [Tatoeba downloads](https://tatoeba.org/en/downloads), updated weekly |
| Own recordings | Audio gaps | Yours | Yes | `overrides/audio/` |

Fetch rules:

- Kaikki and Tatoeba change weekly at unversioned URLs. Snapshot into `data/raw/` and record URL, time, size and sha256; `fetch --refresh` is always explicit.
- Wikimedia: descriptive User-Agent with contact, Commons API batched at 50 titles per request, at most 2 requests per second per host.
- Fetch only the \~2,000 audio files needed, never Kaikki's 20 GB bulk audio archive.
- Leipzig's terms forbid automated querying of its website; use the download files only.

&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;&#32;

## Pipeline stages

`nix run .#build` runs stages 20–70 over the snapshot in `data/raw/`; the same inputs must give byte-identical outputs. Stage results are cached in `data/work/cache/` (D48); `--fresh` recomputes everything and `--offline` fails rather than fetch Commons data the snapshot lacks.

- Stage 10 · fetch (network): download every source into `data/raw/` and update `sources.lock.json`.
- Stage 20 · lexicon: extract the German entries of both Kaikki editions to JSONL with byte-offset indexes, and build the lexicon (lemmas, forms, etymology ids, separable particles, contractions, ordinals) from them (D48).
- Stage 30 · frequency and lemmas:
  - Convert spoken and written word-form counts to per-million.
  - Map each form to its candidate (lemma, POS, etymology) via Kaikki `form_of` links and each lemma's `forms` list.
  - If a list is case-folded, split case variants (Essen/essen, Sie/sie) by Leipzig case ratios.
  - Split forms with several lemmas by P(lemma, POS given form) from the UD treebanks, add-one smoothed. Unseen forms split evenly and get flagged.
  - Separable verbs (anfangen): estimate from unsplit forms (infinitive, Partizip II, zu-infinitive, verb-final forms). Scale by the split/unsplit ratio of particle verbs (`compound:prt`) measured in UD.
  - Remove the split uses counted elsewhere (D25): discount each base verb by its UD share of tokens that head a separated particle, and each particle by its UD share of PTKVZ uses.
  - Blend: weighted geometric mean of per-million frequencies, spoken weight 0.7, small epsilon.
  - Filter: drop proper nouns, tokens without a German Wiktionary entry, digits, and fillers listed in `overrides/words.toml`. Keep interjections such as ja, nein, danke, bitte, hallo.
  - Output per word: rank, stable id, `token_share` (share of all tokens), cumulative coverage.
- Stage 40 · enrich:
  - Key forms and tables per word type (next section).
  - Up to 3 English glosses and 3 German definitions; strip wiki markup; keep register labels as tags.
  - IPA preferring Germany; syllables from German-Wiktionary hyphenation; stress from the IPA stress mark. When syllable counts disagree: no highlight and a report entry.
  - Gender and article; function-word flag; closed classes merged from `overrides/closed_classes.toml`.
  - Cognate from etymology text ("cognate with English X", "compare English X"), kept only when X is among the word's English glosses, plus `[no_cognate]` in `words.toml` (D49).
  - Case tables for articles, determiners and pronouns; ordinals for numerals; preposition contractions.
- Stage 50 · media:
  - Audio: candidates from Kaikki sounds. Prefer the Commons author covering most of the deck; words they lack fall through to the author with the next most coverage, and so on (D24). Regional files only as a last resort, tagged. Own recordings always win.
  - Audio processing: fetch author and licence, then ffmpeg trims silence to 100 ms padding, normalizes to about −16 LUFS, and writes mono MP3 at about 48 kbps.
- Stage 60 · sentences:
  - Candidates: Tatoeba sentences with English translations, plus Wiktionary usage examples (never quotations, which cite outside works). Sentences and translations without a named author are left out.
  - Match any inflected form; for separable verbs, stem and particle must both appear, particle later.
  - Keep 4–10 tokens, prefer native authors (Tatoeba level 5), skip sentences tagged as needing review. Store the top 5 per word.
- Stage 70 · bundle: write the deck bundle. `--profile personal|public`; `personal` (the development build) uses the whole data set; `public` drops NC/ND items such as NC-licensed audio (D26, D46).

Stable ids are `lemma#pos#n`, with n the etymology number (default 1): `Bank#noun#1` (Bänke) vs `Bank#noun#2` (Banken), `sein#verb#1` vs `sein#det#1`. Pins live in `overrides/words.toml`, and an id is never reused for another meaning.

## Forms per word type

Each word shows a few key forms on the card and full tables behind the Formen button, taken from Kaikki `forms` with tags and cross-checked against the German-Wiktionary extract.

| Word type | Key forms on the card | Full tables (Formen) |
| --- | --- | --- |
| Noun | Article/gender, plural, genitive singular. Flags: weak noun (der Junge → des Jungen), plural-only, singular-only | 4 cases × singular/plural, with articles |
| Verb | er-form; du-form if the stem changes (du fährst); Präteritum (er); Partizip II with haben/sein. Flags: separable prefix, reflexive, strong/weak/mixed/modal (D50) | Present (6 persons), Präteritum (6), imperative (du/ihr/Sie), Konjunktiv II for modals and haben/sein/werden |
| Adjective | Comparative, superlative (am …sten), irregular stem (hoch → hohe), predicative-only flag | None per word; the generic ending table sits in Info |
| Adverb | Comparison where it exists (gern → lieber → am liebsten) | None |
| Article, determiner, pronoun | None | Case × gender/number table |
| Preposition | Case governed (Akk, Dat, two-way, Gen); contractions (im, am, ins, zum, zur, beim, vom) | None |
| Conjunction | Coordinating vs subordinating (verb goes to the end) | None |
| Numeral | Ordinal | None |
| Particle, interjection | Flag "kontextabhängig": usage only | None |

Closed classes (about 30 core prepositions, the conjunctions, articles and pronouns) are hand-checked against Wiktionary and stored in `overrides/closed_classes.toml`.

## Deck bundle and overrides

A deck is a versioned, content-addressed directory named `YYYY.MM.DD-<short hash of inputs>`, so identical inputs give an identical deck. The date is the snapshot's (its latest retrieval in `sources.lock.json`), not the build's; the inputs are the snapshot, the overrides, the settings, the pipeline code and the ffmpeg version. Of the Commons recordings in the snapshot, only those the deck uses count, so one fetched just to listen to in the curation tool changes nothing.

```
data/dist/deck/<version>/
├─ manifest.json      # schema_version, deck_version, n_max, profile, input hashes, counts, coverage summary
├─ deck.sqlite        # canonical
├─ words.json         # denormalized; what the app loads
├─ attribution.json   # every source and every media item / sentence credit
├─ coverage.md        # human-readable report
└─ media/
   └─ audio/<sha1>.mp3
```

SQLite tables:

| Table | Columns |
| --- | --- |
| `word` | `id` PK, `rank`, `lemma`, `pos`, `gender`, `article`, `token_share`, `coverage_cum`, `ipa`, `syllables`, `stress_syllable`, `cognate_en`, `flags` JSON, `key_forms` JSON, `tables` JSON, `gloss_en` JSON, `gloss_de` JSON, `audio_id`, `provenance` JSON |
| `sentence` | `id`, `word_id` (together the PK: one sentence can serve several words), `position`, `de`, `en`, `source`, `source_ref`, `author`, `license`, `en_author`, `en_license`, `native`, `deck_token_ids` JSON, `out_of_deck`, `hl_start`, `hl_end`, `score` |
| `media` | `id` PK, `kind`, `path`, `source`, `source_url`, `author`, `license`, `license_url`, `sha256`, `duration_ms` |
| `source` | `id` PK, `name`, `url`, `license`, `retrieved_at`, `sha256` |

`words.json` holds one object per word, with up to 5 sentences and media paths inlined.

The pipeline also writes `data/work/curation.sqlite`: all audio and sentence candidates, the current picks, and QA issues. The curation tool reads it and writes overrides.

Overrides are committed and re-applied on every build; an override that no longer matches anything fails the build.

- `words.toml`: include/exclude, pinned ids, merges and splits, hidden or reordered senses, manual gloss fixes (provenance `manual`). Phase 3 implements `[exclude]`, `[merge]`, `[gloss_en]` and `[gloss_de]` (which also hide or reorder senses) and `[no_cognate]` (D49); Phase 4 adds `[audio]`, the Commons file a word uses instead of the build's pick (one of its candidates, with author and licence). The rest comes when the curation tool needs it.
- `closed_classes.toml`: prepositions (case, contractions), conjunctions (type), article and pronoun tables. Drafted from both editions' categories and tags by `python -m karteikasten_pipeline.draft`, then checked by hand; the tables come from the data (stage 40).
- `sentences.toml`: pinned and banned sentences, `[pin]` and `[ban]` by word id.
- `audio/`: own recordings, named by word id with `#` replaced by `_` (`Hand_noun_1.flac`).

## App layout and look

The app is five portrait pages along a bottom tab bar, Karte │ Statistik │ Wörter │ Optionen │ Info, switched by a tap or a swipe (D54). Karte, the study screen, is three stacked blocks: status, card and score share the height 20/60/10. Formen, Wort and Lizenzen hang below their page as panes. They are styled like ratatui but drawn with HTML/CSS; `docs/mockups.md` draws every page and pane.

- Monospace everywhere. Each block has a 1 px border with rounded corners and its title inset in the top border, like a ratatui Block; buttons can sit in a border too (D56).
- Text sizes are multiples of the base size, which Schriftgröße sets (D59). The word auto-fits the card width between 1.5× and 3×; nothing else scales.
- Gender colours are theme tokens: der blue, die red, das green, plural-only purple (pink in Catppuccin, where purple is the accent; D30); the accent and all four can be picked (D58).
- Icons are Material Icons drawn as SVG (table below, D57); the mockups draw the nearest Unicode symbol.
- Mockup content is illustrative; real content comes from the pipeline. The mockups below predate D54 and use 34 × 30 cells; `docs/mockups.md` uses 44 columns, about what a 375 px phone shows.

Bereit (every card starts here; all status fields dashed, buttons disabled):

```
╭─ Statistik ─── Mittwoch 16:04 ─╮
│ Rang #--- · ----- · ---        │
│ Heute -- · Gesamt ---          │
│ Fällig -- · Neu - · Serie -    │
│ Abdeckung [------------] --%   │
│ Sitzung --:-- · Ø -- Punkte    │
╰────────────────────────────────╯
╭─ Karte ────────────────────────╮
│                                │
│                                │
│                                │
│                                │
│                                │
│            Bereit!             │
│                                │
│                                │
│                                │
│                                │
│                                │
├────────────────────────────────┤
│ [Audio]         [Formen]       │
│ [Satz]          [Verwandt]     │
╰────────────────────────────────╯
╭─ Punkte: -- ───────────────────╮
│ [Weiß ich nicht]  [Weiß ich]   │
╰────────────────────────────────╯
╭─ Menü ─────────────────────────╮
│ [⛭] [⏾] [de] [▥] [🕮] [⌕] [ⓘ]   │
╰────────────────────────────────╯
```

Läuft (word revealed, clock running; here Satz was picked, so its sentence has typed in below the word, which stays put; Menü unchanged):

```
╭─ Statistik ─── Mittwoch 16:04 ─╮
│ Rang #312 · Nomen · die        │
│ Heute 12 · Gesamt 412          │
│ Fällig 31 · Neu 6 · Serie 5    │
│ Abdeckung [######......] 41%   │
│ Sitzung 04:12 · Ø 72 Punkte    │
╰────────────────────────────────╯
╭─ Karte ────────────────────────╮
│                                │
│                                │
│                                │
│                                │
│            die Hand            │
│             [hant]             │
│                                │
│ Gib mir deine Hand.            │
│                                │
│                                │
│                                │
├────────────────────────────────┤
│ [Audio]         [Formen]       │
│ [Satz]          [Verwandt]     │
╰────────────────────────────────╯
╭─ Punkte: 70 ───────────────────╮
│ [Weiß ich nicht]  [Weiß ich]   │
╰────────────────────────────────╯
```

Beantwortet after Weiß ich (score frozen, hints free, undo offered; the meaning in the UI language, German here; status and Menü unchanged):

```
╭─ Karte ────────────────────────╮
│                                │
│            die Hand            │
│             [hant]             │
│                                │
│ 1. Greiforgan bei Menschen     │
│ Pl. die Hände                  │
│                                │
│ Gib mir deine Hand.            │
│                                │
├────────────────────────────────┤
│ [Audio]         [Formen]       │
│ [Satz]          [Verwandt]     │
╰────────────────────────────────╯
╭─ Punkte: 70 ───────────────────╮
│ [war doch falsch]  [Weiter]    │
╰────────────────────────────────╯
```

| Element | Material icon (D57) |
| --- | --- |
| Audio | volume_up |
| Formen | table_chart |
| Satz | notes |
| Verwandt | link |
| Wörter, Quellen | menu_book; Suche: search |
| Thema, Variante | contrast; dark_mode, light_mode or brightness_auto for Mocha, Latte or System |
| Statistik's blocks | insights, bar_chart, speed, psychology, pie_chart, calendar_month, schedule, emoji_events, warning |
| Info | info; Lizenzen: gavel |
| Schließen, Standard, Ordnen | close, restart_alt, swap_vert |

## Card flow and score

Every card runs Bereit → Enthüllen → Läuft → Beantwortet → Weiter, new words included (D53).

&#91;embedded content: card states · 5 states, 2 paths\]

Weiter always returns to Bereit, and the clock runs only in Läuft. (The diagram's Intro path is gone, D53.)

1. Bereit: the card shows Bereit! as large plain text and no greeting (D28, D34). Every status-bar field shows dashes at its normal width; hint and answer buttons are disabled. On the first open of a day, a word of the day (an already-known word with its best sentence) sits above the button.
2. Enthüllen: status fields fill in. The word with its article appears by letter shuffle: each letter cycles random letters of the same case (including ÄÖÜß) and locks left to right with about 50 ms stagger, 700 ms at most. IPA and syllables fade in after. With `prefers-reduced-motion`, the word appears at once.
3. Läuft: the clock starts when the last letter locks. The score decays, hints cost points, and the buttons are Weiß ich nicht and Weiß ich. The score shows in the Punkte block's title, shuffling on every change, and the number and border fade to its band's colour (D29). Hint buttons show no costs; a press that costs points flashes its deduction on the button, and Satz types its sentence in below the word (D32).
4. Beantwortet: the meaning (in English, D66), key forms and the chosen sentence show; hints are free; audio plays once if that setting is on. After Weiß ich, the score bar offers "war doch falsch" (undo) and Weiter; undo stays available until Weiter. After Weiß ich nicht, only Weiter.
5. New words (D53): the same flow; the first answer is the word's first FSRS rating. Weiß ich nicht makes it a learning card that comes back within minutes; Weiß ich with a high score (Easy) schedules it days ahead.

The clock pauses while the page is hidden (`visibilitychange`) and resumes when it is visible again.

```latex
\text{score} = \min\left(100,\ \max\left(0,\ 100 - 5\left\lfloor \frac{\max(0,\ t_{\text{active}} - 2\,\text{s})}{1.5\,\text{s}} \right\rfloor - \sum \text{penalties}\right)\right)
```

| Event | Effect |
| --- | --- |
| Audio, first play before answering | −10 |
| Formen | −15 |
| Satz | −20 |
| Verwandt (cognate) | −30 |
| Any hint after answering | Free |
| Weiß ich nicht | Score 0, FSRS Again |
| Weiß ich with score 0–39 | FSRS Hard |
| Weiß ich with score 40–84 | FSRS Good |
| Weiß ich with score 85–100 | FSRS Easy |
| war doch falsch (undo) | Score 0, FSRS Again |

Each hint is charged once per review. Every number here (start, step, decay, grace, penalties, grade bands) is a setting.

## Scheduling, storage and sync

Reviews are append-only events in IndexedDB; FSRS card state is derived from them, cached, and must always equal a full replay.

Scheduling:

- ts-fsrs (FSRS-6), desired retention 0.9, fuzz on, short-term learning steps per ts-fsrs defaults. Check current API names against its docs.
- Queue order: words left from an Intro before D53 and never rated, learning and relearning cards due now, then reviews due before the next rollover (oldest first), then the level's checks by rank up to their daily limit (20, D67), then new words by rank past the level up to the daily limit (15; a word counts on the day of its first answer). With nothing else left, a learning card due within the learn-ahead window (20 minutes, a setting); otherwise Feierabend, which picks up a card as soon as it comes due.
- The day rolls over at 04:00 local time.

Storage and offline:

- IndexedDB stores: `events`, `cards` (derived cache, rewritten from a full replay at every start), `settings`, `meta`. Call `navigator.storage.persist()` on first run.
- An answered review is kept in `meta` until Weiter writes its event (undo changes it there); if the app closes first, the next start writes it as it stood, so no answer is lost.
- Deck loading: `/deck/latest.json` → `/deck/<v>/manifest.json` + `words.json`, all inside the APK (D41).
- New deck version: arrives with an APK update. Progress follows stable ids; orphaned ids keep their history and are listed, never deleted.
- IndexedDB lives in the app's data: an update with the same id and key keeps it (D43, D44); uninstalling or clearing the app's storage deletes it, so export is the only backup.

Event shape:

```json
{
  "id": "01J9X3…",
  "type": "review | intro | known | suspend | unsuspend | reset",
  "word_id": "Hand#noun#1",
  "ts": "2026-10-06T08:15:02.120Z",
  "deck_version": "2026.10.06-ab12cd3",
  "app_version": "0.1.0",
  "review": {
    "shown_at": "…", "ready_at": "…", "answered_at": "…",
    "answer": "know | dont_know", "undo": false,
    "score": 72, "hints": ["audio"], "active_ms": 6400, "grade": 3
  }
}
```

Export and import:

- Export writes `Documents/Karteikasten/karteikasten-YYYY-MM-DD.json` (D52): `{format: "karteikasten-backup", version: 1, exported_at, device_id, settings, events}`; `settings` also carries the language and theme.
- Import merges events by id (idempotent union); restoring settings is optional. Optionen shows "Letzter Export vor N Tagen" and nudges after 7 days.
- Syncthing later: export files land in a synced folder, and merging stays a union of events.

Languages:

- UI strings live in `app/src/lib/strings.ts`, in English only (D66).
- The meaning is the English glosses, and the answer view adds the sentence's English translation (D66).

## Status bar and screens

The status block, titled Status (D55), carries eleven fields, all dashed during Bereit, under a title with the weekday and time (D33). The tabs lead to four pages besides Karte (D54), and Feierabend! closes each session.

| Field | Meaning |
| --- | --- |
| Heute | Reviews answered today (since 04:00) |
| Gesamt | Reviews answered all time |
| Rang | The word's rank in the top-n list |
| Wortart | Word type |
| Artikel | der/die/das, in the gender colour |
| Fällig | Due cards left today |
| Neu | New words left today |
| Serie | Days in a row with at least one review |
| Abdeckung | Sum of `token_share` over known words (FSRS state Review, or Kenne ich schon) |
| Sitzung | Session time |
| Ø Punkte | Session average score |

| Screen | Contents |
| --- | --- |
| Optionen | Thema: Variante (Mocha, Latte, System) and Farben (D58); Anzeige: Schriftgröße, Bewegung, Haptik, Uhr (D59); Lernen: Level and checks a day (D67), daily new limit, n (up to the deck's `n_max`), desired retention, learn-ahead, audio after answer; Punkte: all score numbers and grade bands; Erinnerung (D63); Sicherung: export and import, one file, regular exports (D62); Privatsphäre: cloud backup (D62) |
| Statistik | A span (30 days, 90 days, a year, all, a range) against the span before; Verlauf, Punkte, Behalten, Abdeckung per rank band, Tage (the 12-week heatmap), Rhythmus, Rekorde, Problemwörter; reorder or put away (D60) |
| Wörter | All n words with rank, lemma, type and status; filters by status, type and gender; the Wort pane with all data and no scoring; actions Kenne ich schon, Pausieren, Zurücksetzen |
| Suche | Wörter's search field (D54); umlaut-tolerant (ae matches ä), lemmas first, then meanings |
| Info | The adjective-ending table, sources and per-item credits (searchable), deck and app versions, the Lizenzen pane (D61) |
| Feierabend! | Shown when the queue is empty: reviews, average score, new words, streak, coverage change, cards due tomorrow |

Haptics: one short vibration on Weiß ich and a double one on Weiß ich nicht, through the Vibration API of Android's WebView (D40); Haptik turns it on, off, or leaves it to the phone's touch feedback (D59).

## Curation tool

`nix run .#curate` opens a ratatui TUI that turns pipeline candidates into committed overrides.

- Reads `data/work/curation.sqlite` (every word's card, all audio candidates, the best 20 sentence candidates, the issues); writes `overrides/words.toml` `[audio]`, `overrides/sentences.toml` `[pin]`/`[ban]` and `overrides/audio/`. Each change is saved at once with toml_edit, so comments and layout survive; the next build applies it, and the header says when overrides are newer than the database.
- Views: issue queue (blocking first, then by rank; `t` shows every word), and a word view with its card, the audio picker with the recorder, and the sentence picker.
- Commands in `curate/curate.toml`: `record_cmd` (ffmpeg capture via PipeWire/PulseAudio; r again sends SIGINT so the file is closed properly), `play_cmd` (ffplay) and `fetch_cmd`. Candidates the build did not pick are not in the snapshot; Space fetches them first with `fetch --commons FILE`, which adds them to `data/raw` and `sources.lock.json` like any Commons file.
- Keys: j/k move, Enter open, Tab audio or sentences, a accept (pin), x reject (ban a sentence, unpin audio), n/p next/previous candidate, Space play, r record, / search, Esc back, q quit.

| Severity | Checks |
| --- | --- |
| Blocking | Noun without gender or plural (abbreviations exempt, D51); verb without Partizip II or auxiliary; no English gloss; any item without licence or author |
| Warning | No audio; no sentence; syllable/stress mismatch; audio duration outlier |

An orphaned override fails the build instead of warning (Overrides), so it never reaches the queue.

`nix run .#report -- --diff [OLD [NEW]]` writes `reports/diff.md`: which inputs changed, words entering and leaving the deck, rank moves, card changes per field, coverage, and the issues fixed and new. Without versions it compares the latest deck with the one built before it.

## APK

Nix builds the APK and signs it with this machine's debug key; it is installed by hand (D40–D45).

- `packages.apk`: `app/` with its `android/` Capacitor project, the web build from `packages.app` and a deck, built by Gradle offline. Maven artefacts come from `nix/apk-deps.json`; refresh it after changing Capacitor or Gradle versions with `nix build .#apk.mitmCache.updateScript && ./result`.
- `nix run .#apk -- [--deck VERSION] [--version-code N] [--install]`: bundles the deck named by `data/dist/deck/latest.json` (or VERSION), signs with `~/.android/debug.keystore` (created if missing), writes `data/dist/apk/karteikasten-<versionName>.apk`, and with `--install` runs `adb install -r`.
- Friends get the APK file; Android asks once to allow installs from the app that opens it.
- Optional weekly refresh (systemd timer on the desktop): `fetch --refresh`, build, and a diff report in `reports/`. It never publishes on its own.

## Licensing and attribution

Personal builds use the whole data set, NC items included (D26); public builds drop every NC/ND item and are released under CC BY-SA 4.0.

- Info lists every source and every per-item credit from `attribution.json`.
- DeReWo never enters the repo, the bundle, or any derived file that ships.
- `data/raw/` is never committed.
- Own recordings need a licence before any public release (CC0 suggested).
- Tatoeba credit: link tatoeba.org, name CC BY 2.0 FR, and credit each sentence's author.
- Commons audio: credit each file's author and licence exactly as the API returns them.

## Phases

Eight phases run in order, Phases 1 and 2 in parallel, and each ends with a short report and your review before the next starts.

&#91;embedded content: roadmap · 8 phases, 7 gates\]

Phase 0 unlocks both spikes, and Phase 3 starts only after the coverage report and the phone test both pass.

- Phase 0 · Foundations
  - Repo skeleton as in Architecture; a plain `flake.nix` (D47); devShell; `.envrc`; `.gitignore` (`data/`, `result*`, `node_modules/`, `target/`).
  - Stub apps (`fetch`, `build`, `report`) that print TODO; Svelte scaffold; `cargo new curate`; server module stub (gone with the Pi, D41); `nix flake check` with alejandra (D47).
  - Done when `direnv allow` gives python+duckdb, node, cargo and ffmpeg (and vips until D46); `nix flake check` passes; `nix build .#app` builds the scaffold.
- Phase 1 · Data spike (top 100 words)
  - Fetchers for every source, with `sources.lock.json`; field notes per source in `docs/sources/`.
  - Work through "Verify in Phase 1" and build a throwaway top-100 deck.
  - Done when `reports/phase1-coverage.md` shows coverage per field plus anomalies, and you have confirmed or amended the decisions here.
- Phase 2 · UI spike (parallel with Phase 1)
  - Fixture data for 3 words; the four blocks; Bereit with dashed fields; letter shuffle; hint buttons; decaying score; answer view; nav icons; font subset; audio; two themes. It started as an installable PWA with a picture overlay; the APK replaced the PWA (D40) and the overlay went (D46).
  - Test on the phone with the APK over adb (`nix run .#apk -- --install`); `app/phone.fish` serves the web build to the phone's browser over the home network for quick looks.
  - Done when the APK installs, works offline from first launch, renders IPA without fallback boxes, and the shuffle and layout feel right to you (D40). Passed on 2026-10-22.
- Phase 3 · Full pipeline (n = 2,000)
  - Stages 20–70 as specified, with `--profile personal|public`.
  - Done when two builds from the same snapshot are byte-identical; every media item and sentence has source, author and licence; pytest passes the tricky-word fixtures; the coverage targets set in Phase 1 are met (confirmed 2026-10-22, last section of `reports/phase1-coverage.md`).
- Phase 4 · Curation and QA
  - Curation tool with issue queue, pickers and recorder; automated checks; build-to-build diff report.
  - Done when the top 500 words have no blocking issues (D46). Passed on 2026-10-22.
- Phase 5 · Core study loop
  - Engine: score state machine, grade bands, queue, ts-fsrs adapter, 04:00 rollover. Storage; deck loader (D41).
  - Full card flow, new words included (D53), undo, dynamic sentence choice, the language button (D35), pause while hidden, haptics; export and import (D52).
  - Done when Vitest covers decay, penalties, bands, undo, pause, queue and replay; export → wipe → import restores identical state; a week of real daily use loses nothing.
- Phase 6 · Screens and polish
  - The pages, panes and controls of D54–D61 as drawn in `docs/mockups.md`: Statistik, Wörter with Suche, Optionen, Info; word of the day, Feierabend!; the backup, privacy, reminder, debug build and icon of D62–D65.
  - Done when every string is in `strings.ts`, every screen works one-handed, and attribution is complete.
- Phase 7 · Deploy and data lifecycle
  - Optional weekly refresh with a diff (D41); scheduled exports (D62) replace the export nudge.
  - Done when an APK with a changed deck installs over the old one with progress intact.
- Phase 8 · Backlog: only on request (see Backlog).

## Testing

Every engine rule and every known pipeline trap gets a test, and the tricky-word fixtures must pass from Phase 3 on.

- pytest (pipeline): small fixture slices of each source, the tricky words below, and determinism (build twice, compare hashes).
- Vitest (app): decay and grace, penalties charged once, floor 0, grade bands, undo, pause/resume, queue limits and order, replay equals cache, idempotent import merge.
- cargo test (curation tool): overrides round-trip through TOML unchanged.
- Optional smoke test with Playwright, using browsers from nixpkgs.

| Word(s) | Checks |
| --- | --- |
| sein (verb) / sein (determiner) | Two ids, split counts |
| die | Article vs pronoun split |
| Bank (Bänke) / Bank (Banken) | Etymology ids, different plurals |
| Essen / essen, Morgen / morgen, Sie / sie | Case handling |
| anfangen, aufhören, ankommen, anrufen | Separable-verb correction lands at plausible ranks |
| Junge, Herr | Weak-noun flag, des Herrn |
| Leute, Eltern | Plural-only |
| haben, werden, können, wissen, fahren | Auxiliaries, modals, stem change |
| sich freuen | Reflexive flag |
| gut, viel, gern, hoch | Irregular comparison, hoch → hohe |
| mit, für, in, wegen | Dative, accusative, two-way, genitive |
| weil, und | Subordinating vs coordinating |
| doch, mal | Particle flag, usage only |
| ja, danke, okay | Interjections kept |
| äh | Filler excluded |

## Verify in Phase 1

These assumptions need real data before Phase 3; record each answer in `docs/sources/` and amend this doc where needed. Answers so far: `reports/phase1-coverage.md`.

- [x] Is FrequencyWords case-folded? Does the Leipzig word list keep case? Which Leipzig corpora (news/web, year) to use.
- [x] Exact Kaikki field paths for forms, tags, sounds, hyphenation and examples in both editions.
- [x] Audio coverage for the top 2,000, the speaker distribution, and which Lingua Libre speaker to prefer (D24).
- [x] Concreteness thresholds: dropped with the pictures (D46).
- [x] ARASAAC API endpoints, rate limits and match rate; OpenMoji/CLDR match rate.
- [x] Licences of UD GSD and HDT, and the terms of the Köper norms (D26).
- [x] Separable-verb correction: anfangen, aufhören, ankommen and anrufen land at plausible ranks (DeReWo cross-check, D25).
- [x] Tatoeba file names and URLs, native-speaker yield, and the names of review tags.
- [x] Coverage targets per field for Phase 3: confirmed on 2026-10-22.

## Backlog (not now)

None of these get built until you ask for them.

- Remaining D13 extras: gender-suffix rules (-ung → die), plural pattern classes, verb + preposition (warten auf), synonyms, CEFR tags from the Goethe lists (personal use only).
- Drills: production (English → German), listening, der/die/das, plurals.
- FSRS parameter optimization from your own log after about 1,000 reviews.
- Raising n beyond 2,000 via the pipeline's `n_max`.
- Tatoeba sentence audio, licence-filtered.
- Personal notes and mnemonics per word.
- Swipe gestures for the answer buttons.
- Automated Syncthing sync.
- A setting to hide vulgar words.
