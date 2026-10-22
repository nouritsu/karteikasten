"""Phase 1 spike: stages 20-70 over the snapshot, with cached inputs.

Throwaway orchestration that produced reports/phase1-coverage.md and the spike and
fixture decks; Phase 3 turns it into the `build` command. From the dev shell,
inside the checkout:  python -m karteikasten_pipeline.spike [--fresh]
"""

import pickle
import sys
import time
from pathlib import Path

import duckdb

from karteikasten_pipeline import overrides
from karteikasten_pipeline.paths import find_root
from karteikasten_pipeline.readers import frequencywords, leipzig
from karteikasten_pipeline.stages import frequency, lexicon, ud

ROOT = find_root(Path.cwd())
WORK = ROOT / "data" / "work"
CACHE = WORK / "spike-inputs.pickle"


def inputs(fresh: bool):
    if CACHE.exists() and not fresh:
        return pickle.loads(CACHE.read_bytes())
    start = time.time()
    lex = lexicon.load(WORK)
    stats = ud.collect(sorted((ROOT / "data/raw/ud").glob("*/*.conllu")))
    spoken = frequencywords.read(ROOT / "data/raw/frequencywords/de_full.txt")
    con = duckdb.connect()
    written: dict[str, tuple[int, int]] = {}
    for name in ("deu_news_2025_1M", "deu-de_web_2021_1M"):
        for word, total, initial in leipzig.counts(con, WORK / "leipzig" / name).fetchall():
            t, i = written.get(word, (0, 0))
            written[word] = (t + total, i + initial)
    data = (lex, stats, spoken, written)
    CACHE.write_bytes(pickle.dumps(data))
    print(f"inputs built in {time.time() - start:.0f}s", file=sys.stderr)
    return data


def run(fresh: bool = False, epsilon: float = 0.1, spoken_weight: float = 0.7) -> frequency.Result:
    lex, stats, spoken, written = inputs(fresh)
    words = overrides.load_words(ROOT / "overrides/words.toml")
    missing = overrides.unmatched(words, set(lex.lemmas))
    assert not missing, missing
    return frequency.rank(
        spoken, written, lex, stats, spoken_weight=spoken_weight, epsilon=epsilon, exclude=words.exclude
    )


if __name__ == "__main__":
    result = run(fresh="--fresh" in sys.argv)
    WORK.joinpath("frequency.pickle").write_bytes(pickle.dumps(result))
    print(f"ranked {len(result.ranked):,}; unmapped {result.unmapped_share:.3f}; {result.notes}")
    for n in (100, 500, 1000, 2000):
        print(f"  coverage top {n}: {result.ranked[n - 1].coverage_cum:.3f}")
    print("  " + "  ".join(f"{r.rank}.{r.word}({r.pos})" for r in result.ranked[:150]))


def enrich_top(n: int = 2000):
    """Stage 40 over the top n; caches the cards."""
    from collections import defaultdict
    from karteikasten_pipeline.readers import kaikki
    from karteikasten_pipeline.stages import enrich
    lex, *_ = inputs(False)
    result = pickle.loads(WORK.joinpath("frequency.pickle").read_bytes())
    top = result.ranked[:n]
    ids = {r.id for r in top}
    en = lexicon.entries_for(WORK, ids)
    words = {r.word for r in top}
    de: dict[str, list[dict]] = defaultdict(list)
    for entry in kaikki.read(WORK / "kaikki" / "de.jsonl"):
        if entry["word"] in words:
            de[entry["word"]].append(entry)
    cards = [enrich.build_card(r.id, en.get(r.id, []), de.get(r.word, []), lex.separable.get(r.id)) for r in top]
    WORK.joinpath("cards.pickle").write_bytes(pickle.dumps((cards, en, dict(de))))
    return cards


