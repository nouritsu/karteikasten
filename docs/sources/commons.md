# Wikimedia Commons: audio

Recordings and their per-file credits. Ships: yes, each file with its author and licence exactly as the API returns them.

- Candidates are the files both Wiktionary editions link (`sounds[].audio`), named like `De-Hand.ogg` (`De-at-` means Austria) or `LL-Q188 (deu)-<speaker>-<word>.wav` (Lingua Libre).
- Metadata: `https://commons.wikimedia.org/w/api.php`, `prop=imageinfo`, `iiprop=url|size|mime|sha1|extmetadata`, filtered to `Artist|LicenseShortName|LicenseUrl|Credit|AttributionRequired|UsageTerms`, with `redirects=1` and `maxlag=5`. Batches of 50 titles, at most 2 requests per second, User-Agent with contact. Each batch response is snapshotted under `data/raw/commons/info/` and locked. Audio originals go to `data/raw/commons/audio/`, also locked; only the deck's files are fetched, never the 20 GB bulk archive.
- Top 2,000 (Phase 1):
  - 99.9% of words have at least one standard-German file. No word has only regional files.
  - Lingua Libre covers 3.8%. The top speaker, Sebastian Wallroth, has 67 words.
  - **One Commons author, Jeuwre, has a standard-German recording for 1,975 of the 2,000 words (98.75%).**
  - Licences over all 3,770 candidates: CC BY-SA 4.0/3.0/2.5, CC BY 2.0 FR/3.0, CC0, public domain, GFDL. **None is NC or ND**, so the public profile keeps all audio.
- Pick rule (D24, `stages/media.py`):
  - Authors are ranked by how many deck words they have a usable standard-German file for. Each word takes the file of the highest-ranked author who has one, so words the top author lacks fall through to the next author by coverage. Regional files come after every standard one, and own recordings always win.
  - The author key is the first linked name in the Artist field (Lingua Libre lists the speaker first), else the field's text. It is case-folded and loses any `User:` prefix, because the same person appears as *Jeuwre* and *jeuwre*, or *Tosca* and *User:Tosca*. Artist values that name nobody (*Own work*, *myself*) rank after every named author. Credits still use the whole Artist field.
  - A file is usable only when Commons gives its author and licence. The public profile also skips NC/ND files.
  - Result for the top 2,000: Jeuwre voices 1,975 words. 22 fall through to 7 other authors (Katrin Boxberger/Bernadette Perrin-Riou 6, Dinock90 5, T.Voekler 5, MiER 2, Kampy 2, Cyrotux 1, Bleibein 1). 3 have no recording at all (*Dr.*, *b.*, *rauskommen*).
- Processing (ffmpeg, bit-exact): trim silence to 100 ms at each end, loudnorm to −16 LUFS, mono 24 kHz MP3 at 48 kbps, named `<sha1>.mp3`.
