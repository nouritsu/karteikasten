# ARASAAC: pictograms

Personal profile only (CC BY-NC-SA 4.0); the public profile drops them.

- API (OpenAPI at `https://api.arasaac.org/arasaac_v1.json`, base `https://api.arasaac.org/v1`):
  - `GET /pictograms/all/{lang}` returns every pictogram with its keywords in one request (de: 13,845 pictograms, 6.4 MB). This is fetched once and snapshotted, which is gentler than about a thousand searches.
  - `GET /pictograms/{lang}/search/{text}` and `/bestsearch/{text}` exist but aren't needed.
  - Images: `https://static.arasaac.org/pictograms/{id}/{id}_500.png`, or `GET /pictograms/{id}?resolution=500|2500`.
  - The spec defines no rate limit; the client allows at most 2 requests per second per host.
- Fields: `_id`, `keywords[]` (`keyword`, `plural`, `type`: 2 = common noun, 3 = verb, …), `synsets`, `categories`, `tags`, and the flags `violence`, `sex`, `schematic`.
- Matching: a noun matches when a common-noun keyword or its plural equals the lemma (ignoring case). In the top 2,000, 476 of 791 nouns (60%) have at least one pictogram, before the concreteness filter and approval.
- Attribution (ARASAAC's required wording): "Pictographic symbols are the property of the Government of Aragón and have been created by Sergio Palao for ARASAAC (https://arasaac.org), that distributes them under Creative Commons License BY-NC-SA."
- Processing: vips thumbnail to 256 px WebP (Q80, metadata stripped), named `<sha1>.webp`.
