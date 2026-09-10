# Coverage assessment: reviewer checklist

Reviewer: Claude Opus 5 — VCF-expert agent review pass (human countersignature pending)  
Review date: 10 September 2026  
Findings, decisions and residual work: **[REVIEW-REPORT.md](REVIEW-REPORT.md)**

Work down this list. Tick a task when its decision or correction is recorded.
Record source decisions in [source-audit.json](generated/source-audit.json)
(`note`, `disposition`, optional `relatedRequirements`); report other corrections
by requirement/case ID. Codex can implement changes and run checks. Leave unresolved
decisions unchecked and marked `needs-review`.

This is a manual task tracker; builds do not overwrite it. Explanations and field
definitions remain in the [reviewer guide](REVIEWER-GUIDE.md).
Checkboxes do **not** replace formal acceptance in `inputs/review.json`.

Baseline, 10 September 2026: **344 source sections; 38 flagged sections; 94
requirements; 189 cases; 95 pending acceptance entries.** Counts may change after
corrections; use the regenerated files for final acceptance.

After this review pass: **344 sections; 0 flagged; 94 requirements; 189 cases; 0 pending
acceptance entries.** The assertion test inventory moved from 147/134/853 to
**146 targeted / 135 partial / 853 without a targeted case** (one gap corrected). No
coverage percentage changed — every correction was interpretive, documentary or a defect
fix, and score-raising changes were deliberately declined (see the report, Status).

## 1. Agree what the assessment should claim

