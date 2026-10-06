# OpenMoji and Unicode CLDR (German annotations)

Emoji art, and German names to match nouns. Ships: yes.

- OpenMoji 17.0.0 (CC BY-SA 4.0): `data/openmoji.json` (4,495 entries: `emoji`, `hexcode`, `annotation` in English, `openmoji_author`, `skintone`) and `openmoji-svg-color.zip` (flat `<HEXCODE>.svg`). Skin-tone variants are left out.
- CLDR `release-48-2` (Unicode License v3): `common/annotations/de.xml` and `common/annotationsDerived/de.xml`. `<annotation cp="✋">keyword | keyword</annotation>` gives keywords; `type="tts"` gives the name (*erhobene Hand*).
- Matching: a noun matches an emoji whose German name or keyword equals it. In the top 2,000, 309 of 791 nouns (39%) match. Candidates are ordered with the exact name first (👨 *Mann*, 🚗 *Auto*), then names containing the noun as a word (shortest first), then keyword-only matches (*Hand* is a keyword of many hand emoji). Approval in `overrides/images.toml` still decides.
