# Karteikasten — mockups

The screens after D54–D66, drawn at 44 columns, about what a 375 px phone shows (the spec's
older mockups use 34). The app is in English (D66): German is the content, the word, its forms
and its sentences. Brackets are buttons; words set into a block's border are buttons too. The
icons are Material Icons drawn as SVG in the accent (D57); the mockups draw the nearest symbol:
♪ Audio, ▦ Forms, ¶ Sentence, ⚯ Cognate, ✕ close, ⤓ ⤒ export and import, ↺ reset, ⇅ arrange,
˄ ˅ move, ✎ edit, ‖ pause, ✓ done, ⌕ search, ▤ a range of days. Stats draws its meters, squares
and charts in the browser; here they are block characters. The running app is the reference
where they differ.

## Layout

Five pages side by side — **Card │ Stats │ Words │ Options │ Info** — switched by the tabs
along the bottom (the accent line under the current one slides with the page) or by swiping
left and right; the pages slide only when one is turned (D54). The app always opens on Card.

Forms (from its hint), Word (from a word in Words or Trouble words) and Licences (from Info)
open as panes that hang below their page: each rises the height of its content and pushes the
page up and off the top, with **✕ Close** at the right of its top edge, and drops back when
closed, by Close, Escape, a tap on what is left of the page, or a drag down. Stats, Options
and Info are columns of blocks that scroll; a block opened from a button there (Colours, Put
away, Range, Score's editor) unfolds right below the block it belongs to, pushing the rest
down, and folds back up when closed.

## Card

The study screen as before (D17, D29, D34, D36, D38), less the Menü: status, card and score
share the height 20/60/10 above the tabs. The status block is titled **Status** (D55). The
hint buttons stay inside the card, two to a row, with Material icons.

Ready. Every status field is dashed, the answer buttons are disabled, and the whole card face
is the button.

```text
╭─ Status ─────────────── Wednesday 16:04 ─╮
│ Rank #--- · ----- · ---                  │
│ Today -- · Total ---                     │
│ Due -- · New -- · Streak --              │
│ Coverage [------------] --%              │
│ Session --:-- · avg -- points            │
╰──────────────────────────────────────────╯
╭─ Card ───────────────────────────────────╮
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
│                  Ready!                  │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
├──────────────────────────────────────────┤
│ ♪ Audio                          ▦ Forms │
│ ¶ Sentence                     ⚯ Cognate │
╰──────────────────────────────────────────╯
╭─ Score: -- ──────────────────────────────╮
│ [Don't know]                   [Know it] │
╰──────────────────────────────────────────╯
Card │ Stats │ Words │ Options │ Info
‾‾‾‾
```

Running. The word has shuffled in, the clock runs, and Sentence has typed its sentence in below
the word, which stays put.

```text
╭─ Status ─────────────── Wednesday 16:04 ─╮
│ Rank #312 · noun · die                   │
│ Today 12 · Total 412                     │
│ Due 31 · New  6 · Streak  5              │
│ Coverage [#####.......] 41%              │
│ Session 04:12 · avg 72 points            │
╰──────────────────────────────────────────╯
╭─ Card ───────────────────────────────────╮
│                                          │
│                                          │
│                                          │
│                 die Hand                 │
│                  [hant]                  │
│                                          │
│                                          │
│ Gib mir deine Hand.                      │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
├──────────────────────────────────────────┤
│ ♪ Audio                          ▦ Forms │
│ ¶ Sentence                     ⚯ Cognate │
╰──────────────────────────────────────────╯
╭─ Score: 75 ──────────────────────────────╮
│ [Don't know]                   [Know it] │
╰──────────────────────────────────────────╯
Card │ Stats │ Words │ Options │ Info
‾‾‾‾
```

Answered, after Know it: the score is frozen, hints are free, the English meaning follows the
word, the sentence brings its translation, and **I was wrong** undoes.

```text
╭─ Card ───────────────────────────────────╮
│                                          │
│                 die Hand                 │
│                  [hant]                  │
│                                          │
│                   hand                   │
│      pl. die Hände · gen. der Hand       │
│                                          │
│           Gib mir deine Hand.            │
│            Give me your hand.            │
│                                          │
├──────────────────────────────────────────┤
│ ♪ Audio                          ▦ Forms │
│ ¶ Sentence                     ⚯ Cognate │
╰──────────────────────────────────────────╯
╭─ Score: 75 ──────────────────────────────╮
│ [I was wrong]                     [Next] │
╰──────────────────────────────────────────╯
Card │ Stats │ Words │ Options │ Info
‾‾‾‾
```

Forms pane, opened by its hint once the deduction has shown (D32). The card's lower part and the
score stay in view above it; tapping them or dragging the pane down closes it.

```text
  (the page pushed up by the pane)
│           Gib mir deine Hand.            │
│                                          │
├──────────────────────────────────────────┤
│ ♪ Audio                          ▦ Forms │
│ ¶ Sentence                     ⚯ Cognate │
╰──────────────────────────────────────────╯
╭─ Score: 60 ──────────────────────────────╮
│ [Don't know]                   [Know it] │
╰──────────────────────────────────────────╯
╭─ Forms ──────────────────────── ✕ Close ─╮
│             singular     plural          │
│ nom         die Hand     die Hände       │
│ acc         die Hand     die Hände       │
│ dat         der Hand     den Händen      │
│ gen         der Hand     der Hände       │
╰──────────────────────────────────────────╯
```

Done for today, when the queue is empty: the summary scrambles into place under the headline
(D21). The status fields that belong to a word stay dashed; Today, Due and the rest stay live.
When 48 of your last 50 first answers on the words the next level would cover were known, two
more lines suggest that level (D67); nothing changes until you change it in Options.

```text
╭─ Status ─────────────── Wednesday 16:04 ─╮
│ Rank #--- · ----- · ---                  │
│ Today 12 · Total 412                     │
│ Due 31 · New  6 · Streak  5              │
│ Coverage [#####.......] 41%              │
│ Session 04:12 · avg 72 points            │
╰──────────────────────────────────────────╯
╭─ Card ───────────────────────────────────╮
│                                          │
│                                          │
│             Done for today!              │
│                                          │
│        42 reviews · avg score 74         │
│   You already knew 48 of your last 50    │
│   new words. Try A2.1? Options → Study   │
│       6 new words · 12-day streak        │
│           Coverage 41% → 42% ▲           │
│                                          │
│          38 cards due tomorrow.          │
│                                          │
├──────────────────────────────────────────┤
│ ♪ Audio                          ▦ Forms │
│ ¶ Sentence                     ⚯ Cognate │
╰──────────────────────────────────────────╯
╭─ Score: -- ──────────────────────────────╮
│                                          │
╰──────────────────────────────────────────╯
Card │ Stats │ Words │ Options │ Info
‾‾‾‾
```

## Stats

A column of blocks that scrolls (D60). The span sits in Overview's top edge (**30d 90d 1y all**,
and **▤** for any range of days, which unfolds a Range block with a stepper for each end), is
remembered, and sets what History, Score, Recall, Coverage and Rhythm cover. Overview sets each
value against the span before, with a green ▲ or a red ▼ beside the ones that rose or fell, two
values to a line; the span before follows in one muted line that breaks only between its parts.
Records and Trouble words cover all time, Days the last twelve weeks. Values are in the accent.