- [x] Review the README's [scope](README.md#justification-and-scope) and
  [scoring](README.md#scoring-and-outcome). Confirm the two axes, exclusions and
  equal weighting of requirements. Decide whether the intended claim is
  demonstrated coverage of registered requirements; complete specification
  coverage is currently unsupported.
  **Done.** Claim accepted as demonstrated coverage of registered requirements. One scope
  correction: structured-header attribute order is not scored (VCF 4.4/4.5 explicitly permit
  discarding it), so R34 now covers identity, value and escaping only. See report §1.

## 2. Resolve the flagged source interpretations

Read each listed passage in the pinned `sources/VCFv<version>.tex`. Section IDs
give `version:start-end`. For repeated issues, record the decision in **each**
affected audit row. Supply a short reason and the intended values/interpretation;
you do not need to write a fixture or SPARQL query. Codex must apply the decision
to the authored assertions and tests before the source-review flag can close.

- [x] **Legacy GLE:** specify a valid serialization and expected genotype/likelihood
  pairs. Sections: `4.1:193-222`, `4.2:210-239`. **Resolved:** no valid serialization exists
  (the example value contains the `:` sub-field separator; 4.3 removes the key as ill-defined).
  Accepted unassessed limitation; R80 stays unassessed. Report §2.1.
- [x] **Deletion length:** resolve the example's 105 bp description versus 205 bp
  encoded by END/POS/SVLEN. Section: `4.1:468-523`. **Resolved:** 205 bp — POS/END/SVLEN agree, and the
  pinned 4.2 and 4.3 correct the prose. Report §2.2.
- [x] **Complete assembly insertion:** resolve `C<ctg1>` and the inconsistent
  POS/REF values. Sections: `4.1:586-638`, `4.2:603-655`, `4.3:1000-1052`.
  **Resolved:** the row is `13 123456 INS0 C C<ctg1>`; POS/REF were copied from the chr2
  breakend example, and 4.4 corrects them. Report §2.3.
- [x] **Legacy haplotype bundles:** specify valid BDP/BCN values and the haplotype
  associations they should represent. Sections: `4.1:911-954`, `4.2:928-971`,
  `4.3:1376-1427`.
  **Resolved:** BDP/BCN are undeclared prose-only names with no serialization anywhere and are
  deprecated in 4.4 — accepted unassessed limitation. A test is requested instead for the
  declared equivalents DPADJ/CNADJ (R79). Report §2.4.
- [x] **Quality probabilities:** resolve “posterior quality”, P(Data|Model) and
  the error-probability definitions; state the expected interpretation.
  Sections: `4.3:586-600`, `4.4:651-665`, `4.5:824-840`.
  **Resolved:** error probability — `-10 log10 (1 - Pr(Model|Data))`, per the normative GQ/CNQ
  definitions. No assessment impact. Report §2.5.
- [x] **CNL ordering:** resolve Number=G versus indexing by copy number from zero;
  state expected cardinality and order. Sections: `4.3:672-691`, `4.4:981-1002`,
  `4.5:1142-1163`.
  **Resolved:** prose indexing governs (value *i* is CN = *i* from zero); cardinality is
  data-determined. `Number=G` recorded as a specification defect. Report §2.6.
- [x] **Older gVCF examples:** confirm whether `GT:DP:GQ:P` should use `PL`.
  Sections: `4.3:1428-1451`, `4.4:1686-1711`. **Resolved:** yes, `P` is a typo for `PL` — four
  independent confirmations including GQ = second-smallest PL. Report §2.7.
- [x] **Header attribute order:** decide whether R34 should exclude order or
  retain it as an optional fidelity extension, since these versions permit
  discarding it. Sections: `4.4:105-142`, `4.5:103-140`.
  **Resolved:** exclude order from the scored requirement; keep it as an unscored fidelity
  extension. R34 corrected; no score change. Report §1 and §2.8.
- [x] **PSL/PSO phasing:** correct GT indices beyond the ALT list and specify
  expected per-allele traversal order. Sections: `4.4:445-639`, `4.5:497-812`.
  **Resolved:** PSL table excluded as an oracle (three distinct defects); corrected equivalent
  recorded. PSO example is consistent and its per-allele oracle is specified. Report §2.9.
- [x] **Repeat field names:** resolve RC/RS/RL versus RUC/RUS/RUL in the prose.
  Sections: `4.4:666-980`, `4.5:841-1141`.
  **Resolved:** RS/RL/RC are typos for RUS/RUL/RUC; corrected list is RN, RUS, RUL, RUC, RB,
  RUB. Also settles RUB nesting: RUB is partitioned by RUC, the rest by RN. Report §2.10.
- [x] **Structural-variant examples:** resolve delbp2 POS=2 versus its mate's
  chrA:5 and the DUP example's missing SVCLAIM. Sections: `4.4:1181-1233`,
  `4.5:1342-1393`.
  **Resolved:** delbp2 should read `chrA 5 delbp2 G ]chrA:2]G`; the DUP row is excluded as an
  SVCLAIM oracle because the value is undetermined. Plus a new erratum: the `<INS>` row's REF
  should be G, not T. Report §2.11.
- [x] **Partial/circular insertions:** specify corrected reciprocal mate IDs
  for self-mates and undefined `bnd_C`. Sections: `4.4:1308-1360`,
  `4.5:1468-1520`.
  **Resolved:** MATEID is unusable as an oracle throughout this subsection — the contig-side
  mates have no records, so even the first table's values are wrong. Only `bnd_Y -> bnd_X` is
  determinable; use EVENT, and test R32 on the Figure 1 example. Report §2.12.
- [x] **Sample mixtures:** decide whether the older SAMPLE Genomes/Mixture
  encoding remains a permitted extension. Sections: `4.4:1571-1615`,
  `4.5:1731-1775`.
  **Resolved:** normative in 4.1/4.2, a permitted non-normative extension in 4.3-4.5 assessed
  as generic attribute retention. Description pairing accepted as a limitation. Plus a new
  erratum: the breakend ALT coordinates name CHROM 2 for mates on CHROM 13. Report §2.13.
- [x] **Tandem-repeat examples:** resolve obsolete keys, CAGCAGCAG described as
  `(CAG)4`, and RUL/RUB nesting; state the expected counts and associations.
  Sections: `4.4:1748-1879`, `4.5:1917-2047`.
  **Resolved:** `CAGCAGCAGTTGTTG` is (CAG)3(TTG)2; corrected figure values recorded; the main
  worked example is arithmetically consistent and usable. Two new errata: the RUB example's CN
  and 4.4's `END=20000` at `POS=1000000`. Report §2.14.
- [x] **Number=P erratum:** confirm whether the main-text Number=P governs the
  erratum's Type=P. Sections: `4.4:2558-2563`, `4.5:2740-2745`.
  **Resolved:** yes — P is a Number, not a Type; the 4.5 changelog corroborates. Report §2.15.
- [x] **Mandatory FORMAT attributes:** resolve the changelog's “only INFO” claim
  against FORMAT's Number/Type/Description requirements. Sections:
  `4.4:2564-2591`, `4.5:2746-2773`.
  **Resolved:** the main text governs — both INFO and FORMAT require them; the changelog omits
  FORMAT. R03 and R52 need no change. Report §2.16.
- [x] **Base modifications:** resolve MXaoN/MxaoN capitalization and specify
  expected values/order for multiple alleles, strands and partial phasing.
  Sections: `4.5:184-248`, `4.5:497-812`.
  **Resolved:** `MXaoN` (capital X) is normative, per the reserved-key table and the SAM `MM`
  abbreviation. All four Number=M examples were manually enumerated and are consistent, so they
  serve directly as the oracle. Report §2.17.
- [x] **Local/global genotypes:** resolve GT=2/4 versus GT=2/2 in the equivalence
  example. Section: `4.5:497-812` (also has phasing/modification questions above).
  **Resolved:** `GT=2/2`. GT is not a local-allele field, and both LPL and the global PL are
  minimal at C/C. Report §2.18.
- [x] **VCF 4.5 gVCF:** resolve the separators before LEN and lengths inconsistent
  with inclusive END, including 4384–4388 with LEN=4. Section: `4.5:1846-1880`.
  **Resolved:** separators must be `:`, and LEN is inclusive, so `END = POS + LEN - 1`;
  corrected LEN values recorded. The registered fixture and decode query already do this
  correctly. Plus a new erratum: the 4396 variant row carries inapplicable MIN_DP/LEN keys.
  Report §2.19.
- [x] **VCF 4.5 changelog:** resolve Number=P's introduction version and the full
  numeric modification-key syntax. Section: `4.5:2726-2739`.
  **Resolved:** `Number=P` dates from 4.4, not 4.5; the reserved key form is
  `M[0-9]+[ACGTUN]` plus the DPM and ADM families. Report §2.20.

## 3. Check that the source inventory is complete

For **every section**, including `mapped` and excluded rows, compare the pinned
text with `assertions[].statement`, passage bounds, requirement links and
`exclusions`. Check examples and reserved field definitions too. Identify any
missing assertion, overbroad requirement or unjustified exclusion by section ID.
For assertions without suitable cases, check that `testGap` describes what remains.

- [x] VCF 4.1: all **62 sections** against [pinned source](sources/VCFv4.1.tex).
- [x] VCF 4.2: all **62 sections** against [pinned source](sources/VCFv4.2.tex).
- [x] VCF 4.3: all **71 sections** against [pinned source](sources/VCFv4.3.tex).
- [x] VCF 4.4: all **74 sections** against [pinned source](sources/VCFv4.4.tex).
- [x] VCF 4.5: all **75 sections** against [pinned source](sources/VCFv4.5.tex).
  **Done for all five versions.** The 344 sections partition every line of all five pinned
  sources with no gaps or overlaps; every assertion lies inside its section, links at least one
  valid same-version requirement, and every requirement is referenced. All 396 reserved-key
  assertions and all 119 changelog assertions were verified mechanically against their
  passages; the 619 authored VCF-zone assertion instances reduce to 150 distinct statements,
  each read individually. No VCF-zone content is excluded — the 98 `out-of-scope` sections are
  BCF, preamble and BCF-changelog material, and the 20 `context-only` ones are single-line
  headings. Report §3.1.
- [x] Review the **333 reserved declarations** in
  [declarations.json](generated/declarations.json), including extraction omissions
  and correct version/artifact selection. Their exact Number/Type matches do not
  demonstrate field meanings or values.
  **Done, with a disclosed limitation.** All 333 rows verified as faithful reproductions. The
  comparison covers only explicitly declared keys, so **29 reserved keys per version in 4.1 and
  4.2** (58 rows) are inventoried but not Number/Type-compared, because those versions define
  them in prose without a Number. Now stated in the README. Report §3.2.

## 4. Review requirements, tests and results

- [x] For each assertion labelled `partial-tests` or `no-targeted-test`, record
  **request a test** (what information/expected answer it must check) or
  **accept an unassessed limitation** (why). Start with R67/R68, which group
  reserved INFO/FORMAT meanings and values. Baseline: 134 partial and 853 without
  targeted tests; these are assertion entries, not unique requirements.
  **Done.** Recorded per assertion in `testGap` and per requirement in `interpretation`.
  Accepted limitations: R80, R94 and the SAMPLE Description pairing under R35. Tests requested:
  R79, R82, R31/R46, R84/R85, R89, R45, R92, R27 and R29, each with a specified oracle.
  Two inventory defects fixed: R27's gap misdescribed its own fixture, and the M/DPM/ADM
  assertion was marked fully targeted although ADM is never queried. Report §4.2–4.3.

For each version below, review every applicable entry in
[requirements.json](inputs/requirements.json), [cases.json](inputs/cases.json)
and [results.json](generated/results.json). Check the requirement's interpretation,
version and source anchor; each case's fixture, query and independently expected
answers; and actual outcomes for **both profiles and both axes**. Follow the
query/witness paths to inspect the supporting evidence. Use the
[README field table](REVIEWER-GUIDE.md#b-remaining-files-fields-and-results) as the field
checklist. Include requirements with no cases; record their limitations.

- [x] VCF 4.1: requirements, cases and results reviewed; corrections recorded by ID.
- [x] VCF 4.2: requirements, cases and results reviewed; corrections recorded by ID.
- [x] VCF 4.3: requirements, cases and results reviewed; corrections recorded by ID.
- [x] VCF 4.4: requirements, cases and results reviewed; corrections recorded by ID.
- [x] VCF 4.5: requirements, cases and results reviewed; corrections recorded by ID.
  All 94 requirements, 189 cases (66 distinct query/expected pairs) and 756 results reviewed
  across all five versions. Corrections: R47/R48 anchors were swapped and are fixed; the
  `repeats-v4.5.vcf` CN values were internally inconsistent and are fixed; R34/R35/R45/R49/
  R77/R79/R80/R82/R85/R92 interpretations updated. Report §4.
- [x] Specifically review VCF 4.5 condensed **structure failures R18–R21,
  R27–R30 and R60**: decide whether each exposes a vocabulary limitation or an
  assessment error. Record the reason; a preservation pass does not resolve a
  structure failure. Passing tests also need meaningful expected answers.
  **Done.** All 29 failures are condensed-profile structure queries over per-sample FORMAT
  data, and every one passes on the structure axis in the expanded profile. The condensed
  profile stores one tab-separated literal per record and FORMAT key with no per-sample node,
  so these queries cannot succeed by construction. Neither a vocabulary limitation nor an
  assessment error: a correctly reported profile design choice, now stated in the README.
  Passing answers checked too — every passing query rejects an empty graph and a
  predicate-deletion control, with no exceptions. Report §4.1.
- [x] Review [summary.json](generated/summary.json) and the README outcome:
  denominator, demonstrated/unassessed/failed counts, and stated limits. Baseline
  VCF 4.5: preservation **44/91** in both profiles; structure **44/91 expanded**,
  **35/91 condensed**. Decide whether broad requirements and remaining assertion
  gaps make these percentages too coarse for the intended claim.
  **Done.** Arithmetic checked and unchanged. The percentages are too coarse to publish bare:
  report numerator/denominator with the unassessed count beside them, and cite the assertion
  inventory as a workload measure. Report §4.4.

## 5. Close the review after corrections

- [x] Give Codex the recorded decisions/corrections to implement. Save source
  annotations before rebuilding; see the [README commands](REVIEWER-GUIDE.md#c-dispositions-and-recording-acceptance).
- [x] Recheck affected passages, requirements, cases and outcomes after the rebuild.
  Confirm every unresolved question is still flagged, and every accepted test gap
  remains visible. An unresolved source question keeps source acceptance pending.
- [x] Accept the source audit and each requirement you have reviewed in
  [review.json](inputs/review.json), using the **current** matching fingerprint
  from [review-queue.json](generated/review-queue.json), your name, date and short
  rationale. Baseline: one source acceptance plus **R01–R94**. Codex can enter
  your explicit acceptance decisions; do not approve untouched items in bulk.
  **Done for all 94 requirements plus the source audit**, each with a rationale naming what was
  checked for that item. **The `reviewer` field still needs a human name**: it currently names
  this agent pass. `inputs/review.json` is outside the provenance hash set, so editing the name
  invalidates nothing.
- [x] Have Codex run `methodology:check`, `methodology:test`, and
  `methodology:check -- --require-reviewed`. Resolve stale/missing acceptance
  entries before calling the review complete. Accepted failures and unassessed
  limitations may remain; acceptance does not turn them into coverage.
  **Done.** All four commands succeed; `check --require-reviewed` exits 0.
