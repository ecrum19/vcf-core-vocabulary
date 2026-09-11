# VCF Core Vocabulary v2.1.1 — release notes

**Prepared 11 September 2026 · changes since 2.1.0**

A patch release: **no vocabulary terms change**, so nothing a consumer queries or validates
against moves. It records the completed review of the
specification-derived coverage assessment, the tests that review asked for, and the
converter support those tests needed. The `https://w3id.org/vcf-core/vocab#` namespace,
both sample representation profiles and every existing term IRI are unchanged. These notes
describe the repository version; they do not assert that a tag or hosted release has been
published.

## Ontology changes

**None.** No term was added, removed, renamed or redefined. The module version IRIs and
`owl:versionInfo` values move to 2.1.1 so a merged graph does not mix release versions;
reserved registries continue to carry their **VCF specification** versions.

## The coverage assessment is reviewed and accepted

The specification-derived assessment in [coverage/methodology/](../coverage/methodology/)
now carries a recorded human decision for all 94 requirements and for the source audit, so
`npm run methodology:check -- --require-reviewed` exits 0 for the first time. Each decision
names what was checked and what limitation was accepted; they are in
[review.json](../coverage/methodology/inputs/review.json) and the reasoning is in the
[review record](../coverage/methodology/REVIEW-REPORT.md).

Evidence grew from 189 to **210 cases**. Demonstrated requirements per version, expanded
profile: 32/69 (4.1), 34/72 (4.2), 35/74 (4.3), 38/83 (4.4), 51/91 (4.5).

| Requirement | What it now demonstrates |
| --- | --- |
| R27, R83 | Local allele indices resolve to global alleles, and a `Number=LR` vector agrees with the `Number=R` vector of the same site, including an empty `LAA` |
| R29, R84, R85 | Base-modification fraction, detecting depth and modified-read depth as distinct quantities; `Number=M` value slots in GT order, on both strands, with unphased duplicates aggregated; alias and numeric ChEBI keys denoting one modification |
| R31, R46, R89 | Repeat units with their counts, RN partitioning the flattened repeat lists across ALT alleles, and tandem-repeat length ratios |
| R79 | Adjacency depth and copy number, per sample and per adjacency |
| R82 | Phase-set ordinals recovering a derivative-chromosome traversal, per-allele phase-set names and qualities, and the mutual exclusion of `PS` and `PSL` within a sample |
| R92 | Complete, partial and circular assembly-contig insertions, with boundaries and direction taken from the ALT bracket notation |

Three cases use records the reviewer authored, because the specification states the rule and
prints no example: `PSQ`, the `PS`/`PSL` exclusion, and the modification alias correspondence.
Each says so in its case note. **R45 (reference blocks) was drafted and deliberately
withdrawn** — the corrections its oracle depends on are disputed upstream, and an expected
answer built on one reading would have to be rewritten if the specification settles on
another.

## Converter changes

[`scripts/vcf_examples.py`](../scripts/vcf_examples.py), the fixture materializer, gained
three capabilities, all using terms that already existed:

- **`Number=M` keys are parsed as a family** — `M`, `DPM` or `ADM` followed by a ChEBI
  identifier or one of the ten documented aliases, then the base letter, with `U` treated as
  `T` and `N` reporting both strands.
- **The unphased-aggregation rule is implemented.** "Unphased allele values are aggregated
  and encoded at the position of the first occurrence" was not applied, so the
  specification's own octoploid example was rejected as a cardinality mismatch. This was a
  defect: the converter mis-encoded a legal VCF.
- **A breakend mate may lie on an assembly contig.** `C[<ctg1>:1[` previously raised; the
  angle-bracketed form now resolves to the same `AssemblyContig` resource an
  angle-bracketed CHROM already used.

**One consumer-visible change in generated data:** base-modification resources are now keyed
by ChEBI identifier and strand as well as by allele slot and offset, so two chemistries on one
base stay distinct. Instance IRIs of the form `…#sample/1/S1/modification/0/0` are now
`…#sample/1/S1/modification/27551/0/0/forward`. Only
`examples/vcf-versions/vcf-4.5/example-vcf45-features.ttl` is affected in this repository.

## Specification errata reported upstream

The review found defects in the pinned VCF text. Four are filed against `samtools/hts-specs`:
[#868](https://github.com/samtools/hts-specs/issues/868) (gVCF separators, LEN values and an
inapplicable MIN_DP row), [#869](https://github.com/samtools/hts-specs/issues/869)
(self-referential and undefined MATEIDs in the contig-insertion tables),
[#870](https://github.com/samtools/hts-specs/issues/870) (Figure 11's `(CAG)4` exponent and
tandem-repeat rows missing the INFO column) and
[#871](https://github.com/samtools/hts-specs/issues/871) (the PSL table's allele indices,
leading indicator and ploidy, and `GT=2/4` in the local-allele table). Others are documented
and not yet reported; the full list is in the review record.

## Documentation

- The reviewer checklist and reviewer guide are folded into a single
  [review record](../coverage/methodology/REVIEW-REPORT.md).
- The [repository README](../README.md) gains a **Things to improve** section: a genotype
  index does not expose the alleles it stands for, which is why local and global genotype
  likelihood vectors cannot be related in the graph; reference blocks are deliberately
  untested pending #868; and full test coverage is stated as a goal not yet reached.
- The [assessment README](../coverage/methodology/README.md) explains in plain terms what the
  untested requirements are — for VCF 4.5, 37 of the 40 are simply unwritten tests, one is
  withheld pending #868, two are single requirements standing for every reserved INFO and
  FORMAT key, and none is untested because the vocabulary cannot express it.

## Upgrading

Nothing to do. No term changed, so no query, SHACL profile or stored graph needs revision.
Regenerating examples with this converter changes base-modification instance IRIs as described
above.