The charts are SVG on the text's grid, standing on a baseline; tap or drag across one to read a
bar in the line below it. Recall and Coverage draw each share as a meter: a label, the bar and
the number in three columns. Score's answers are one bar across the block, its legend keeping
each square with its name. Days is a grid of squares, deeper in the accent the more reviews a
day had, today outlined. A word in Trouble words opens its Word pane on Words.

```text
╭─ Overview ──────────── 30d 90d 1y all ▤ ─╮
│ 713 reviews ▲      23.8 a day ▲          │
│ 190 new words ▼    avg score 58 ▲        │
│ recall 84% ▼                             │
│                                          │
│ The 30 days before: 497 reviews ·        │
│ avg score 57 · recall 88%                │
╰─ ⇅ Arrange ──────────────────────────────╯
╭─ History ─────────────────── 23.8 a day ─╮
│ 54                                       │
│ ▃▅▂▆▇▃▅█▆▄▂▅▇▆▃▄▆█▅▃▆▇▅▄▆▃▅▇█▅▃▆▇▅▄▆     │
│ ──────────────────────────────────────── │
│ 23 Oct                            21 Nov │
│ ■ reviews   ■ new words                  │
╰──────────────────────────────────────────╯
╭─ Score ───────────────────────── avg 58 ─╮
│ · · · · · · · · · · · · · · · · · · · ·  │
│ ‾‾\__/‾‾‾\_/‾‾‾‾\__/‾‾‾‾\_/‾‾‾\__/‾‾     │
│ · · · · · · · · · · · · · · · · · · · ·  │
│ ──────────────────────────────────────── │
│ Tap or drag to read a value.             │
│ ████████████▕██████████████▕█████▕█████  │
│ ■ easy 31%   ■ good 40%   ■ hard 14%     │
│ ■ didn't know 15%                        │
╰──────────────────────────────────────────╯
╭─ Recall ─────────────────────────── 84% ─╮
│ Knew 256 of 303 · aiming for 90%         │
│ young   ██████████████████████░░░░  86%  │
│ mature  █████████████████████░░░░░  83%  │
│ Young: remembered for under 21 days.     │
╰──────────────────────────────────────────╯
╭─ Coverage ───────────────────────── 56% ─╮
│     1–500  ███████████░░░░░░░░░░░░░  251 │
│  501–1000  ░░░░░░░░░░░░░░░░░░░░░░░░    0 │
│ 1001–1500  ░░░░░░░░░░░░░░░░░░░░░░░░    0 │
│ 1501–2000  ░░░░░░░░░░░░░░░░░░░░░░░░    0 │
│ 251 of 2000 words known ·                │
│ +10% since 23 Oct                        │
╰──────────────────────────────────────────╯
╭─ Days ──────────────────── 7-day streak ─╮
│ Mo  □ □ □ □ □ □ ■ ■ ■ ■ □ ■              │
│     □ □ □ □ □ □ ■ □ ■ ■ ■ ■              │
│ We  □ □ □ □ □ □ ■ ■ ■ ■ ■ ■              │
│     □ □ □ □ □ ■ ■ ■ ■ ■ ■ ■              │
│ Fr  □ □ □ □ □ ■ ■ □ ■ □ □ ■              │
│     □ □ □ □ □ ■ ■ ■ ■ ■ □ ▣              │
│ Su  □ □ □ □ □ ■ ■ ■ □ ■ ■                │
│ ■ 1+  ■ 10+  ■ 25+  ■ 50+  reviews a day │
│ best streak 8 days · 5.6 days a week     │
╰──────────────────────────────────────────╯
╭─ Rhythm ─────────────────────────────────╮
│       █                          ▆       │
│       █                          █       │
│ ──────────────────────────────────────── │
│ 00       06        12        18      24  │
│ Busiest around 07:00.                    │
│ avg 3.7 min a day · 1 sitting            │
╰──────────────────────────────────────────╯
╭─ Records ───────────────────── all time ─╮
│ best streak   12 days   8 Oct–19 Oct     │
│ busiest day   54        12 Oct           │
│ best score    70        24 Oct           │
│ in all        1210 reviews on 38 days    │
╰──────────────────────────────────────────╯
╭─ Trouble words ────────────────────── 3 ─╮
│ #418 die Ursache            forgotten 5× │
│ #602 erwähnen               forgotten 4× │
│ #977 bisherig               forgotten 4× │
╰──────────────────────────────────────────╯
Card │ Stats │ Words │ Options │ Info
       ‾‾‾‾‾
```

