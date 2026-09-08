# Methodological coverage assessment: VCF 4.1–4.5

This specification-derived assessment uses a reproducible requirement-traceability
workflow. The original
[104-construct assessment](../curated/README.md) uses a separate rubric.
Start with [the current report](generated/report.md); read
[DECISIONS.md](DECISIONS.md) when reviewing or changing judgments.

## Current findings and review status

The current first assessment records **491 retained requirements and 133 with
full supporting evidence** across their applicable versions. Of those 133,
122 concern conditional Number/Type declarations, five validity/advisory rules,
two allele-meaning representations and four source-byte predicates.
All **333 extracted reserved Number/Type rows match** their vocabulary artifacts;
330 of those rows detect both tested declaration mutations. These counts do not
establish an overall semantic-coverage percentage.

First-review triage, mapping, alignment suggestions and changelog dispositions
are recorded. **193 reverse source transitions and an exhaustive source audit
remain unfinished**, so `check --require-reviewed` still exits 2. Partial evidence
is an assessed result, not proof that a concept is impossible to represent.

The repository owner agreed to six policies: maintained source pins, INFO/FORMAT
key identity, separate declaration/meaning credit, preservation of requirement
strength, all-missing PSL interpretation and provisional FORMAT-body precedence.
Their qualification is retained: **complex semantic adequacy requires judgment**.
All 125 reserved-field meaning contracts currently receive only partial evidence.
Generic storage, a matching description or a class name does not prove complete
biological or quantitative meaning.

The active [decisions.json](decisions.json) preserves authors, original judgments,
review history and scoped owner confirmations. Policy agreement is not approval
of every mapping or of corpus completeness. Codex implemented the workflow and
performed its first review; this is not independent human validation of the code.

## Reproducible findings

1. **Custom structured headers:** the full validator accepts absent IDs and
   duplicate IDs under the same CUSTOM prefix; ordinary controls remain accepted.
2. **Numeric modification declarations:** M123A, DPM123A and ADM123A accept
   Number=999 or Type=String instead of the prescribed M/Float or M/Integer pairs.
3. **PS/PSL lists:** PS=100 with PSL=.,. is rejected in expanded and condensed
   4.4/4.5 controls, contrary to the owner's agreed missing-list interpretation.
4. **Mixed LF/CRLF:** the byte checker rejects mixed terminators. Codex provisionally
   interprets the source's LF-or-CRLF permission as allowing mixtures; the owner
   has not confirmed this specific interpretation. Coverage remains partial.

The FORMAT body/changelog contradiction is retained: the explicit body requires
ID, Number, Type and Description, whereas the historical changelog restricts the
latter three to INFO. The agreed provisional body precedence does not correct the
source contradiction. Full credit is scoped to individual reviewed conditions
and prerequisites, never arbitrary-file conformance.

## Run it

From the repository root, using Python 3.10 or newer:

```sh
python3 -m venv .venv                   # only if no environment exists
.venv/bin/python -m pip install -r requirements-dev.txt
npm run methodological:build             # regenerate primary reports, offline
npm run methodological:check             # recompute and compare; writes nothing
npm run methodological:test              # focused regression tests
```

The Python entry point can also be invoked directly, from any directory:

```sh
.venv/bin/python coverage/methodological/workflow.py build
.venv/bin/python coverage/methodological/workflow.py check --require-reviewed
```

`--require-reviewed` is an optional publication gate. Exit codes are:

| Code | Meaning |
| --- | --- |
| 0 | Artifacts reproduce and evidence references are consistent. Pending assessments are allowed by default. |
| 1 | Invalid/missing input, stale generated output, changed/dangling reviewed evidence, or a version-mismatched claim. |
| 2 | Inputs/artifacts are sound, but `--require-reviewed` found unresolved assessment work. |

The strict gate is about completing the recorded assessment, not demonstrating
100% coverage: an explicitly assessed gap can remain in a reviewed report.
It also cannot certify that the extractor found every requirement.

Source downloads are separate and never part of ordinary builds or CI:

```sh
npm run methodological:fetch
```

This command requires `curl` and network access. It downloads **all five** sources
and verifies every hash before replacing any snapshot. It does not bless upstream
changes. If a URL no longer serves the pinned bytes, restore the committed copy
or supply an immutable `downloadUrl` in the lock that serves those same bytes.
Do not refresh hashes merely to make a failure go away.

## Source provenance

