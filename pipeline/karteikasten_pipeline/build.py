"""`build`: stages 20-70 over the snapshot in data/raw (spec: Pipeline stages).

Each stage's result is cached in data/work/cache under a hash of its inputs and
code (D48), so a second build only recomputes what changed. The network is used
only for Commons metadata and audio files that the snapshot lacks; both land in
data/raw and sources.lock.json like any other snapshot, and `--offline` refuses
instead. The deck goes to data/dist/deck/<version>/, latest.json names it, and
data/work/curation.sqlite holds the candidates and issues for the curation tool.
"""

import contextlib
import json
from collections import defaultdict
from collections.abc import Callable, Iterator
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import quote

from karteikasten_pipeline import cache as caching
from karteikasten_pipeline import config, coverage, curation, fetch, overrides
from karteikasten_pipeline.fetch import commons, lock
from karteikasten_pipeline.fetch.http import Client, sha256_of
from karteikasten_pipeline.fetch.sources import SOURCES
from karteikasten_pipeline.paths import Paths
from karteikasten_pipeline.readers import conllu, frequencywords, kaikki, leipzig, tatoeba
from karteikasten_pipeline.stages import bundle, enrich, frequency, lexicon, media, sentences, ud

EN_DUMP = "kaikki-en/raw-wiktextract-data.jsonl.gz"
DE_DUMP = "kaikki-de/de-extract.jsonl.gz"
LEIPZIG_CORPORA = ("deu_news_2025_1M", "deu-de_web_2021_1M")
TATOEBA_FILES = (
    "deu_sentences_detailed.tsv.bz2",
    "deu_sentences_CC0.tsv.bz2",
    "eng_sentences_detailed.tsv.bz2",
    "eng_sentences_CC0.tsv.bz2",
    "deu-eng_links.tsv.bz2",
    "deu_tags.tsv.bz2",
    "deu_user_languages.tsv.bz2",
)
PRIVATE = ("derewo/",)  # never part of a deck's inputs (spec: DeReWo stays a private cross-check)
COMMONS = {"id": "commons", "name": "Wikimedia Commons (audio)", "url": "https://commons.wikimedia.org",
           "license": "per file (see items)"}
OWN = {"id": "own", "name": "Own recordings", "url": None, "license": "per file (see items)"}


class BuildError(Exception):
    pass


def _extract(paths: Paths, entries: dict[str, lock.Entry], raw: str, name: str, log: Callable[[str], None]) -> None:
    """data/work/kaikki/<name>: the German entries of a Kaikki dump, extracted again
    whenever the dump's hash in the lock differs from the one recorded beside it."""
    if raw not in entries:
        raise BuildError(f"{raw} is not in sources.lock.json; run `nix run .#fetch` first")
    dest = paths.work / "kaikki" / name
    stamp = dest.with_name(name + ".sha256")
    if dest.exists() and stamp.exists() and stamp.read_text().strip() == entries[raw].sha256:
        return
    log(f"stage 20: extracting the German entries of {raw}")
    count = kaikki.extract_german(paths.raw / raw, dest)
    stamp.write_text(entries[raw].sha256 + "\n")
    log(f"stage 20: {count:,} entries in {dest.relative_to(paths.root)}")


def _written(paths: Paths) -> dict[str, tuple[int, int]]:
    import duckdb

    con = duckdb.connect()
    written: dict[str, tuple[int, int]] = {}
    for name in LEIPZIG_CORPORA:
        corpus = leipzig.unpack(paths.raw / "leipzig" / f"{name}.tar.gz", paths.work / "leipzig")
        for word, total, initial in leipzig.counts(con, corpus).fetchall():
            t, i = written.get(word, (0, 0))
            written[word] = (t + total, i + initial)
    return written


