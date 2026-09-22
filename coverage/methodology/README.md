# Specification-derived coverage assessment

**This measures demonstrated coverage of registered VCF information requirements.
It does not establish complete coverage of the specification.**

## In plain terms

We read the VCF 4.1–4.5 specifications, wrote down every piece of information a VCF
file can carry, and then tried to get each one back out of RDF with a query. A
requirement counts as covered only when a query returns the answer we wrote down in
advance.

| Step | Example |
| --- | --- |
| 1. A **requirement** read out of the spec | *"Read depth for one sample must be retrievable."* |
| 2. A **fixture** exercising it | a small file whose sample column reads `0/1:42` |
| 3. Convert to RDF | in both the expanded and condensed sample profiles |
| 4. A **query** plus its expected answer | `SELECT ?sample ?depth …` → we write `SAMPLE1, 42` **before** running it |
| 5. Compare | the query returns `SAMPLE1, 42` → `demonstrated` |

Three rules keep the number conservative:

- **Expected answers are authored from the specification**, never copied from query
  output, so a test cannot prove only that the code agrees with itself.
- **Untested requirements score zero** and stay in the denominator. This is why the
  percentages sit near a half rather than in the 90s.
- **Every passing query must also be able to fail.** It is re-run against an empty
  graph and against a graph with the relevant predicate deleted.

A low percentage means "not yet demonstrated", not "the vocabulary cannot do this".

### What the untested requirements are

For VCF 4.5, 51 of 91 requirements have a passing test and **40 do not**:

