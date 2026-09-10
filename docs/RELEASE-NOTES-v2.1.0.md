# VCF Core Vocabulary v2.1.0 — release notes

**Prepared 8 September 2026 · changes since the 2.0.0 development baseline**

Version 2.1.0 adds structured representations for VCF boundary cases, extends
their validation and makes the coverage evidence easier to inspect and reproduce.
It retains the `https://w3id.org/vcf-core/vocab#` namespace and both sample
representation profiles. These notes describe the repository version; they do
not assert that a tag or hosted release has been published.

## Ontology changes

| Addition | Purpose and consumer impact |
| --- | --- |
| `AssemblyContig`, `assemblyContigId`, `declaredInAssembly`, `chromAssemblyContig` | A bracketed CHROM token such as `<asm1>` can identify an assembly contig and its `##assembly` source. The original token stays on `chrom`; the contig is distinct from a `##contig` declaration. |
| `PaddingInterpretation` and its rule, side, count and anchor terms | Record the padding interpretation without trimming REF or ALT. Named rules distinguish simple indels, symbolic alleles, the position-one exception, unspecified alleles and cases where padding is undetermined. A shared prefix alone does not establish padding. |
| `FormatKey`, `hasFormatKey` | Expose the record's declared FORMAT sequence using `fieldIndex` and `declaredBy`. Consumers can distinguish an omitted trailing sample field from a key the record never declared. `formatRaw` remains available. |

The additions are in the [core](../ontology/vcf-core-vocabulary.ttl) and
[allele](../ontology/vcf-core-alleles.ttl) modules. Existing term IRIs are retained.
The core version IRI is now `https://w3id.org/vcf-core/vocab/2.1.0`; module,
package, citation and documentation metadata use 2.1.0. Reserved registries
continue to carry their **VCF specification** versions.

## Validation and examples

- New consistency rules check declared FORMAT order, bracketed CHROM agreement
  and padding-rule/anchor consistency. In particular, a bracketed CHROM now
  requires its matching parsed assembly contig and cannot also name a declared
  reference contig.
- The Python semantic layer checks agreement between the existing `rawValue`
  and `decodedValue` carriers for percent-encoded values. These properties
  predate 2.1.0; their decoded consistency check is new.
- [Boundary examples](../examples/vcf-versions/vcf-4.5/example-vcf45-boundaries.ttl)
  and queries demonstrate assembly contigs, padding, missingness, telomeric
  positions, percent encoding and omitted trailing FORMAT fields.
- A separate [source-byte checker](../coverage/vcf45-inventory/check_serialization.py)
  assesses encoding, BOM, control characters and line termination. Paired LF
  and CRLF fixtures have the same logical content. Byte checks do not contribute
  to the logical-model coverage denominator. The mixed-LF/CRLF interpretation
  remains provisional in the methodological review.

Existing 2.0.0 graphs keep their term IRIs, but the additional checks can reject
incomplete or inconsistent representations previously accepted. Producers of
bracketed CHROM records should add the assembly-contig link and identifier.
Producers emitting `rawValue` should also supply its correct `decodedValue`.
Padding consistency checks do not prove that an arbitrary biological variant
was interpreted correctly.

## Coverage assessments

The [coverage directory](../coverage/README.md) separates three purposes:

| Directory | Contents and recorded result |
| --- | --- |
| [`coverage/vcf45-inventory/`](../coverage/vcf45-inventory/README.md) | Curated VCF 4.5 inventory, scripts and reports: **104/104** logical constructs represented under the preservation/structure rubric; **87** have enforcement evidence. (Named `coverage/curated/` at release; renamed for clarity afterwards.) |
| Retired specification-traceability assessment | Historical results below describe the former modal-word workflow. The replacement is documented only in [coverage/methodology/README.md](../coverage/methodology/README.md). |
| [`examples/profile-comparison/`](../examples/profile-comparison/README.md) | Synthetic fixtures, query and reproducible illustration checks for the two sample profiles. (Named `coverage/paper/` at release; moved afterwards, since it illustrates rather than measures.) |

The retired methodological workflow derived its register from hash-pinned specification
sources and records evidence, scope, reviewer judgments and version differences.
The six owner-approved assessment policies remain in the ledger with their
qualifications. Complex semantic coverage requires judgment: matching field
metadata or retaining a raw literal does not establish complete meaning.

At the time of this release, the first assessment had **193 reverse source transitions** and an
exhaustive source audit to complete. Known findings include missing/duplicate
CUSTOM header IDs accepted by the validator, incorrect numeric modification
declarations accepted, and all-missing PSL lists rejected alongside populated PS.
The source's FORMAT body/changelog conflict and mixed-line-ending interpretation
remain explicit. Neither assessment is a claim of exhaustive VCF conformance.

The curated rubric now records preservation, structure and enforcement
independently. Full representation requires preservation **and** structure;
byte-level properties are reported separately. Its score and the methodological
score have different denominators and must not be combined.

## Organization and reproducibility

- The original assessment paths and commands described in this release were later retired. Use the [current methodology documentation](../coverage/methodology/README.md).
- `ontology/versions/registry.json` centralizes specification-version rules used
  by generators, reserved snapshots, file classes and documentation entries.
  This removes duplicated configuration; it does not add another VCF version.
- The README now starts with usage, examples, validation and coverage limits.
  These notes replace the root changelog. Earlier release and namespace history
  remains in the [2.0.0 notes](RELEASE-NOTES-v2.0.0.md), which also link to the
  archived 1.1.0 changelog.

See [coverage reproduction](../coverage/README.md) and the
[maintenance guide](../scripts/README.md) for commands and input/output ownership.

## Verification scope

Targeted checks passed for version metadata, ontology parsing, documentation
links and the README query, along with 32 assessment tests and two cleanup tests.
The 14 recorded full-validator coverage cases were replayed: they retain the
same observations, including eight known validator/specification mismatches.
Their input fingerprints now reflect the 2.1.0 metadata. Coverage reports were
regenerated and checked; assessment decisions and scores are unchanged.

The full repository validation suite is not rerun. Its existing report and
validation stamp retain the provenance of the previous complete run; they are
not relabelled as a new 2.1.0 validation result.