def _tatoeba(paths: Paths, words: dict[str, sentences.WordForms], pins, bans):
    t = paths.raw / "tatoeba"
    cc0 = tatoeba.cc0_ids(t / "deu_sentences_CC0.tsv.bz2") | tatoeba.cc0_ids(t / "eng_sentences_CC0.tsv.bz2")
    links: dict[int, list[int]] = defaultdict(list)
    for d, e in tatoeba.links(t / "deu-eng_links.tsv.bz2"):
        links[d].append(e)
    linked = {e for es in links.values() for e in es}
    english = {
        s.id: (s.text, s.author, s.licence)
        for s in tatoeba.sentences(t / "eng_sentences_detailed.tsv.bz2", cc0)
        if s.id in linked
    }
    review = {sid for sid, tag in tatoeba.tags(t / "deu_tags.tsv.bz2") if tag in sentences.REVIEW_TAGS}
    native = {u for u, level in tatoeba.skill_levels(t / "deu_user_languages.tsv.bz2").items() if level == 5}
    german = ((s.id, s.text, s.author, s.licence) for s in tatoeba.sentences(t / "deu_sentences_detailed.tsv.bz2", cc0))
    return sentences.select(words, german, english, links, review, native, pins=pins, bans=bans)


def _source_rows(entries: dict[str, lock.Entry], recordings: bool) -> list[dict[str, Any]]:
    """One row per source: its latest retrieval and a hash over its files' hashes."""
    rows = []
    for source in SOURCES:
        if source.id == "derewo":
            continue
        files = {p: e for p, e in entries.items() if e.source == source.id}
        rows.append({
            "id": source.id, "name": source.name, "url": source.files[0].url, "license": source.licence,
            "retrieved_at": max((e.retrieved_at for e in files.values()), default=None),
            "sha256": caching.digest({p: e.sha256 for p, e in sorted(files.items())}) if files else None,
        })
    files = {p: e for p, e in entries.items() if e.source == "commons"}
    rows.append({**COMMONS, "retrieved_at": max((e.retrieved_at for e in files.values()), default=None),
                 "sha256": caching.digest({p: e.sha256 for p, e in sorted(files.items())})})
    if recordings:
        rows.append({**OWN, "retrieved_at": None, "sha256": None})
    return rows