[sources.lock.json](sources.lock.json) records the authoritative URLs, local paths,
and SHA-256 values. The five LaTeX snapshots are committed under [sources](sources/)
so reproduction is offline. They were retrieved from
[samtools/hts-specs](https://github.com/samtools/hts-specs) on 8 September 2026.
They are upstream specification source material; their contents and attribution
are preserved.

The registry loader is reused from `scripts/version_registry.py`. One correction
to the plans: the current version registry supplies the **source locations**, but
the hashes actually live in `ontology/versions/vcf-4.x-reserved.json` for 4.1–4.4
and the SHA-256 comment in `ontology/vcf-core-reserved-keys.ttl` for 4.5. Every run
checks that the local lock and those existing artifacts agree. The pins are to
the current maintained specification revisions, including errata, not necessarily
the original historical release-day texts.

[generated/provenance.json](generated/provenance.json) fingerprints every input
used to construct the report, including this workflow's code, the decision
ledger, the ontology, shapes, and curated inventory. There are no generated
timestamps, absolute checkout paths, random identifiers, or network-dependent
results. RDF blank nodes are canonicalized before evidence fingerprints are
computed. The direct RDF dependency is pinned in [requirements.txt](requirements.txt).

## How the denominator is derived

1. **Extract separately for each pinned version.** Read section headings and
   preserve one-based source line ranges. Exclude the preamble and the BCF section.
   Parse the later changelog separately, including mixed VCF/BCF items for review.
2. **Run two prose sweeps.** The modal vocabulary includes obligations,
   prohibitions, advice, and “reserved”. A second pattern set catches selected
   declarative wording, including numerically sorted positions and fixed-field
   annotations. A statement can have both discovery tags; it is emitted once.
   Strength precedence is prohibition, obligation, advisory, declarative. A
   compound sentence gets one provisional strength and still needs triage.
3. **Extract explicit Number/Type definitions independently.** Read reserved INFO
   and genotype longtables and INFO/FORMAT declarations in the two structural
   variant definition sections, directly from the source. Definitions in example
   blocks are not treated as normative table rows. Earlier prose-only definitions
   remain prose; the extractor does not invent Number/Type values for them.
4. **Group exact normalized text within section and item context.** Typography
   and whitespace are normalized; numbers, field identifiers, negation, and
   literal VCF versions are retained. `REQ-…` IDs are content-derived and independent
   of source line offsets. Repeated occurrences retain separate occurrence IDs.
5. **Propose, never accept, fuzzy alignment.** Same-section and same-context
   pairs use text similarity (ratio ≥ 0.72 and token overlap ≥ 0.4), or the same
   reserved field identity. Ratios ≥ 0.92 are marked high confidence; all still
   require review. Accepted merges preserve the reviewer-selected target ID and
   record source IDs as aliases. Fuzzy matches may be rejected, and reviewers may
   align relocated requirements even when the heuristic did not suggest them.
6. **Publish the extraction's blind spots.** `proseAudit` retains all processed
   prose blocks, their raw TeX, anchors, and selected candidates, including blocks
   that matched neither sweep. `skippedLines` and `excludedRegions` expose examples,
   tables, comments, the preamble, and BCF. Source line ranges for sentences refer
   to their containing block; they are not falsely precise sentence offsets.

The bounded parser does not expand TeX macros, interpret equations, recover
requirements from figures, or prove the completeness of its declarative patterns.
Inline TeX cleaning is for discovery and readability; the pinned raw source is
authoritative. Parent item context is shallow, so nested lists and cross-paragraph
references especially need inspection. Manual additions and splits are recorded
with explicit anchors, reviewer, and rationale; they remain distinguishable from
mechanically discovered entries.

With the initial sources and method, the obligation/prohibition counts are
27/27/64/105/115 for 4.1–4.5, matching the multi-version plan. The 4.5 modal sweep
finds 185 candidates: 115 obligation/prohibition and 70 advisory. The single-version
plan's 113/72 split was explicitly exploratory. No count is forced in extraction
to reproduce that estimate. Reserved definitions and the broader declarative sweep
increase the full candidate count; those are a different measure.

## Evidence and coverage arithmetic

The catalogue discovers named SHACL shapes, individual SPARQL rules (not just
their parent shape), curated construct entries, declared ontology terms, named
Python decoded-check error codes, and the serialization checker. Token overlap
and reserved-family/version matches produce shortlists, not coverage credit.
The seven plan examples are also exposed as explicit seed suggestions.

Reviewed mappings are many-to-many. For each requirement and version, a full
mapping can supply the required axis:

| Requirement kind | Required evidence role |
| --- | --- |
| `representational` | `representation`: an inventory entry or declared ontology term |
| `validity` | `enforcement`: a shape, individual rule, or decoded check |
| `serialization` | `serialization`: the source-byte checker, with a reason identifying the relevant check |
| `processing`, `bcf` | Explicit scope exclusion; these never earn vocabulary coverage credit |

A `partial` evidence assessment is retained but never counted as full. A mapping
only contributes after `mappingComplete: true`. Union-level discharge requires
the needed role in **every applicable version**. Per-version rollups use the same
reviewed union, rather than five unrelated denominators. Tables report counts,
including normative wording density; no per-version coverage percentages exist.

The workflow also performs a judgment-free, literal comparison of independently
extracted reserved-field Number/Type rows with the version's reserved-key artifact.
`reserved-definition-comparison.json` retains every expected and actual definition
and reports exact, missing, and different rows. This is a narrow measurement of
metadata agreement, including repeated source rows, not a substitute for assessing
the full requirement or proving that a value validator enforces it. Disagreements
are findings to inspect; they do not cause the measurement itself to fail.

Every evidence link pins its fingerprint. Deleting a target, changing a query
while retaining its name, or editing a cited inventory entry invalidates the
review until it is reassessed. SHACL scopes recognize positive `fileFormat` gates
and shared ungated rules; uncertain control flow has unknown scope. Unknown scopes
require an explicit `scopeReason`. A known 4.5-only rule cannot be credited to 4.3.
The curated inventory is scoped to 4.5. Ontology evidence includes shared terms
and the earlier `ontology/versions/*.ttl` reserved definitions, whose `reservedIn`
values determine scope. Their often generic descriptions establish metadata
presence, not complete field meaning. The byte inspector has no version gate;
its individual predicates can be assessed against source clauses in any version.
The continued review credits four byte predicates only in 4.3–4.5, where those
clauses were located and controls were executed.

An ungated shape's presence says nothing by itself about whether it actually fires
on a graph. Review targets, property prerequisites, decoded/raw carriers, positive
fixtures, and negative probes. The workflow checks traceability references, not
the truth of a human semantic verdict. Evidence fingerprints cover the cited
shape/constraint's outgoing blank-node closure, inventory object, term definition,
or complete Python checker file. Other changes anywhere in the assessed artifacts
also invalidate the generated provenance; inspect that diff before regenerating.

`unmappedVersions` and `dischargeStatus` expose partial version coverage. The plan's
finding buckets describe the **inventory and enforcement axes** once mapping is
assessed: `enforced, not inventoried`, `inventoried, not enforced`, `neither`,
`out of scope`, and `version-mismatched`. `inventoried and enforced` records the
intersection. `neither` is not automatically a missing model term: a direct term
mapping may establish representation without a curated inventory entry. Excluded,
duplicate, split, non-requirement, and unassessed entries remain visible and are
not silently folded into the requirement denominator.

## Version differences and changelog cross-check

`generated/audit/version-diff.json` records `newlyObserved`, `noLongerObserved`, and reviewed
rewordings for each adjacent version pair. These are observations about source
text after alignment. They are **not** automatic assertions of introduction or
withdrawal. `END` and `SVTYPE` deprecation remains separate from removal; optional
reviewed lifecycle notes can record either with a rationale.

The changelog is independently extracted from all three sources that contain one
(4.3, 4.4, 4.5). Its item count includes repeated historical changes, errata, and
BCF items, not that many distinct semantic changes. The review must link each
relevant item to corpus entries or explicitly classify/explain it. Links that
do not appear in the corresponding derived diff require a `disagreementReason`.
In the other direction, each unlinked diff observation is published and can get
an explicit transition note (for example, a specification changelog omission).
An unresolved item is never silently reconciled by similarity.

## Files and repository integration

| Location | Role |
| --- | --- |
| `decisions.json` | Sole active reviewer ledger; authored input, never regenerated. |
| `sources.lock.json`, `sources/` | Hash-pinned authoritative source copies for offline reproduction. |
| `extract.py`, `evidence.py`, `workflow.py` | Extraction, evidence catalogue and assessment CLI. |
| `test_workflow.py` | Regression tests, also loaded by the repository suite. |
| `review_probes.py`, `review_profile_probes.py` | Executable isolated and full-validator experiments. |
| `probes/rules.json`, `probes/profiles.json` | Recorded experiment observations, including known failures. |
| `generated/report.md`, `generated/summary.json` | Primary human/machine results. |
| `generated/corpus.json`, `generated/traceability.json` | Source register, anchors, mappings and version credit. |
| `generated/evidence-catalogue.json` | Addressable evidence, scope and fingerprints. |
| `generated/reserved-definition-comparison.json` | Literal source/artifact Number/Type comparison. |
| `generated/changelog-reconciliation.json` | Changelog decisions and unresolved reverse observations. |
| `generated/provenance.json` | Exact source and input hashes. |

The seven additional audit outputs are generated **only on request**:

```sh
npm run methodological:audit
npm run methodological:check -- --audit
```

`generated/audit/` contains `extracted.json` (including unselected prose),
`alignment-suggestions.json`, `version-diff.json`, `review-queue.json`,
`seed-checks.json`, `seed-review.md` and `reviewed-decisions.md`. These are optional,
reproducible reviewer aids and are ignored by Git. Rebuild them after changing
inputs; ordinary checks cover the primary outputs. `npm run clean` removes them.
No judgment or unique source data lives only in that directory.

`npm run coverage:report` checks these primary outputs and includes the separate
requirements summary in the curated report. Workflow inputs and recorded probes
are fingerprinted by the validation gate and covered by CI. The two assessments
retain separate denominators and their conclusions are not changed by relocation.

`npm run methodological:review-probes` executes and compares both recorded experiments.
It takes several minutes and reproduces known failures; that is not conformance
success. The isolated observations include 24 byte cases and 333 declaration rows;
the full-validator experiment contains 14 complete-fixture controls.
After a deliberate validator change, rerun the scripts without `--check`, inspect
the observation changes, reassess affected judgments and rebuild. Do not update
fingerprints merely to bypass evidence review.

`npm run validate:force` validates the vocabulary and fixtures as well as this
measurement. Results are recorded in `tests/generated/validation.json`; the
validation stamp fingerprints the successful full run. Green fixture tests do not
close the unfinished source audit.
