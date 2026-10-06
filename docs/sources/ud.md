# Universal Dependencies: German GSD and HDT (r2.18)

POS ratios for ambiguous forms, and particle-verb statistics. Ships: ratios only.

- Where: `UniversalDependencies/UD_German-GSD` and `UD_German-HDT`, tag `r2.18`. GSD has train/dev/test; HDT has train-a-1, a-2, b-1, b-2, dev and test. Together 3.69M tokens.
- Licences (`LICENSE.txt` in each repo): GSD is CC BY-SA 4.0. For HDT the annotation is CC BY-SA 4.0, but its text "can be distributed for academic use". That's fine here: only derived ratios are used, and the text is never redistributed.
- Format: CoNLL-U, read by `readers/conllu.py` (nixpkgs has no Python package for it). Multiword tokens (*im* = *in* + *dem*) are counted once, as their surface token.
- STTS tags (XPOS column) matter more than UPOS here. Negation *nicht* is `PART/PTKNEG` (an adverb in Wiktionary). Infinitive *zu* is `PTKZU`, *zu* meaning "too" is `PTKA`, postposed *nach* is `APPO`, and a separated verb particle is `PTKVZ`.
- Separable verbs: in both treebanks a separated use keeps the base lemma on the finite verb, with the particle attached as `compound:prt` (*rief … an* → *rufen* + *an*). Unsplit forms carry the full lemma (*anrufen*, *angerufen*, *anzurufen*). Overall there are 0.51 split uses per unsplit use; per verb, *anfangen* 0.52, *aufhören* 0.66, *ankommen* 0.87, *anrufen* 0.37.
- Lemma conventions differ from Wiktionary's. For example, UD lemmatises *alle* as *alle* (Wiktionary: *all*) and *Leute* mostly as archaic *Leut*. Stage 30 therefore matches UD evidence by POS first and uses the lemma only to choose among same-POS candidates, and archaic entries give way to current ones.
