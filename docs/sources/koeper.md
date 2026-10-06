# Köper & Schulte im Walde (2016): concreteness and imageability norms

Build-time filter for which nouns get pictures. Ships: no.

- `https://www.ims.uni-stuttgart.de/documents/ressourcen/experiment-daten/affective_norms.txt.gz`: 351,617 lemmas, columns `Word AbstConc Arou IMG Val`, ratings 0–10, where a higher `AbstConc` means more concrete (*Tisch* 7.77, *Hand* 6.65, *Idee* 3.69, *Freiheit* 2.34).
- **Terms: CC BY-NC-SA 4.0.** Cite Köper & Schulte im Walde (2016), LREC, and ideally the training resources named on the page.
- D26: personal builds, the development build, derive the deck's `is_concrete` from these norms. Public builds ship `is_concrete` only where a human approved or rejected an image; the norms then only pre-filter candidates.
- 760 of the top-2,000's 791 nouns have norms. Thresholds come from your labels in `reports/concreteness-labels.csv`.