| Why a requirement has no test | Count |
| --- | ---: |
| A test plan exists; the fixture and query are unwritten | 37 |
| Withdrawn: its specification text is disputed upstream (R45, [hts-specs#868](https://github.com/samtools/hts-specs/issues/868)) | 1 |
| One requirement standing for hundreds of keys — R67/R68 cover *every* reserved INFO and FORMAT key | 2 |
| The vocabulary cannot represent it | **0** |

**The gap is unwritten work, not a limit of the model.** No query has ever failed in
the expanded profile; all 45 failing witnesses are condensed-profile structure
queries, a deliberate storage trade-off described below.

Some rules are genuinely hard to test because the specification states them without
printing a record to check against — `PSQ`, the `PS`/`PSL` exclusion, `<NON_REF>`
aliasing, `U`/`T` equivalence and `CICNADJ`. Where no defensible oracle exists the
requirement is recorded as an accepted limitation rather than quietly skipped: R80
(GLE) and R94 (BDP/BCN).

### The two axes

**Preservation** — the information can be retrieved, including by decoding a VCF text
literal. **Structure** — it is reachable through RDF properties and indices without
parsing a compound literal. A requirement can pass the first and fail the second.

## Review status

**Reviewed and accepted by Elias Crum on 11 September 2026**, with the reviewer
recorded on all 94 requirements since 2.1.3. Every requirement and the source audit
carry a decision in [review.json](inputs/review.json), and
`methodology:check --require-reviewed` exits 0.
[REVIEW-REPORT.md](REVIEW-REPORT.md) holds the findings, the resolved source
questions and the accepted limitations.

Two agent passes prepared the material; the reviewer signed each item against its
evidence, and the queries and expected answers were subsequently hand-checked.

## Scoring

For each version, profile and axis the denominator includes **all applicable
requirements**, including untested ones. `demonstrated` means every supplied test
passes, `partial` some, `not-demonstrated` none, `unassessed` no test. Only
demonstrated requirements count in the numerator; there is no fractional credit and
no union across axes or versions.

A passing finite example does not establish arbitrary-input fidelity, and a failed
witness does not prove no suitable representation exists. Assertion counts repeat
across sections and versions: they are an audit workload inventory, not a second
coverage denominator.

<!-- results:start -->
**94 registered requirements; 210 cases; 840 query slots** (two profiles × two axes).

| VCF | Requirements | Expanded: preservation / structure | Condensed: preservation / structure |
| --- | ---: | --- | --- |
| 4.1 | 69 | 32 (46.4%) / 32 (46.4%) | 32 (46.4%) / 26 (37.7%) |
| 4.2 | 72 | 34 (47.2%) / 34 (47.2%) | 34 (47.2%) / 28 (38.9%) |
| 4.3 | 74 | 35 (47.3%) / 35 (47.3%) | 35 (47.3%) / 29 (39.2%) |
| 4.4 | 83 | 38 (45.8%) / 38 (45.8%) | 38 (45.8%) / 31 (37.3%) |
| 4.5 | 91 | 51 (56.0%) / 51 (56.0%) | 51 (56.0%) / 37 (40.7%) |

**Reserved declarations:** 333/333 explicit source rows match RDF Number/Type; 0 missing, 0 different.
**Human review:** 0 pending items; source completeness accepted.

**Source audit:** 344 sections; 1134 authored assertion entries; 0 sections flagged `needs-review`.
**Assertion test inventory:** 149 with targeted cases, 154 with partial test evidence, 831 without a targeted case. These are test-presence categories, not passing-coverage scores.

For VCF 4.5, 14 condensed structural witnesses fail; 40 requirements lack tests.
<!-- results:end -->

### Reading the numbers

**The 333 compared rows are not every reserved key.** They are the keys the sources
declare explicitly in `##INFO=`/`##FORMAT=` blocks or reserved-key tables. VCF 4.1
and 4.2 define a further 29 reserved keys each in prose bullets that give no Number
and, for INFO, no Type, so the agreement figure is weighted towards 4.3–4.5.

**Number/Type agreement is not semantic agreement.** CNL and CNP are declared
`Number=G` in 4.3–4.5 while the normative prose indexes them by copy number from
zero; the declaration is reproduced faithfully and remains inconsistent with the
field's stated meaning.

**The condensed structure column measures a profile choice.** All 45 failing
witnesses are condensed-profile structure queries over per-sample FORMAT data. That
profile deliberately stores one tab-separated `vcfc:encodedValues` literal per record
and FORMAT key instead of per-sample nodes, and the structure axis forbids parsing
compound literals, so those queries cannot succeed by construction. Every one passes
the structure axis in the expanded profile.

## Scope

Identity, field meaning, version context, ordering and missingness are in scope. Byte
layout, punctuation enforcement, invalid-input rejection, BCF encoding, compression,
indexing and producer estimation algorithms are excluded, and each section records
its own exclusions. Structured-header attribute ordering is not scored, because
4.4/4.5 state implementations must not rely on it; R02, the order of meta-information
lines, is scored. Representing a reported estimate does not establish that the
producer calculated it correctly.

The design adapts requirements-based ontology evaluation — LOT for deriving and
reviewing requirements from source documents, and SAMOD for pairing a question, an
RDF witness, a query and independently authored answers. The axes, requirement
granularity and scoring are **operational choices**, not metrics validated by those
publications.

## Files

Pinned VCF text → authored source assertions → requirements → fixtures → RDF in both
profiles → queries versus independent answers → results.

| | |
| --- | --- |
| [sources.lock.json](sources.lock.json) | Pins the [VCF 4.1–4.5 sources](sources/) by SHA-256 |
| [source-assertions.json](inputs/source-assertions.json) | Authored passage interpretations, requirement links, exclusions and review questions |
| [requirements.json](inputs/requirements.json) | Capabilities, versions, source anchors, interpretations, `testPlan` |
| [cases.json](inputs/cases.json) | Binds each case to a requirement, version, [fixture](fixtures/), [query](queries/) and expected rows |
| [scripts/](scripts/) | `assess.py` runs the assessment; `source.py` and `source_review.py` inventory and check the audit |
| [generated/](generated/) | Results, summary, witnesses, source audit, review queue and input-hash provenance |

Execution is offline and expected answers never come from query output. Converter
errors stop the workflow; they do not establish vocabulary incapability.

## Reproduce

From the repository root with `requirements-dev.txt` installed:

```sh
npm run methodology:build
npm run methodology:check
npm run methodology:test
npm run methodology:check -- --require-reviewed
```

`check` recomputes without writing and fails on stale output. Changes to evidence
invalidate acceptance. [Regression tests](tests/test_assessment.py) cover these
safeguards.
