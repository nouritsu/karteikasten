"""Regenerate tests/fixtures/snapshot.tar.gz, a tiny slice of every source.

The slice holds the spec's tricky words (Testing: tricky-word table), every other
lemma that shares a form with them, and some context, so the real build runs on
it offline in a few seconds. Corpus counts keep their proportions but are scaled
down; Leipzig is rebuilt as synthetic sentences that keep each form's
sentence-initial share. Commons audio is left out: the slice names the files of
the tricky words only, and the tests write a tone for each.

The slice is excerpts of the sources under their own licences: Wiktionary via
Kaikki and UD (CC BY-SA 4.0), Tatoeba (CC BY 2.0 FR, some CC0), Commons file
metadata; the FrequencyWords and Leipzig parts are scaled counts only. DeReWo is
never part of it.

Run after a full build, from the dev shell inside the checkout:
    python pipeline/tests/fixtures/make_snapshot.py
"""

import bz2
import gzip
import io
import json
import pickle
import re
import sys
import tarfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "pipeline"))

from karteikasten_pipeline.fetch import commons  # noqa: E402
from karteikasten_pipeline.readers import conllu  # noqa: E402
from karteikasten_pipeline.stages import media  # noqa: E402

OUT = Path(__file__).with_name("snapshot.tar.gz")
TRICKY = [
    "sein#verb#1", "sein#det#2", "der#article#1", "der#pron#1", "Bank#noun#1", "Bank#noun#2",
    "Essen#noun#1", "essen#verb#1", "Morgen#noun#1", "morgen#adv#1", "Sie#pron#1", "sie#pron#1", "sie#pron#2",
    "anfangen#verb#1", "aufhören#verb#1", "ankommen#verb#1", "anrufen#verb#1",
    "fangen#verb#1", "hören#verb#1", "kommen#verb#1", "rufen#verb#1",
    "Junge#noun#1", "Herr#noun#1", "Leute#noun#1", "Eltern#noun#1",
    "haben#verb#1", "werden#verb#1", "können#verb#1", "wissen#verb#1", "fahren#verb#1", "freuen#verb#1",
    "sich#pron#1", "gut#adj#1", "viel#det#1", "gern#adv#1", "hoch#adj#1",
    "mit#prep#1", "für#prep#1", "in#prep#1", "wegen#prep#1", "an#prep#1", "auf#prep#1",
    "weil#conj#1", "und#conj#1", "doch#particle#1", "doch#adv#1", "doch#conj#1", "mal#adv#1", "ja#adv#1",
    "ja#intj#1", "danke#intj#1", "okay#intj#1", "okay#adj#1", "äh#intj#1", "zwei#num#1", "ich#pron#1", "du#pron#1", "er#pron#1", "Hand#noun#1",
    "Haus#noun#1", "Jahr#noun#1", "schon#adv#1", "sehr#adv#1",
]
# Only the fields the pipeline reads; the rest (translations, descendants, ...) is bulk.
KEEP = {
    "word", "pos", "pos_title", "lang_code", "etymology_number", "etymology_text", "senses", "forms", "sounds",
    "hyphenations", "head_templates", "categories", "derived",
}
SENSE_KEEP = {"glosses", "tags", "raw_tags", "form_of", "alt_of", "examples", "categories"}
SCALE = 200  # corpus counts are divided by this
UD_PER_FORM, UD_PER_PARTICLE_VERB, TATOEBA_PER_WORD = 4, 8, 12


def slim(entry: dict) -> dict:
    entry = {k: v for k, v in entry.items() if k in KEEP}
    entry["senses"] = [{k: v for k, v in s.items() if k in SENSE_KEEP} for s in entry.get("senses", [])]
    entry["derived"] = [{"word": d["word"]} for d in entry.get("derived", []) if "word" in d][:60]
    return entry


def jsonl_gz(entries: list[dict]) -> bytes:
    text = "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n" for e in entries)
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0) as gz:
        gz.write(text.encode())
    return buffer.getvalue()


def tsv_bz2(rows: list[list[str]]) -> bytes:
    return bz2.compress("".join("\t".join(r) + "\n" for r in rows).encode())