def _write_closed_class_evidence(paths, top, cards, en_for, de_for, lex) -> None:
    """data/work/closed-classes.json: what both editions say about each preposition and
    conjunction in the deck, for drafting overrides/closed_classes.toml (draft.py)."""
    evidence = {}
    for r in top:
        de = enrich.german_entries_for(cards[r.id], de_for[r.id])
        if r.pos in ("prep", "postp"):
            ev = enrich.case_evidence(en_for[r.id], de)
            evidence[r.id] = {"kind": "preposition", "rank": r.rank, "cases": ev.cases(), "en": ev.en,
                              "de_main": ev.de_main, "de_secondary": ev.de_secondary, "notes": ev.notes,
                              "agree": ev.agree(), "contractions": lex.contractions.get(r.id, [])}
        elif r.pos == "conj":
            ev = enrich.conjunction_evidence(en_for[r.id], de)
            evidence[r.id] = {"kind": "conjunction", "rank": r.rank, "type": ev.kind(), "en": ev.en, "de": ev.de,
                              "agree": ev.agree()}
    text = json.dumps(evidence, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    (paths.work / "closed-classes.json").write_text(text, encoding="utf-8")


def _round(x: float) -> float:
    return float(f"{x:.10g}")


def run(
    paths: Paths,
    *,
    profile: str | None = None,
    fresh: bool = False,
    offline: bool = False,
    log: Callable[[str], None] = print,
) -> Path:
    settings = config.load(paths.config)
    profile = profile or settings.profile
    if profile not in ("personal", "public"):
        raise BuildError(f"unknown profile {profile!r}")
    entries = lock.load(paths.lock)
    try:
        over = overrides.load(paths.overrides)
    except overrides.OverrideError as error:
        raise BuildError(str(error)) from error
    store = caching.Cache(paths.work / "cache", fresh=fresh, log=log)
    # Hashed before any stage runs, so an edit during a long build cannot relabel its deck.
    code_digest = caching.code(*_pipeline_modules())

    def raw(*prefixes: str) -> dict[str, str]:
        return {p: e.sha256 for p, e in sorted(entries.items()) if p.startswith(prefixes)}

    # -- stage 20: lexicon -------------------------------------------------------------------
    _extract(paths, entries, EN_DUMP, "en.jsonl", log)
    _extract(paths, entries, DE_DUMP, "de.jsonl", log)
    lexicon_key = caching.digest(raw("kaikki-en/", "kaikki-de/"), caching.code(lexicon, kaikki))
    lex, en_index, de_index = store.get("lexicon", lexicon_key, lambda: lexicon.load(paths.work))
    if stale := overrides.unmatched(over, set(lex.lemmas)):
        raise BuildError("overrides name ids the lexicon does not have: " + ", ".join(stale))

    # -- stage 30: frequency and lemmas -----------------------------------------------------
    ud_key = caching.digest(raw("ud/"), caching.code(ud, conllu))
    ud_stats = store.get("ud", ud_key, lambda: ud.collect(sorted(paths.raw.glob("ud/*/*.conllu"))))
    spoken_key = caching.digest(raw("frequencywords/"), caching.code(frequencywords))
    spoken = store.get("spoken", spoken_key, lambda: frequencywords.read(paths.raw / "frequencywords" / "de_full.txt"))
    written_key = caching.digest(raw("leipzig/"), caching.code(leipzig))
    written = store.get("written", written_key, lambda: _written(paths))
    words_over = over.words
    ranking_key = caching.digest(
        lexicon_key, ud_key, spoken_key, written_key, caching.code(frequency),
        settings.spoken_weight, settings.epsilon, words_over.exclude, words_over.merge,
    )
    ranking = store.get("ranking", ranking_key, lambda: frequency.rank(
        spoken, written, lex, ud_stats, spoken_weight=settings.spoken_weight, epsilon=settings.epsilon,
        exclude=words_over.exclude, merge=words_over.merge,
    ))
    top = ranking.ranked[: settings.n_max]
    deck_ids = {r.id for r in top}
    absorbed_by: dict[str, list[str]] = defaultdict(list)
    for absorbed, target in sorted(words_over.merge.items()):
        absorbed_by[target].append(absorbed)
    survivor = {a: t for t, absorbed in absorbed_by.items() for a in absorbed}
    log(f"stage 30: {len(ranking.ranked):,} lemmas ranked; the top {len(top):,} cover "
        f"{top[-1].coverage_cum:.1%} of running text")

    # -- stage 40: card content -------------------------------------------------------------
    group = {r.id: [r.id, *absorbed_by.get(r.id, [])] for r in top}
    needed = {id_ for ids in group.values() for id_ in ids}
    en_found = en_index.get(needed)
    de_found = de_index.get({lex.lemmas[id_].word for id_ in needed})
    en_for = {r.id: [e for id_ in group[r.id] for e in en_found.get(id_, [])] for r in top}
    de_for = {}
    for r in top:
        words_of = list(dict.fromkeys(lex.lemmas[id_].word for id_ in group[r.id]))
        de_for[r.id] = [e for w in words_of for e in de_found.get(w, [])]
    cards: dict[str, enrich.Card] = {}
    for r in top:
        card = enrich.build_card(
            r.id, en_for[r.id], de_for[r.id], lex.separable.get(r.id),
            contractions=lex.contractions.get(r.id, []), ordinals=lex.ordinals,
        )
        enrich.apply_closed_classes(card, over.closed)
        for field, manual in (("gloss_en", words_over.gloss_en), ("gloss_de", words_over.gloss_de)):
            if r.id in manual:
                setattr(card, field, [enrich.Gloss(text) for text in manual[r.id]])
                card.sources[field] = "manual (words.toml)"
        if r.id in words_over.no_cognate:
            if not card.cognate_en:
                raise BuildError(f"words.toml [no_cognate] {r.id}: the card has no cognate hint to drop")
            card.cognate_en = None
            card.sources["cognate_en"] = f"dropped by hand: {words_over.no_cognate[r.id]}"
        cards[r.id] = card
    log(f"stage 40: {len(cards):,} cards")
    _write_closed_class_evidence(paths, top, cards, en_for, de_for, lex)

    # -- stage 50: audio --------------------------------------------------------------------
    candidates = {r.id: media.audio_candidates(en_for[r.id] + de_for[r.id]) for r in top}
    titles = sorted({c.file for cands in candidates.values() for c in cands})
    audio_store = media.AudioStore(paths.work / "media", fresh=fresh)
    recordings = {id_: path for id_, path in over.recordings.items() if id_ in deck_ids}
    if recordings and not (settings.recording_author and settings.recording_license):
        raise BuildError("overrides/audio has recordings, but [recordings] author and license in "
                         "config/pipeline.toml are empty")
    client_context = contextlib.nullcontext(None) if offline else Client(settings.contact)
    audio: dict[str, dict[str, Any] | None] = {}
    with client_context as client:
        try:
            infos = commons.info(titles, paths.raw, paths.lock, client, log=log)
        except commons.Offline as error:
            raise BuildError(f"--offline: {error}") from error
        by_author = media.author_coverage(candidates, infos, profile)
        picks = {id_: media.pick_audio(cands, infos, by_author, profile) for id_, cands in candidates.items()}
        for id_, file in sorted(words_over.audio.items()):
            if id_ not in candidates:
                raise BuildError(f"words.toml [audio] names a word outside the deck: {id_}")
            pinned = next((c for c in candidates[id_] if c.file == file), None)
            if pinned is None:
                raise BuildError(f"words.toml [audio] {id_}: {file} is not one of its recordings")
            if not media.usable(infos.get(file), profile):
                raise BuildError(f"words.toml [audio] {id_}: {file} has no author or licence on Commons"
                                 + (", or is NC/ND" if profile == "public" else ""))
            picks[id_] = pinned
        for done, r in enumerate(top, start=1):
            if r.id in recordings:
                source = recordings[r.id]
                name, duration = audio_store.get(source, sha256_of(source))
                audio[r.id] = {
                    "path": f"media/audio/{name}", "source": "Own recording", "source_url": None,
                    "author": settings.recording_author, "license": settings.recording_license,
                    "license_url": None, "duration_ms": duration, "region": None,
                }
            elif (pick := picks[r.id]) is not None:
                meta = infos[pick.file]
                relative = f"commons/audio/{pick.file}"
                if offline and not ((paths.raw / relative).exists() and relative in lock.load(paths.lock)):
                    raise BuildError(f"--offline: {relative} is not in the snapshot")
                source = fetch.snapshot(client, paths.raw, paths.lock, relative, meta["url"], "commons")
                name, duration = audio_store.get(source, sha256_of(source))
                audio[r.id] = {
                    "path": f"media/audio/{name}", "source": "Wikimedia Commons",
                    "source_url": meta.get("descriptionurl"), "author": media.metadata(meta, "Artist"),
                    "license": media.metadata(meta, "LicenseShortName"),
                    "license_url": media.metadata(meta, "LicenseUrl") or None,
                    "duration_ms": duration, "region": pick.region,
                }
            else:
                audio[r.id] = None
            if done % 250 == 0:
                audio_store.save()
                log(f"stage 50: audio for {done:,} of {len(top):,} words")
    audio_store.save()
    for item in audio.values():
        if item:
            item["sha256"] = sha256_of(paths.work / "media" / "audio" / Path(item["path"]).name)
            item["id"] = "audio:" + Path(item["path"]).stem
    log(f"stage 50: audio for {sum(1 for a in audio.values() if a):,} words")

    # -- stage 60: sentences ----------------------------------------------------------------
    forms_of: dict[str, set[str]] = defaultdict(set)
    for form, ids in lex.candidates.items():
        for id_ in ids & needed:
            forms_of[survivor.get(id_, id_)].add(form)
    word_forms: dict[str, sentences.WordForms] = {}
    for r in top:
        particle = lex.separable.get(r.id)
        stems = set()
        if particle:
            for entry in en_for[r.id]:
                for f in entry.get("forms", []):
                    parts = f.get("form", "").split(" ")
                    if len(parts) == 2 and parts[1] == particle:
                        stems.add(parts[0])
        word_forms[r.id] = sentences.WordForms(forms=forms_of[r.id], stems=stems, particle=particle, lemma=r.word)
    pins = {id_: s for id_, s in over.sentences.pin.items() if id_ in deck_ids}
    bans = {id_: s for id_, s in over.sentences.ban.items() if id_ in deck_ids}
    for table, chosen_ids in (("pin", over.sentences.pin), ("ban", over.sentences.ban)):
        if outside := sorted(set(chosen_ids) - deck_ids):
            raise BuildError(f"sentences.toml [{table}] names words outside the deck: {', '.join(outside)}")
    forms_digest = caching.digest({id_: [sorted(w.forms), sorted(w.stems), w.particle, w.lemma]
                                   for id_, w in sorted(word_forms.items())})
    sentences_key = caching.digest(raw("tatoeba/"), forms_digest, pins, bans,
                                   caching.code(sentences, tatoeba))
    tatoeba_best, tatoeba_pinned, used_bans = store.get(
        "sentences", sentences_key, lambda: _tatoeba(paths, word_forms, pins, bans)
    )
    survivor_of = {**{id_: id_ for id_ in deck_ids}, **{a: t for a, t in survivor.items() if t in deck_ids}}
    chosen: dict[str, list[sentences.Candidate]] = {}
    for r in top:
        examples = sentences.wiktionary_examples(word_forms[r.id], en_for[r.id])
        available = {c.id: c for c in examples} | tatoeba_pinned.get(r.id, {})
        pinned = []
        for sentence_id in pins.get(r.id, []):
            if sentence_id not in available:
                raise BuildError(f"sentences.toml [pin] {r.id}: {sentence_id} is not a sentence for this word")
            pinned.append(available[sentence_id])
        banned = set(bans.get(r.id, []))
        example_ids = {c.id for c in examples}
        for sentence_id in banned:
            if (r.id, sentence_id) not in used_bans and sentence_id not in example_ids:
                raise BuildError(f"sentences.toml [ban] {r.id}: {sentence_id} is not a sentence for this word")
        chosen[r.id] = sentences.final(tatoeba_best.get(r.id, []), examples, pinned, banned)

    def deck_tokens(text: str) -> tuple[list[str], int]:
        """Deck word ids in a sentence, and how many of its tokens are no deck word."""
        found: set[str] = set()
        outside = 0
        for i, (token, _, _) in enumerate(sentences.tokens(text)):
            variants = {token, token.lower()} if i == 0 else {token}
            ids = {survivor_of[id_] for v in variants for id_ in lex.candidates.get(v, ()) if id_ in survivor_of}
            found |= ids
            outside += not ids
        return sorted(found), outside

    def sentence_record(word: str, c: sentences.Candidate) -> dict[str, Any]:
        ids, outside = deck_tokens(c.de)
        url = (f"https://tatoeba.org/de/sentences/show/{c.source_ref}" if c.source == "tatoeba"
               else f"https://en.wiktionary.org/wiki/{quote(word)}#German")
        return {
            "id": c.id, "de": c.de, "en": c.en, "hl": list(c.hl), "source": c.source.capitalize(),
            "source_ref": c.source_ref, "source_url": url, "author": c.author, "license": c.licence,
            "native": c.native, "en_author": c.en_author, "en_license": c.en_licence,
            "score": round(c.score, 4), "deck_token_ids": ids, "out_of_deck": outside,
        }

    log(f"stage 60: sentences for {sum(1 for c in chosen.values() if c):,} words")

    # -- stage 70: bundle ---------------------------------------------------------------------
    words: list[dict[str, Any]] = []
    notes: dict[str, list[str]] = {}
    for r in top:
        record = cards[r.id].as_dict()
        notes[r.id] = record.pop("issues")
        record.pop("cognates_raw")
        record["provenance"] = record.pop("sources")
        record.update(
            rank=r.rank, token_share=_round(r.token_share), coverage_cum=_round(r.coverage_cum),
            frequency_flags=r.flags, audio=audio[r.id],
            sentences=[sentence_record(r.word, c) for c in chosen[r.id]],
        )
        words.append(record)

    entries = lock.load(paths.lock)  # stage 50 may have added Commons snapshots
    # Recordings the deck does not use (fetched to listen to in the curation tool) are
    # not inputs: hearing a candidate must not change the deck version.
    picked = {f"commons/audio/{p.file}" for id_, p in picks.items() if p is not None and id_ not in recordings}
    used = {p: e for p, e in sorted(entries.items())
            if not p.startswith(PRIVATE) and (not p.startswith("commons/audio/") or p in picked)}
    inputs = {
        "raw": caching.digest({p: e.sha256 for p, e in used.items()}),
        "overrides": caching.files(p for p in paths.overrides.rglob("*") if p.is_file()),
        "config": caching.digest(settings.n_max, profile, settings.spoken_weight, settings.epsilon,
                                 settings.recording_author, settings.recording_license),
        "code": code_digest,
        "ffmpeg": audio_store.version,
    }
    snapshot = max(e.retrieved_at for e in used.values())[:10]
    version = bundle.deck_version(date.fromisoformat(snapshot), inputs)

    media_rows = [
        {"id": a["id"], "kind": "audio", "path": a["path"], "source": a["source"], "source_url": a["source_url"],
         "author": a["author"], "license": a["license"], "license_url": a["license_url"], "sha256": a["sha256"],
         "duration_ms": a["duration_ms"]}
        for a in {a["id"]: a for a in audio.values() if a}.values()
    ]
    sources_rows = _source_rows(used, bool(recordings))
    credits = []
    for w in words:
        if w["audio"]:
            credits.append({"kind": "audio", "word": w["id"], **{k: w["audio"][k] for k in
                            ("id", "path", "source", "source_url", "author", "license", "license_url")}})
        for s in w["sentences"]:
            credits.append({"kind": "sentence", "word": w["id"], **{k: s[k] for k in
                            ("id", "source", "source_url", "author", "license", "en_author", "en_license")}})
    attribution = {"sources": sources_rows, "items": credits}

    for w in words:
        w["issues"] = notes[w["id"]]
    outliers = curation.duration_outliers(words)
    found = curation.issues(words, outliers)
    for w in words:
        del w["issues"]
    blocking_top500 = sorted({i.word_id for i in found if i.severity == "blocking"} & {w["id"] for w in words[:500]})
    raw_cognates = sum(1 for c in cards.values() if c.cognates_raw)
    extra = {
        "Cognate hints (D49)": f"{sum(1 for w in words if w['cognate_en'])} kept of {raw_cognates} words with an "
                               "etymology cognate; dropped where the English word is not among the glosses",
        "Syllable/stress mismatches": str(sum(1 for n in notes.values() if any(x.startswith("syllables:") for x in n))),
        "Audio duration outliers": ", ".join(f"`{i}`" for i in sorted(outliers)) or "none",
        "Blocking issues in the top 500": ", ".join(f"`{i}`" for i in blocking_top500) or "none",
        "Unmapped blended mass": f"{ranking.unmapped_share:.1%}",
    }
    report = coverage.render(words, deck_version=version, profile=profile, extra=extra)
    manifest = {
        "deck_version": version, "n_max": settings.n_max, "profile": profile, "inputs": inputs,
        "counts": {"words": len(words), "audio": len(media_rows), "sentences": sum(len(w["sentences"]) for w in words)},
        "coverage": coverage.summary(words),
    }
    dest = bundle.write(
        paths.dist / "deck" / version, manifest=manifest, words=words, media=media_rows, sources=sources_rows,
        attribution=attribution, coverage=report, media_dir=paths.work / "media",
    )
    (paths.dist / "deck" / "latest.json").write_text(json.dumps({"version": version}) + "\n", encoding="utf-8")

    audio_rows = {
        id_: [{"file": c.file, "url": infos[c.file].get("url") if c.file in infos else None,
               "author": media.metadata(infos[c.file], "Artist") if c.file in infos else None,
               "license": media.metadata(infos[c.file], "LicenseShortName") if c.file in infos else None,
               "region": c.region, "usable": media.usable(infos.get(c.file), profile),
               "picked": picks[id_] is not None and picks[id_].file == c.file} for c in cands]
        for id_, cands in candidates.items()
    }
    sentence_rows = {
        id_: [{"id": c.id, "de": c.de, "en": c.en, "author": c.author, "license": c.licence, "native": c.native,
               "score": c.score, "picked": c.id in {x.id for x in chosen[id_]}}
              for c in {c.id: c for c in chosen[id_] + tatoeba_best.get(id_, [])}.values()]
        for id_ in deck_ids
    }
    curation.write(paths.work / "curation.sqlite", version, words, audio_rows, sentence_rows, found)
    log(f"stage 70: {dest.relative_to(paths.root)} ({len(words):,} words, {len(media_rows):,} audio files, "
        f"{manifest['counts']['sentences']:,} sentences)")
    return dest


def _pipeline_modules() -> Iterator[Any]:
    import importlib
    import pkgutil

    import karteikasten_pipeline

    for info in sorted(pkgutil.walk_packages(karteikasten_pipeline.__path__, "karteikasten_pipeline."),
                       key=lambda i: i.name):
        if info.name.endswith(".__main__"):  # importing it would run the CLI
            continue
        yield importlib.import_module(info.name)