**⇅ Arrange** in Overview's bottom edge sets **˄ ˅ ✕** into the top edge of every block below
it: up, down, and put away. A Put away block unfolds below Overview with a **+** word for each
block put away; **✓ Done**, or leaving the page, folds it and ends arranging; **↺ Defaults**
beside it puts every block back in the first order.

```text
╭─ Overview ──────────── 30d 90d 1y all ▤ ─╮
│ 713 reviews ▲      23.8 a day ▲          │
│ …                                        │
╰─ ⇅ Arrange ──────────────────────────────╯
╭─ Put away ───────────────────────────────╮
│ [ + Rhythm ]  [ + Trouble words ]        │
╰─ ↺ Defaults ──────────────────── ✓ Done ─╯
╭─ History ──────────────────────── ˄ ˅ ✕ ─╮
│ …                                        │
╰──────────────────────────────────────────╯
```

## Words

One block fills the page: the search field (umlaut-tolerant, ae finds ä, ss finds ß; lemmas
first, then English meanings) and three filters that step through their values on a tap, then
the list, which scrolls inside the block. Each row shows the rank, the word in its gender
colour, its type and its status, type and status set apart. Tapping a row opens its Word pane.

```text
╭─ Words ─────────────────────────── 2000 ─╮
│ ⌕ [German word or English meaning      ] │
│ Status [all]  Type [all]  Gender [all]   │
├──────────────────────────────────────────┤
│  #312 die Hand         noun  known       │
│ #1408 handeln          verb  new         │
│ #1733 der Handel       noun  learning    │
│ #1862 die Handlung     noun  new         │
│ #1990 der Handschuh    noun  paused      │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
╰──────────────────────────────────────────╯
Card │ Stats │ Words │ Options │ Info
               ‾‾‾‾‾
```

