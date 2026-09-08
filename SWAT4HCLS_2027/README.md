# SWAT4HCLS 2027 manuscript

- [main.tex](main.tex) and [sources.bib](sources.bib): authored manuscript and references.
- [template/](template/): unchanged CEURART class, logos and their licenses.
- [Makefile](Makefile): isolated, reproducible local build.
- `paper-draft.pdf`: generated export; `.build/`: disposable build directory.
- [Paper evidence](../coverage/paper/README.md) and [coverage assessments](../coverage/README.md): fixtures, methods, scripts and results.

## Build

From this directory:

```sh
make
```

Requires `latexmk`, `pdflatex`, BibTeX and the LaTeX packages used by CEURART,
including the `elsarticle-num-names` bibliography style (available in TeX Live).
The Makefile copies the sources and template assets into `.build/`, compiles there,
and exports `paper-draft.pdf`. Class, margins, fonts and shell-escape settings are
not altered. `npm run clean` from the repository root removes build intermediates
while retaining the exported PDF.

## Check the evidence

From the repository root:

```sh
npm run coverage:report
npm run coverage:paper -- --check
npm run validate:examples
npm run validate:force
```

The curated assessment's current claim is 104/104 inventoried logical-model
constructs under its stated rubric. The independent 4.1–4.5 assessment is provisional;
neither establishes complete VCF conformance. The paper illustration checks one
small synthetic record and must not be described as a general conversion benchmark.

This remains a working draft. Condensation to the venue's short-paper limit and
substantive human review of the scientific claims and AI-use declaration remain
editorial work before submission. Compilation and repository validation do not
establish venue compliance or publication.