def coverage(n: int = 2000):
    """Per-field coverage, audio and sentences over the top n; returns a summary dict."""
    import json
    from collections import Counter, defaultdict
    from karteikasten_pipeline.readers import tatoeba
    from karteikasten_pipeline.stages import enrich, media, sentences as sent
    lex, *_ = inputs(False)
    result = pickle.loads(WORK.joinpath("frequency.pickle").read_bytes())
    cards, en, de = pickle.loads(WORK.joinpath("cards.pickle").read_bytes())
    top = result.ranked[:n]
    raw = ROOT / "data" / "raw"
    summary: dict = {"n": n}

    # -- card fields -------------------------------------------------------------------------------
    def share(pred, items):
        items = list(items)
        return round(sum(1 for c in items if pred(c)) / max(1, len(items)), 3), len(items)
    fields = {}
    for cut in (100, 500, n):
        cs = cards[:cut]
        nouns = [c for c in cs if c.pos == "noun"]
        verbs = [c for c in cs if c.pos == "verb"]
        fields[cut] = {
            "gloss_en": share(lambda c: c.gloss_en, cs),
            "gloss_de": share(lambda c: c.gloss_de, cs),
            "ipa": share(lambda c: c.ipa, cs),
            "syllables": share(lambda c: c.syllables, cs),
            "stress_highlight": share(lambda c: c.stress_syllable is not None, cs),
            "cognate_en": share(lambda c: c.cognate_en, cs),
            "noun_gender_or_plural_only": share(lambda c: c.article, nouns),
            "noun_plural": share(lambda c: c.key_forms.get("plural") or "plural_only" in c.flags or "singular_only" in c.flags, nouns),
            "noun_genitive": share(lambda c: c.key_forms.get("genitive"), nouns),
            "noun_table": share(lambda c: c.tables.get("declension"), nouns),
            "verb_core_forms": share(lambda c: all(c.key_forms.get(k) for k in ("er", "praeteritum", "partizip2", "auxiliary")), verbs),
            "verb_strength": share(lambda c: {"strong", "weak", "mixed"} & set(c.flags), verbs),
            "adj_comparison": share(lambda c: c.key_forms.get("comparative"), [c for c in cs if c.pos == "adj"]),
            "prep_case": share(lambda c: c.key_forms.get("case"), [c for c in cs if c.pos in ("prep", "postp")]),
            "conj_type": share(lambda c: c.key_forms.get("conjunction"), [c for c in cs if c.pos == "conj"]),
        }
    summary["fields"] = fields
    summary["pos"] = dict(Counter(c.pos for c in cards[:n]).most_common())
    summary["syllable_mismatch"] = [c.lemma for c in cards[:n] if c.issues][:40]
    summary["syllable_mismatch_count"] = sum(1 for c in cards[:n] if c.issues)

    # -- audio (D24) ------------------------------------------------------------------------------
    from karteikasten_pipeline import config
    from karteikasten_pipeline.fetch import commons
    from karteikasten_pipeline.fetch.http import Client
    audio = {r.id: media.audio_candidates(en.get(r.id, []) + de.get(r.word, [])) for r in top}
    files = sorted({c.file for cands in audio.values() for c in cands})
    with Client(config.load(ROOT / "config/pipeline.toml").contact) as client:
        infos = commons.info(files, raw, ROOT / "sources.lock.json", client, log=lambda m: None)
    by_author = media.author_coverage(audio, infos, "personal")
    picks = {id_: media.pick_audio(cands, infos, by_author, "personal") for id_, cands in audio.items()}
    voice = {id_: media.author(infos[p.file]) if p else None for id_, p in picks.items()}
    leader = min(by_author, key=lambda a: (-by_author[a], a))
    summary["audio"] = {
        cut: {
            "any": share(lambda r: audio[r.id], top[:cut]),
            "standard": share(lambda r: any(c.region is None for c in audio[r.id]), top[:cut]),
            "picked": share(lambda r: picks[r.id], top[:cut]),
            "leader": share(lambda r: voice[r.id] == leader, top[:cut]),
            "regional_pick": share(lambda r: picks[r.id] and picks[r.id].region, top[:cut]),
            "anonymous_pick": share(lambda r: picks[r.id] and not voice[r.id], top[:cut]),
        }
        for cut in (100, 500, n)
    }
    summary["authors_by_coverage"] = sorted(by_author.items(), key=lambda kv: (-kv[1], kv[0]))[:8]
    summary["picked_authors"] = Counter(voice.values()).most_common()
    summary["no_usable_audio"] = [r.id for r in top if audio[r.id] and not picks[r.id]]
    WORK.joinpath("commons-info.pickle").write_bytes(pickle.dumps(infos))
    WORK.joinpath("audio-picks.pickle").write_bytes(pickle.dumps((audio, picks, by_author)))

    # -- sentences ------------------------------------------------------------------------------
    forms_of: dict[str, set[str]] = defaultdict(set)
    wanted = {r.id for r in top}
    for form, ids in lex.candidates.items():
        for id_ in ids & wanted:
            forms_of[id_].add(form)
    words = {}
    for r in top:
        particle = lex.separable.get(r.id)
        stems = set()
        if particle:
            for entry in en.get(r.id, []):
                for f in entry.get("forms", []):
                    parts = f.get("form", "").split(" ")
                    if len(parts) == 2 and parts[1] == particle:
                        stems.add(parts[0])
        words[r.id] = sent.WordForms(forms=forms_of[r.id], stems=stems, particle=particle, lemma=r.word)
    t = raw / "tatoeba"
    cc0 = tatoeba.cc0_ids(t / "deu_sentences_CC0.tsv.bz2") | tatoeba.cc0_ids(t / "eng_sentences_CC0.tsv.bz2")
    links = defaultdict(list)
    for d, e in tatoeba.links(t / "deu-eng_links.tsv.bz2"):
        links[d].append(e)
    linked = {e for es in links.values() for e in es}
    english = {s.id: (s.text, s.author, s.licence) for s in tatoeba.sentences(t / "eng_sentences_detailed.tsv.bz2", cc0) if s.id in linked}
    review = {sid for sid, tag in tatoeba.tags(t / "deu_tags.tsv.bz2") if tag in sent.REVIEW_TAGS}
    levels = tatoeba.skill_levels(t / "deu_user_languages.tsv.bz2")
    native = {u for u, lvl in levels.items() if lvl == 5}
    german = [(s.id, s.text, s.author, s.licence) for s in tatoeba.sentences(t / "deu_sentences_detailed.tsv.bz2", cc0)]
    chosen = sent.select(words, german, english, links, review, native)
    WORK.joinpath("sentences.pickle").write_bytes(pickle.dumps(chosen))
    summary["sentences"] = {
        cut: {
            "any": share(lambda r: chosen.get(r.id), top[:cut]),
            "five": share(lambda r: len(chosen.get(r.id, [])) >= 5, top[:cut]),
            "best_is_native": share(lambda r: chosen.get(r.id) and chosen[r.id][0].native, top[:cut]),
            "best_has_english": share(lambda r: chosen.get(r.id) and chosen[r.id][0].en, top[:cut]),
        }
        for cut in (100, 500, n)
    }
    summary["tatoeba"] = {
        "german_sentences": len(german),
        "by_native_authors": sum(1 for _, _, a, _ in german if a in native),
        "review_tagged": len(review),
        "with_english_link": sum(1 for sid, *_ in german if sid in links),
        "native_users": len(native),
    }
    WORK.joinpath("coverage.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str))
    return summary


def build_deck(ids: list[str], name: str):
    """Throwaway deck for the given lemma ids (Phase 1 spike / Phase 2 fixtures)."""
    import json
    from datetime import date
    from karteikasten_pipeline import config, fetch
    from karteikasten_pipeline.fetch.http import Client
    from karteikasten_pipeline.fetch import lock
    from karteikasten_pipeline.stages import bundle, media
    raw, lock_path = ROOT / "data/raw", ROOT / "sources.lock.json"
    result = pickle.loads(WORK.joinpath("frequency.pickle").read_bytes())
    ranked = {r.id: r for r in result.ranked}
    cards = {c.id: c for c in pickle.loads(WORK.joinpath("cards.pickle").read_bytes())[0]}
    audio, picks, by_author = pickle.loads(WORK.joinpath("audio-picks.pickle").read_bytes())
    infos = pickle.loads(WORK.joinpath("commons-info.pickle").read_bytes())
    chosen = pickle.loads(WORK.joinpath("sentences.pickle").read_bytes())
    media_dir = WORK / "media"
    words, credits = [], []
    with Client(config.load(ROOT / "config/pipeline.toml").contact) as client:
        for id_ in ids:
            r, card = ranked[id_], cards[id_]
            record = card.as_dict()
            record.update(rank=r.rank, token_share=r.token_share, coverage_cum=r.coverage_cum)
            record["frequency_flags"] = r.flags
            pick = picks.get(id_)
            record["audio"] = None
            if pick and pick.file in infos:
                meta = infos[pick.file]
                src = fetch.snapshot(client, raw, lock_path, f"commons/audio/{pick.file}", meta["url"], "commons")
                file, duration = media.process_audio(src, media_dir / "audio")
                record["audio"] = {
                    "path": f"media/audio/{file}",
                    "source": "Wikimedia Commons",
                    "source_url": meta.get("descriptionurl"),
                    "author": media.metadata(meta, "Artist"),
                    "license": media.metadata(meta, "LicenseShortName"),
                    "license_url": media.metadata(meta, "LicenseUrl") or None,
                    "duration_ms": duration,
                    "region": pick.region,
                }
                credits.append({"kind": "audio", "word": id_, **record["audio"]})
            record["sentences"] = []
            for c in chosen.get(id_, []):
                sentence = {
                    "id": f"tatoeba:{c.source_ref}", "de": c.de, "en": c.en, "hl": list(c.hl),
                    "source": "Tatoeba", "source_url": f"https://tatoeba.org/de/sentences/show/{c.source_ref}",
                    "author": c.author, "license": c.licence, "native": c.native,
                    "en_author": c.en_author, "en_license": c.en_licence,
                }
                record["sentences"].append(sentence)
                credits.append({"kind": "sentence", "word": id_, **{k: sentence[k] for k in ("id", "source_url", "author", "license", "en_author", "en_license")}})
            words.append(record)
    entries = lock.load(lock_path)
    inputs = {path: entry.sha256 for path, entry in entries.items() if not path.startswith("derewo/")}
    version = bundle.deck_version(date.today(), inputs) + f"-{name}"
    from karteikasten_pipeline.fetch.sources import SOURCES
    sources = [{"id": s.id, "name": s.name, "license": s.licence} for s in SOURCES if s.id != "derewo"]
    dest = bundle.write(
        ROOT / "data/dist/deck" / version,
        manifest={"deck_version": version, "n_max": len(ids), "profile": "personal", "counts": {"words": len(words), "audio": sum(1 for w in words if w["audio"]), "sentences": sum(len(w["sentences"]) for w in words)}, "note": "Phase 1 spike: not a release deck."},
        words=words,
        attribution={"sources": sources, "items": credits},
        media=media_dir,
    )
    return dest
