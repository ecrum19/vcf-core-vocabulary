# Specification-derived coverage assessment

**This measures demonstrated coverage of registered VCF information requirements.
It does not establish complete coverage of the specification.**

## In plain terms

We read the VCF specifications for versions 4.1 through 4.5, wrote down every
piece of information a VCF file can carry, and then tried to get each one back
out of RDF with a query. A requirement counts as covered only when a query
actually returns the answer we wrote down in advance.

One requirement, end to end:

| Step | Example |
| --- | --- |
| 1. A **requirement** read out of the spec | *"Read depth for one sample must be retrievable."* |
| 2. A **VCF fixture** exercising it | a small file whose sample column reads `0/1:42` |
| 3. Convert it to RDF | in both the expanded and condensed sample profiles |
| 4. A **query** plus the answer we expect | `SELECT ?sample ?depth …` → we write `SAMPLE1, 42` **before** running it |
| 5. Compare | the query returns `SAMPLE1, 42` → this requirement is `demonstrated` |

Three rules make the number conservative rather than flattering:

- **Expected answers are authored from the specification, never copied from query
  output.** Otherwise the test would only prove the code agrees with itself.
- **Untested requirements count against the score.** They sit in the denominator
  as `unassessed`. This is why the percentages sit around a half rather than in
  the 90s: 40 of the 91 VCF 4.5 requirements have no test yet, and each scores zero.
- **Every passing query must also fail on purpose.** It is re-run against an
  empty graph and against a graph with the relevant predicate deleted. If it
  still passes, it was not really reading the data, and it does not count.

So a low percentage here means "we have not demonstrated this yet", not "the
vocabulary cannot do this". The two are easy to confuse and we keep them apart
deliberately.

### What the untested requirements actually are

For VCF 4.5, 51 of the 91 requirements have a passing test and **40 do not**. It is worth
being precise about why, because the honest answer is not flattering in the way people
usually assume:

| Why a requirement has no test | Count |
| --- | ---: |
| A test plan is written and nobody has built the fixture and query yet | 37 |
| Deliberately withdrawn: the specification text it needs is disputed upstream (R45, [hts-specs#868](https://github.com/samtools/hts-specs/issues/868)) | 1 |
| One requirement standing for hundreds of separate keys — R67 and R68 cover *every* reserved INFO and FORMAT key, 396 authored assertions between them | 2 |
| The vocabulary cannot represent it | **0** |

**The gap is unwritten work, not a limit of the vocabulary.** Nothing sits in the untested
column because the model could not express it. Two facts support that reading: no query
has ever failed in the expanded profile — all 45 failing witnesses are condensed-profile
structure queries, which is a deliberate storage trade-off described below — and every test
added so far passed once its expected answer was correct.

That said, the specification does make some rules hard to test, and that is a real effect,
just a smaller one. It shows up *inside* requirements that are otherwise tested, as gaps
recorded against them: the specification states a rule and prints no record exercising it.
`PSQ`, the `PS`-versus-`PSL` exclusion and the alias-to-ChEBI correspondence are all in that
position, and the cases covering them use records the reviewer had to author, labelled as
such. `<NON_REF>` aliasing, `U`/`T` equivalence and `CICNADJ` remain untested for exactly
this reason — there is nothing printed to check an answer against. Where no defensible
oracle exists at all, the requirement is recorded as an accepted limitation rather than
quietly skipped: R80 (GLE) and R94 (BDP/BCN) in the older versions. For how this compares with the repository's other assessment, see
[why there are two](../README.md#why-there-are-two-assessments).

### The two axes

Every requirement is scored twice, and the second is stricter than the first:

| Axis | What a passing test demonstrates |
| --- | --- |
| **Preservation** | Requested information can be retrieved, including by explicitly decoding VCF text literals. |
| **Structure** | Requested components are accessible through RDF properties/indices without parsing compound VCF literals. |

A requirement can pass preservation and fail structure — the information is
there, but only inside a string you have to take apart yourself.

## Review status

**Reviewed and accepted by Elias Crum on 11 September 2026.** Every requirement and
the source audit carry a recorded decision in [review.json](inputs/review.json), and
`methodology:check --require-reviewed` exits 0. [REVIEW-REPORT.md](REVIEW-REPORT.md)
holds the findings, the resolved source questions, the limitations accepted rather
than fixed, and the reviewer reference for the files and fields.

Two agent passes prepared the material and the reviewer signed each item against its
evidence. The 83 requirements not revisited in that signing session keep the earlier
pass's rationale and still name it in their `reviewer` field; the twelve that gained
or lost evidence were re-decided individually.

## Which document do you want?

| Document | Use it for |
| --- | --- |
| This README | What is measured, how, the current results, and the limits. Start here. |
| [REVIEW-REPORT.md](REVIEW-REPORT.md) | The review record: what was found, what changed, what is still open, and what every file and field means. |

## Justification and scope

We adapt requirements-based ontology evaluation; there is no universal published
VCF-to-vocabulary coverage score.

| Precedent | Adaptation / limit |
| --- | --- |
| Poveda-Villalón et al. (2022), [LOT](https://doi.org/10.1016/j.engappai.2022.104755) ([method](https://lot.linkeddata.es/)) | Derive and review information requirements from source documents. LOT does not prescribe our percentages. |
| Publications Office, [eProcurement Ontology report](https://docs.ted.europa.eu/EPO/3.0.1/Report-v3.0.0.html), [architecture §§3.4–3.5](https://docs.ted.europa.eu/epo-home/REFePO_Arch_Design.html) | Relate specification terms/structures to ontology patterns and test retrieval. Its coverage goal is not independent evidence of achieved coverage. |
| Peroni (2016), [SAMOD](https://essepuntato.it/papers/samod-owled2016.html) | Pair a scenario/question, RDF witness, query and independently expected answers. We adapt this test-case idea retrospectively, not the entire development process. |

Our axes, requirement granularity and scoring are **operational choices**, not
metrics validated by those publications.

Identity, field meaning, version context, ordering and missingness are in scope.
A dedicated term per field is unnecessary if a generic resource preserves its
identity and meaning. Byte layout, punctuation enforcement, invalid-input
rejection, BCF encoding, compression, indexing and producer estimation algorithms
are excluded. Each section records its exclusions explicitly. Representing a
reported estimate does not establish that the producer calculated it correctly.
Structured-header attribute ordering is **not scored**: VCF 4.4/4.5 state that
implementations must not rely on it and are not required to preserve it, and
4.1–4.3 nowhere give it meaning, so it is recorded only as an optional
round-trip fidelity extension. (This is distinct from R02, the order of
meta-information lines themselves, which is scored.)

## Process and files

Pinned VCF text → authored source assertions → requirements → VCF fixtures →
RDF in expanded/condensed profiles → queries versus independent answers → results.

- [sources.lock.json](sources.lock.json) pins [VCF 4.1–4.5 sources](sources/).
- [source-assertions.json](inputs/source-assertions.json) contains Codex's authored
  passage interpretations, explicit requirement/case links, exclusions and review
  questions. It is input data, not automatic semantic extraction or human approval.
- [requirements.json](inputs/requirements.json) defines capabilities, versions,
  source anchors and interpretations. New requirements include a concrete `testPlan`.
- [cases.json](inputs/cases.json) binds each case to a requirement/version,
  [fixture](fixtures/), [query](queries/) and independently authored expected rows.
- [assess.py](scripts/assess.py) runs the existing converter against the current
  vocabulary; [source.py](scripts/source.py) inventories sections/declarations;
  [source_review.py](scripts/source_review.py) checks links and preserves annotations.
- [generated results](generated/results.json), [summary](generated/summary.json),
  [RDF witnesses](generated/witnesses/), [source audit](generated/source-audit.json)
  and [review queue](generated/review-queue.json) expose evidence and remaining work.
  [Provenance](generated/provenance.json) records input hashes;
  [fixture origins](inputs/fixture-origins.json) identify reused examples.

Execution is offline. Expected answers never come from query output. Existing
example answers were reused and checked against source text; added header-audit
answers were authored from their fixtures. Every passing query rejects an empty
graph and an applicable predicate-deletion control. Vocabulary terms and property
object kinds are checked. These safeguards establish data dependence, not complete
semantic correctness or OWL consistency. Converter errors stop the workflow;
they do not establish vocabulary incapability.

## Scoring and outcome

For each VCF version/profile/axis, the denominator includes **all applicable
registered requirements**, including untested ones. `demonstrated` means all
supplied tests pass; `partial` means some pass; `not-demonstrated` means tested
but none pass; `unassessed` means no test. Only demonstrated requirements count
in the numerator. No fractional credit or union across axes/versions is used.

A passing finite example does not establish arbitrary-input fidelity. A failed
witness does not prove that no suitable RDF representation exists.
A requirement can have passing cases while the source audit identifies additional
assertions that those cases do not exercise. **Read assertion test gaps alongside
the scores.** Assertion counts repeat information across sections and versions;
they are an audit workload inventory, not another coverage denominator.

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

The source audit added R51–R94 after identifying omitted capabilities. Scores
therefore use a larger register than the earlier 50-requirement assessment.
Added cases cover FILTER declarations and record-to-definition links, FORMAT
attributes, ALT declarations, contig metadata, pedigree roles/URLs, sites-only
files, cardinality/types, escaped strings, SAMPLE/META metadata and sample FT
filter states/codes. The review pass then asked for nine more, all now registered:
adjacency depth and copy number (R79), phase-set ordinals (R82), the RN
partitioning of flattened repeat lists (R31/R46), tandem-repeat length ratios
(R89), reference blocks and their lengths (R45), assembly-contig insertions (R92),
base-modification value slots and key families (R84/R85), a non-identity local
allele set (R27) and the two modification depths separately (R29). Missing
cases remain explicit; adding a requirement never fabricates a passing outcome.

Reserved declaration agreement checks explicit Number/Type rows only. It does
not establish the meanings or instance values of every reserved field. The three
modification-pattern rows are compared as patterns, without testing every
possible concrete identifier. Source ambiguities and test gaps prevent a claim
of complete specification coverage.

**The 333 compared rows are not every reserved key.** They are the keys the
sources declare explicitly, in `##INFO=` / `##FORMAT=` blocks or in the reserved-key
tables: 31 rows for 4.1, 31 for 4.2, 69 for 4.3, 79 for 4.4 and 123 for 4.5.
VCF 4.1 and 4.2 define a further **29 reserved keys each** — 16 INFO
(AA, AC, AF, AN, BQ, CIGAR, DB, H2, H3, MQ, MQ0, NS, SB, SOMATIC, VALIDATED, 1000G)
and 13 FORMAT (GT, DP, FT, GL, GLE, GP, GQ, HQ, PL, PQ, PS, EC, MQ) — in prose
bullets that give no Number and, for INFO, no Type. Those 58 rows are inventoried
as source assertions but **cannot** be Number/Type-compared, so the agreement figure
is weighted towards 4.3–4.5. Four of the 333 rows are duplicate declarations of the
same key in one source (4.3 DP and END, 4.4/4.5 END); the duplicates agree.

**Number/Type agreement is not semantic agreement.** CNL and CNP are declared
`Number=G` in 4.3–4.5 while the normative prose indexes them by copy number from
zero; the declaration is reproduced faithfully and is still inconsistent with the
field's stated meaning.

**What the condensed structure column measures.** All 45 failing witnesses are
condensed-profile structure queries over per-sample FORMAT data (R18–R21 and R60 in
every version; R79 in 4.1–4.3; R82 and R89 in 4.4 and 4.5; and R27–R30, R83, R84 and
R85 in 4.5). The condensed profile deliberately stores
one tab-separated `vcfc:encodedValues` literal per record and FORMAT key, aligned
to the sample set, instead of materialising per-sample nodes; the structure axis
forbids parsing compound literals, so those queries cannot succeed by construction.
Every one of them passes on the structure axis in the expanded profile. That column
therefore measures a **profile design choice**, not a limit of the vocabulary, and
must not be read as "the vocabulary cannot expose per-sample values structurally".

## Reproduce

From the repository root with `requirements-dev.txt` installed:

```sh
npm run methodology:build
npm run methodology:check
npm run methodology:test
npm run methodology:check -- --require-reviewed
```

`check` recomputes without writing and fails on stale output. The final command
returns 2 while human acceptance is incomplete/stale. Changes to evidence
invalidate acceptance. [Regression tests](tests/test_assessment.py) check these
measurement and audit safeguards.