Word pane: everything the deck has on the word, without a score, and the actions (D53, D56).
**✓ Already know it** (on a word not studied yet) and **‖ Pause** act at once; Already know it
then offers **↺ Undo** until the pane closes, and Pause becomes **▷ Resume**. **↺ Reset** asks
**Reset?** on the first press, in red, and acts on the second.

```text
╭─ Word ───────────────────────── ✕ Close ─╮
│ die Hand · #312 · noun                   │
│ [hant] · ≈ hand                          │
│ 1. hand                                  │
│ 2. side, direction                       │
│ pl. die Hände · gen. der Hand            │
├──────────────────────────────────────────┤
│ due Sat 23 Nov · 8 reviews · avg score   │
│ 74                                       │
│ remembered for ~34 days · forgotten 0×   │
├──────────────────────────────────────────┤
│ [ ‖ Pause ]  [ ↺ Reset ]                 │
╰──────────────────────────────────────────╯
```

## Options

A column of blocks that scrolls, one a category (D54, D56, D58, D59, D62, D63). A setting that is
off reads muted. A block's steppers share one label width, so their values line up.

**Theme**: Flavour steps through Mocha, Latte and System, which shows Mocha while the phone is
dark and Latte while it is light, and follows it; the circle reveal (D37) grows from the button.
Colours shows the accent and the four gender colours as squares; tapping them unfolds the Colours
block right below Theme, with a stepper for each through Catppuccin's fourteen accents. A change
applies at once; **↺ Defaults** brings back mauve, blue, red, green and pink.

**Display**: Text size (System, Small, Normal, Large), Motion and Haptics (System, On, Off), and
Clock (System, 24h, 12h) for the time in Status's edge. System follows the phone.

```text
╭─ Theme ──────────────────────────────────╮
│ Flavour                       [ System ] │
│ Colours                        [ ■■■■■ ] │
╰──────────────────────────────────────────╯
╭─ Colours ────────────────────── ✕ Close ─╮
│ Accent  ████ Mauve                  <  > │
│ der     ████ Blue                   <  > │
│ die     ████ Red                    <  > │
│ das     ████ Green                  <  > │
│ plural  ████ Pink                   <  > │
╰───────────────────────────── ↺ Defaults ─╯
╭─ Display ────────────────────────────────╮
│ Text size                     [ System ] │
│ Motion                        [ System ] │
│ Haptics                       [ System ] │
│ Clock                         [ System ] │
│ System follows the phone: its font size, │
│ Remove animations, and touch feedback.   │
╰──────────────────────────────────────────╯
Card │ Stats │ Words │ Options │ Info
                       ‾‾‾‾‾‾‾
```

**Study**: **Level** (D67) steps through Beginner, A1.1, A1.2, A2.1, A2.2, B1.1 and B1.2, at
ranks 0, 100, 250, 500, 800, 1,200 and 1,600. Words up to the level's rank come as quick checks,
**Checks a day** of them, and new words start after it; at Beginner the Checks row hides. The
steppers repeat while held and follow a drag across them. **Score** sums up the
score's numbers (D17, D39), a hint's name and cost kept together; **✎ Edit** turns each into a
stepper.

```text
╭─ Study ──────────────────────────────────╮
│ Level          A1.2 · top 250       <  > │
│ Checks a day   20                   <  > │
│ New words a day 15                  <  > │
│ Vocabulary     top 2000             <  > │
│ Retention      90%                  <  > │
│ Learn ahead    20 min               <  > │
│ Audio after answering             [ on ] │
│ Words up to #250 come as quick checks,   │
│ 20 a day. Know one and it comes back in  │
│ a week, then months; miss one and you    │
│ learn it. New words start at #251.       │
│ With nothing else due, a card still      │
│ being learnt comes up this early.        │
╰──────────────────────────────────────────╯
╭─ Score ──────────────────────────────────╮
│ starts at 100 · 2s grace · −5 every 1.5s │
│ Audio −10 · Forms −15 · Sentence −20 ·   │
│ Cognate −30                              │
│ easy from 85 · good from 40              │
╰───────────────────────────────── ✎ Edit ─╯
```

