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
  as `unassessed`. This is why the percentages are in the 40s rather than the 90s:
  47 of the 91 VCF 4.5 requirements have no test yet, and each scores zero.
- **Every passing query must also fail on purpose.** It is re-run against an
  empty graph and against a graph with the relevant predicate deleted. If it
  still passes, it was not really reading the data, and it does not count.

So a low percentage here means "we have not demonstrated this yet", not "the
vocabulary cannot do this". The two are easy to confuse and we keep them apart
deliberately. For how this compares with the repository's other assessment, see
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

Source interpretations, test adequacy and exclusions have been reviewed once
against the pinned specifications; see [REVIEW-REPORT.md](REVIEW-REPORT.md) for
the findings, the resolved source questions and the limitations accepted rather
than fixed. The acceptance entries in [review.json](inputs/review.json) name that
reviewing pass and **still need a human countersignature**: replace the `reviewer`
field with the accepting person's name (`review.json` is excluded from the
provenance hashes, so this does not invalidate any fingerprint).

## Which document do you want?

| Document | Use it for |
| --- | --- |
| This README | What is measured, how, the current results, and the limits. Start here. |
| [REVIEWER-GUIDE.md](REVIEWER-GUIDE.md) | Reviewing the assessment: what every file and field means, which to edit, how acceptance is recorded. |
| [REVIEW-CHECKLIST.md](REVIEW-CHECKLIST.md) | The reviewer's task tracker. |
| [REVIEW-REPORT.md](REVIEW-REPORT.md) | Findings and decisions from the completed review pass. |

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
**94 registered requirements; 189 cases; 756 query slots** (two profiles × two axes).

| VCF | Requirements | Expanded: preservation / structure | Condensed: preservation / structure |
| --- | ---: | --- | --- |
| 4.1 | 69 | 31 (44.9%) / 31 (44.9%) | 31 (44.9%) / 26 (37.7%) |
| 4.2 | 72 | 33 (45.8%) / 33 (45.8%) | 33 (45.8%) / 28 (38.9%) |
| 4.3 | 74 | 34 (45.9%) / 34 (45.9%) | 34 (45.9%) / 29 (39.2%) |
| 4.4 | 83 | 34 (41.0%) / 34 (41.0%) | 34 (41.0%) / 29 (34.9%) |
| 4.5 | 91 | 44 (48.4%) / 44 (48.4%) | 44 (48.4%) / 35 (38.5%) |

**Reserved declarations:** 333/333 explicit source rows match RDF Number/Type; 0 missing, 0 different.
**Human review:** 0 pending items; source completeness accepted.

**Source audit:** 344 sections; 1134 authored assertion entries; 0 sections flagged `needs-review`.
**Assertion test inventory:** 146 with targeted cases, 135 with partial test evidence, 853 without a targeted case. These are test-presence categories, not passing-coverage scores.

For VCF 4.5, 9 condensed structural witnesses fail; 47 requirements lack tests.
<!-- results:end -->

The source audit added R51–R94 after identifying omitted capabilities. Scores
therefore use a larger register than the earlier 50-requirement assessment.
Added cases cover FILTER declarations and record-to-definition links, FORMAT
attributes, ALT declarations, contig metadata, pedigree roles/URLs, sites-only
files, cardinality/types, escaped strings, SAMPLE/META metadata and sample FT
filter states/codes. Missing
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

**What the condensed structure column measures.** All 29 failing witnesses are
condensed-profile structure queries over per-sample FORMAT data (R18–R21 in every
version, plus R27–R30 in 4.5, and R60). The condensed profile deliberately stores
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