def tar_gz(files: dict[str, bytes]) -> bytes:
    """A tar.gz with fixed metadata, so the same files give the same bytes."""
    plain = io.BytesIO()
    with tarfile.open(fileobj=plain, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for name in sorted(files):
            info = tarfile.TarInfo(name)
            info.size, info.mtime, info.mode = len(files[name]), 0, 0o644
            tar.addfile(info, io.BytesIO(files[name]))
    packed = io.BytesIO()
    with gzip.GzipFile(fileobj=packed, mode="wb", mtime=0) as gz:
        gz.write(plain.getvalue())
    return packed.getvalue()


def latest(stage: str) -> Path:
    found = sorted((ROOT / "data/work/cache").glob(f"{stage}-*.pickle"), key=lambda p: p.stat().st_mtime)
    if not found:
        sys.exit(f"no cached {stage}; run a full build first")
    return found[-1]


def main() -> None:
    lex, en_index, de_index = pickle.loads(latest("lexicon").read_bytes())
    ids = [i for i in TRICKY if i in lex.lemmas]
    missing = sorted(set(TRICKY) - set(ids))
    if missing:
        print("not in the lexicon (left out):", ", ".join(missing), file=sys.stderr)
    forms: dict[str, set[str]] = defaultdict(set)  # id -> its forms
    for form, cands in lex.candidates.items():
        for id_ in cands & set(ids):
            forms[id_].add(form)
    all_forms = {f for fs in forms.values() for f in fs} | {lex.lemmas[i].word for i in ids}
    # Every lemma that shares a form competes for its counts, so it comes along.
    rivals = {i for f in all_forms for i in lex.candidates.get(f, ())}
    words = all_forms | {lex.lemmas[i].word for i in rivals}
    # Ordinals are their own entries (zweite), found through the numeral's derived terms.
    numerals = [lex.lemmas[i].word for i in ids if lex.lemmas[i].pos == "num"]
    words |= {w for w in lex.ordinals if any(w.startswith(n) for n in numerals)}

    files: dict[str, bytes] = {}
    en_keys = [k for k in en_index.offsets if k.split("#")[0] in words]
    en = [slim(e) for es in en_index.get(en_keys).values() for e in es]
    de = [slim(e) for es in de_index.get(words).values() for e in es]
    files["kaikki-en/raw-wiktextract-data.jsonl.gz"] = jsonl_gz(en)
    files["kaikki-de/de-extract.jsonl.gz"] = jsonl_gz(de)

    lower = {w.lower() for w in words}
    spoken = []
    for line in (ROOT / "data/raw/frequencywords/de_full.txt").open(encoding="utf-8"):
        word, _, count = line.rstrip("\n").rpartition(" ")
        if word in lower or word in ("hey", "mr", "okay"):
            spoken.append(f"{word} {max(1, int(count) // SCALE)}\n")
    files["frequencywords/de_full.txt"] = "".join(spoken).encode()

    written = pickle.loads(latest("written").read_bytes())
    for half, corpus in enumerate(("deu_news_2025_1M", "deu-de_web_2021_1M")):
        words_txt, inv, sentence = ["1\txq\t0\n"], [], 0
        filler_uses = 0
        for word_id, form in enumerate(sorted(f for f in written if f in words), start=2):
            total, initial = written[form]
            total, initial = (max(1, total // SCALE) + half) // 2, (initial // SCALE + half) // 2
            if total == 0:
                continue
            words_txt.append(f"{word_id}\t{form}\t{total}\n")
            for _ in range(initial):
                sentence += 1
                inv.append(f"{word_id}\t{sentence}\t0\n")
            if total > initial:
                sentence += 1
                inv.append(f"1\t{sentence}\t0\n")
                filler_uses += 1
                inv += [f"{word_id}\t{sentence}\t{k}\n" for k in range(1, total - initial + 1)]
        words_txt[0] = f"1\txq\t{filler_uses}\n"
        files[f"leipzig/{corpus}.tar.gz"] = tar_gz({
            f"{corpus}/{corpus}-words.txt": "".join(words_txt).encode(),
            f"{corpus}/{corpus}-inv_w.txt": "".join(inv).encode(),
        })

    focus = {f.lower() for f in all_forms}
    per_form: dict[str, int] = defaultdict(int)
    per_verb: dict[str, int] = defaultdict(int)
    separable = {lex.lemmas[i].word for i in ids if i in lex.separable}
    chosen = []
    for path in sorted((ROOT / "data/raw/ud").glob("*/*.conllu")):
        for sentence in conllu.read(path):
            by_id = {w.id: w for w in sentence}
            split = {w.lemma.lower() + by_id[w.head].lemma for w in sentence if w.deprel == "compound:prt" and w.head in by_id}
            wanted = [v for v in split if v in separable and per_verb[v] < UD_PER_PARTICLE_VERB]
            hits = [w.token.lower() for w in sentence if w.token.lower() in focus and per_form[w.token.lower()] < UD_PER_FORM]
            if not wanted and not hits:
                continue
            for v in wanted:
                per_verb[v] += 1
            for h in set(hits):
                per_form[h] += 1
            chosen.append(sentence)
    lines = []
    for sentence in chosen:
        lines.append("# fixture\n")
        for i, w in enumerate(sentence):
            if w.token_start:
                last = i
                while last + 1 < len(sentence) and not sentence[last + 1].token_start:
                    last += 1
                if last > i:  # a contraction such as "im": its range line comes first
                    lines.append(f"{w.id}-{sentence[last].id}\t{w.token}\t_\t_\t_\t_\t_\t_\t_\t_\n")
            lines.append(f"{w.id}\t{w.form}\t{w.lemma}\t{w.upos}\t{w.xpos}\t_\t{w.head}\t{w.deprel}\t_\t_\n")
        lines.append("\n")
    files["ud/gsd/de_gsd-ud-train.conllu"] = "".join(lines).encode()

    t = ROOT / "data/raw/tatoeba"

    def rows(name: str):
        from karteikasten_pipeline.readers.tatoeba import _rows

        return _rows(t / name)

    token = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*")
    per_word: dict[str, int] = defaultdict(int)
    form_owner = {f: i for i in ids for f in forms[i]}
    links: dict[int, list[int]] = defaultdict(list)
    for row in rows("deu-eng_links.tsv.bz2"):
        if len(row) >= 2:
            links[int(row[0])].append(int(row[1]))
    german = []
    for row in rows("deu_sentences_detailed.tsv.bz2"):
        if len(row) < 4 or int(row[0]) not in links:
            continue
        owners = {form_owner[x] for x in token.findall(row[2]) if x in form_owner}
        owners = {o for o in owners if per_word[o] < TATOEBA_PER_WORD}
        if not owners or not 4 <= len(token.findall(row[2])) <= 10:
            continue
        for o in owners:
            per_word[o] += 1
        german.append(row)
    german_ids = {int(r[0]) for r in german}
    english_ids = {e for d in german_ids for e in links[d]}
    english = [r for r in rows("eng_sentences_detailed.tsv.bz2") if len(r) >= 4 and int(r[0]) in english_ids]
    authors = {r[3] for r in german}
    files["tatoeba/deu_sentences_detailed.tsv.bz2"] = tsv_bz2(german)
    files["tatoeba/eng_sentences_detailed.tsv.bz2"] = tsv_bz2(english)
    files["tatoeba/deu-eng_links.tsv.bz2"] = tsv_bz2([[str(d), str(e)] for d in sorted(german_ids) for e in links[d]])
    files["tatoeba/deu_sentences_CC0.tsv.bz2"] = tsv_bz2(
        [r for r in rows("deu_sentences_CC0.tsv.bz2") if r and int(r[0]) in german_ids])
    files["tatoeba/eng_sentences_CC0.tsv.bz2"] = tsv_bz2(
        [r for r in rows("eng_sentences_CC0.tsv.bz2") if r and int(r[0]) in english_ids])
    files["tatoeba/deu_tags.tsv.bz2"] = tsv_bz2(
        [r for r in rows("deu_tags.tsv.bz2") if len(r) >= 2 and int(r[0]) in german_ids])
    files["tatoeba/deu_user_languages.tsv.bz2"] = tsv_bz2(
        [r for r in rows("deu_user_languages.tsv.bz2") if len(r) >= 3 and r[2] in authors])

    # Audio only for the tricky words themselves: each file costs an ffmpeg run per test build.
    from karteikasten_pipeline.stages.lexicon import entry_id

    tricky_words = {lex.lemmas[i].word for i in ids}
    voiced = [e for e in en if entry_id(e) in set(ids)] + [e for e in de if e["word"] in tricky_words]
    titles = sorted({c.file for e in voiced for c in media.audio_candidates([e])})
    known: dict[str, dict | None] = {}
    lock = json.loads((ROOT / "sources.lock.json").read_text())["files"]
    for relative in sorted(p for p in lock if p.startswith("commons/info/")):
        known.update(commons.answers(json.loads((ROOT / "data/raw" / relative).read_text())))
    pages = [{"title": f"File:{t}", "imageinfo": [known[f"File:{t}"]]} for t in titles if known.get(f"File:{t}")]
    # The other words' files are answered as missing, so an offline build skips them.
    voiced_titles = {p["title"] for p in pages}
    others = sorted({c.file for e in en + de for c in media.audio_candidates([e])} - set(titles))
    pages += [{"title": f"File:{t}", "missing": True} for t in others if f"File:{t}" not in voiced_titles]
    files["commons/info/fixture.json"] = json.dumps({"query": {"pages": pages}}, ensure_ascii=False,
                                                     sort_keys=True, indent=1).encode()

    OUT.write_bytes(tar_gz(files))
    sizes = ", ".join(f"{n} {len(b) // 1024} KiB" for n, b in sorted(files.items()) if len(b) > 20_000)
    print(f"{OUT}: {OUT.stat().st_size // 1024} KiB ({len(en)} en and {len(de)} de entries, {len(chosen)} UD "
          f"sentences, {len(german)} Tatoeba sentences, {len(pages)} audio titles). Large: {sizes}")


if __name__ == "__main__":
    main()