**Reminder** (D63): a notification at the time set, on days when cards are due and you have not
studied yet. It also arrives with the app closed: whenever the app goes to the background it
plans the next week's reminders with the counts they will have.

**Backup** (D62): export and import (D52). **Keep one file** writes `karteikasten.json`, replaced
on each export, instead of a file a day, which suits a Syncthing folder. Regular exports take a
calendar event in systemd's OnCalendar notation, said back in plain words with the next run;
tapping an example fills the field. They run with the app closed.

**Privacy** (D62): Android's cloud backup of the app's data, off by default.

```text
╭─ Reminder ───────────────────────────────╮
│ Reminder                          [ on ] │
│ At      19:00                       <  > │
│ Only on days with cards due, and only if │
│ you haven't studied yet.                 │
╰──────────────────────────────────────────╯
╭─ Backup ─────────────────────────────────╮
│ Last export 20 Nov 2026, 21:04.          │
│ [ ⤓ Export ]   [ ⤒ Import ]              │
│ Import adds what is missing and changes  │
│ nothing.                                 │
├──────────────────────────────────────────┤
│ Keep one file                     [ on ] │
│ One file, replaced each time:            │
│ Documents/Karteikasten/karteikasten.json │
│ Export on a schedule              [ on ] │
│ When [*-*-* 22:00                     ]  │
│ Every day at 22:00. Next today 22:00.    │
│ daily  weekly  Sun 21:00                 │
│ Last scheduled export today 06:00, to    │
│ Documents/Karteikasten/karteikasten.json │
╰──────────────────────────────────────────╯
╭─ Privacy ────────────────────────────────╮
│ Cloud backup                     [ off ] │
│ Off keeps your progress out of your      │
│ Google account's backup. Moving to a new │
│ phone by direct transfer works either    │
│ way, on Android 9 and newer.             │
╰──────────────────────────────────────────╯
```

## Info

A column of blocks (D61). **Adjective endings** steps with `<` `>` through the weak, mixed and
strong declensions. **Sources** lists every source, its licence on the line below; typing a word
lists that word's own credits (audio author and licence, each sentence's author and translator)
from `attribution.json`, breaking only between their parts. **About** sits at the bottom with the
app and deck versions and the credits; **third-party notices** opens the Licences pane, which
shows the bundled THIRD_PARTY_NOTICES.md as plain text, scrolling.

```text
╭─ Adjective endings ──────────────────────╮
│ <      weak · after der, die, das      > │
│         m       f       n       pl       │
│ nom     -e      -e      -e      -en      │
│ acc     -en     -e      -e      -en      │
│ dat     -en     -en     -en     -en      │
│ gen     -en     -en     -en     -en      │
╰──────────────────────────────────────────╯
╭─ Sources ────────────────────────────────╮
│ ⌕ [Hand                                ] │
│ die Hand #239                            │
│ Audio · Jeuwre · CC BY-SA 4.0            │
│ Sentence · Espi · CC BY 2.0 FR ·         │
│ translated by stoopeedhooman             │
├──────────────────────────────────────────┤
│ FrequencyWords, OpenSubtitles 2018 (de)  │
│ CC BY-SA 4.0                             │
│                                          │
│ Tatoeba German sentences with English    │
│ translations                             │
│ CC BY 2.0 FR (some CC0)                  │
│ …                                        │
╰──────────────────────────────────────────╯
╭─ About ──────────────────────────────────╮
│ Karteikasten 0.1.0 · deck 2026.10.22-6cf │
│ font Iosevka (SIL OFL 1.1)               │
│ colours Catppuccin (MIT)                 │
│ icons Material Icons (Apache 2.0)        │
│ licences third-party notices             │
╰──────────────────────────────────────────╯
Card │ Stats │ Words │ Options │ Info
                                 ‾‾‾‾
```

## Reminder (Android)

A plain notification in the system's own colours, with the status-bar icon from
`app/notification.svg`; tapping it opens the app, and opening the app clears it.

```text
Karteikasten · 19:00
31 cards due · 15 new words · 12-day streak
You haven't studied today.
```

## Launcher icon

fast-track's icon with Material Icons' translate glyph (文A) where its fork and spoon were
(D65): `app/icon.svg`, `app/icon-monochrome.svg` for Android's themed icons, and
`app/notification.svg` for the status bar.
