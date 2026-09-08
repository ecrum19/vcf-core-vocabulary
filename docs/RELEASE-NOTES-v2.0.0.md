# VCF Core Vocabulary v2.0.0 — release notes

**Draft / unreleased · prepared 7 September 2026 · replaces v1.1.0**

Version 2.0.0 renames the VCF-RDFizer Vocabulary to **VCF Core Vocabulary**, expands
its model from file/header/call containers to queryable VCF 4.5 structures, and
adds executable validation profiles for VCF 4.1–4.5. It repairs the example suite
and makes conversion fidelity and validation claims testable. The namespace and
several modelling conventions change, so migration requires more than updating
a version string.

These notes consolidate both coverage assessments, the current working tree at
HEAD `af523c6`, and the **actual v1.1.0 tag**, commit `8994fcb`. All intervening
work is presented as one v2.0.0 release; intermediate development version labels
are not separate releases. The vocabulary and the VCF-RDFizer converter retain
independent version lines. The license remains CC BY 4.0.

## What was already in v1.1.0

The tagged [v1.1.0 changelog](https://github.com/ecrum19/vcf-core-vocabulary/blob/8994fcb6ce3150235c9c75bd1f149aa0af0e8998/CHANGELOG.md)
already introduced condensed cohorts, ordered samples, FORMAT vectors and their
basic SHACL rules. It also fixed missing-value handling for `ALT=.` and record
IDs. Version 2.0.0 retains and strengthens those capabilities; it does not
introduce condensed representation or claim that earlier fix as new.

Some assessment passages describe other development snapshots also labelled
1.1.0. In particular, the tag defines `ExpandedRepresentation`, while the rename
work refers to `DenseRepresentation`. The compatibility consequence is recorded
under release readiness below.

## Model changes and their rationale

### Namespace and ontology corrections

The new namespace is `https://w3id.org/vcf-core/vocab#`, conventionally `vcfc:`.
The neutral name identifies a shared semantic target usable by multiple
converters. Source filenames, mappings, documentation, package metadata and
citation metadata now use VCF Core.

| Change | Why it was made / consumer impact |
| --- | --- |
| The five VCF Type values, representation profiles and vector encoding are named individuals of their respective value-set classes. | They are used as property values. This makes their intended role explicit; consumers querying them as subclasses must update. |
| Reusable `FieldDefinition` resources no longer imply header-line occurrences. Concrete INFO/FORMAT/FILTER/ALT header classes also inherit their definition type. | Otherwise imported reserved definitions acquired file-line obligations and failed validation. Explicitly type actual declarations as the appropriate header-line class; `declaredOnLine` can link a separate definition to its occurrence. |
| Removed the erroneous `rdf:Resource` domain from the four `fieldValue*` properties; added the record domain to `chromosome`. | Corrects domain modelling without restricting values to one field-value resource class. |
| IRI-template placeholder `{recordId}` becomes `{recordKey}`. | Separates the generated row identifier from the VCF ID column, whose value can be missing or contain several IDs. The `recordId` property remains. |
| Replaced the incorrect `faldo:Reference` alignment with a VRS sequence-reference alignment and a reference to `faldo:reference`. | Distinguishes a reference resource from FALDO's linking property. |

### A modular, queryable VCF model

Five normative modules now share the namespace. A generated bundle supports
validators and the companion site; consumers should load the bundle or resolve
all module imports.

| Module | Added capability and purpose |
| --- | --- |
| [Core](../ontology/vcf-core-vocabulary.ttl) | Structured/unstructured metadata, individual header attributes, `#CHROM`, assembly/META/SAMPLE/PEDIGREE/pedigreeDB forms; explicit header, record and field order; symbolic/fixed Number arity; raw/decoded lexical carriers; parsed IDs and FILTER/FT codes/statuses. These expose information previously embedded only in strings. |
| [Alleles and values](../ontology/vcf-core-alleles.ttl) | Ordered REF/ALT resources, allele kinds and indexed value items linked to alleles, genotype indices, GT positions or modifications. Explicit indices preserve VCF order despite RDF's unordered triples. |
| [Genotypes](../ontology/vcf-core-genotypes.ttl) | Ordered allele calls, no-calls, ploidy, per-allele preceding phase indicators, mixed phasing, phase sets and local-allele memberships. These support queries beyond a raw GT string. |
| [Structural variation](../ontology/vcf-core-sv.ttl) | Symbolic ALT types, SVCLAIM, breakend orientations/mates/events, confidence intervals, repeat sequences/units, copy number, sample reference blocks and base modifications. Resources retain VCF-specific meaning while linking to external models. |
| [Reserved keys](../ontology/vcf-core-reserved-keys.ttl) | Generated INFO/FORMAT definitions, including base-modification families and aliases, with specification provenance. This replaces scattered or manually maintained declarations. |

`LocalAlleleMembership` carries each sample's local order; the shared ALT retains
its record-global index. The preliminary `localAlleleIndex` property directly
on ALT is deprecated. Similarly, `ReferenceBlock` is a **sample interval linked
to an ALT**, not an ALT subclass: two samples can have different FORMAT LEN
extents at the same record. These corrections affect adopters of preliminary
v2 drafts, not constructs present in the v1.1.0 tag.

Both sample profiles remain supported. Explicit `forSample` links and optional
raw sample-block/field carriers improve sample identity and source recovery.
Condensed vectors retain one tab-separated value per sample; missing values keep
their positions. Accessing individual vector cells still requires decoding or
materialized expansion. No cohort-scale performance improvement is claimed from
the small examples.

FALDO supplies locations and strands; SO, GENO, VRS and ChEBI provide selected
alignments. Existing HERO and other integration hooks remain. These links do not
replace VCF syntax resources with assertions of biological equivalence or prove
all external ontology combinations consistent.

### Reserved-key completeness and provenance

The registry contains **122 definition resources: 51 INFO and 71 FORMAT**, including
three pattern families and 30 alias links. The generator consumes 21 general INFO,
31 SV INFO, 63 general FORMAT and eight SV FORMAT source occurrences; shared END
is deduplicated. Pattern families use `keyPattern` rather than an invalid literal
field ID. Ten canonical modification definitions carry ChEBI matches.

Generation records the official source URL and SHA-256
`37f13e0d2e8e741ea8505b0342b6e6034637a1f476eeb3af1b8acc25d70246c5`.
Regeneration from that source was byte-identical during this release-note review.
This demonstrates reproducibility; generator-authored annotations need separate
checks. In particular, END deprecation was corrected to **VCF 4.5**, while
SVTYPE remains **VCF 4.4**, with regression assertions for both. The consulted
[VCF 4.5 specification](https://samtools.github.io/hts-specs/VCFv4.5.pdf) is the
25 February 2026 printing, `e821e4f`.

## Validation changes

### Shared rules and version overlays

Validation now combines three common SHACL files with five version overlays:
core structure, cross-resource rules, raw/parsed consistency, and version-specific
constraints. Overlays follow the owning file's `fileFormat`, so several versions
can coexist. Optional `VCF41File`–`VCF45File` classes add explicit version gates.
See [profile composition](../shacl/README.md).

Historical registries and record-bearing VCF 4.1–4.4 examples prevent current rules
from being applied indiscriminately to older files. For example, a multiallelic
4.3 CIPOS pair passes its historical rule but fails the modern per-ALT tuple rule.
Number-code availability and CN/SVLEN declarations also vary by version. Legacy
snapshots retain source hashes and explicit declarations; unspecified historical
prose is not converted into invented Number/Type requirements.

### Defects now detected

The audits demonstrated that apparently clean SHACL results could hide malformed
data. The repaired constraints and decoded checks cover:

- Missing fileformat/column headers, conflicting versions or structured attributes,
  invalid Number codes and incompatible reserved declarations.
- Negative positions, invalid custom Float/GT lexical forms, malformed missing
  tokens, declared value types and numeric limits. Valid special floats remain
  accepted. Integer-derived XSD datatypes are accepted with numeric bounds;
  decimal indices are rejected.
- Raw/parsed REF, ALT and value disagreement; fixed and A/R/G/LA/LR/LG/P counts;
  absent SV tuple items; reversed confidence intervals; sample/vector dimensions.
- Genotype ploidy, allele references and phase indicators; local membership/order;
  populated PS/PSL conflicts; parsed IDs/filter codes; repeat aggregates and
  per-sample reference-block extent/overlap.

Two ineffective SPARQL branches were repaired after isolated mutation tests
showed that conflicting values still passed. Malformed structural integers now
produce decoded-validation errors rather than a traceback.

The [Python semantic layer](../tests/semantic_validation.py) explicitly supplements
SHACL: it decodes vectors, checks arbitrary-ploidy G/LG cardinalities and Number=M
counts on explicit alleles, and handles additional range, repeat and block rules.
SHACL G/LG formulas cover ploidy 1–8. Running only the portable shapes therefore
does not provide the complete runner's guarantees.

Recommendation warnings are distinct from violations. Supplied graphs may retain
warnings unless `--warnings-as-errors` is requested; all maintained complete
fixtures must pass with **zero warnings** in CI.

## Examples, conversion evidence and documentation

Every advertised Turtle example is now complete. Header-only and minimal-record
graphs pass separately and together; the former represents a valid zero-record
file. Expanded, condensed and paper graphs have complete metadata, declarations,
column links and indices. The large source VCF's space-separated sample cells
were corrected to tabs and its RDF regenerated. The illustrative CONSTRUCT
output also validates, although the template remains a demonstration rather than
a production converter.

The reorganized [example guide](../examples/README.md) provides:

- `examples/core/`: a small quickstart, complete headers, one-record and three-record
  examples, with VCF, Turtle and N-Triples where applicable.
- `examples/profiles/`: three SNPs and eight actual 1000 Genomes sample columns.
- `examples/vcf-versions/`: 4.1–4.4 compatibility fixtures and 4.5 examples of linked
  modifications, mixed triploid phasing, local alleles, breakends, repeats and gVCF.
- `examples/queries/`: queries with exact answers recorded in the manifest.

Modifications are reachable from actual sample FORMAT items rather than orphaned
resources. Queries demonstrate, for example, fraction 0.9/depth 20, the three
phase indicators `|`, `/`, `|`, reciprocal mates, and sample blocks ending at
704 and 709 from respective lengths 5 and 10.

The independent [example checker](../tests/check_examples.py) reconstructs logical
VCF lines from saved RDF, checks vocabulary declarations/property kinds and runs
the queries. Its **16 RDF/source pairs** include both serializations of the expanded
example and both paper profiles. The bounded fixture materializer and checker
provide complementary evidence; they do not establish arbitrary byte-for-byte
conversion fidelity.

The final example refresh replaces generic sample calls with small source
subsets: three HaplotypeCaller records from the supplied `test-larger.vcf.gz`
retain GT:AD:DP:GQ:PL, while the condensed example retains 24 phased GT calls
from eight 1000 Genomes samples. It preserves their actual VCF versions (4.2
and 4.1 respectively) and reference builds, and recalculates cohort AC/AF/AN
after sample selection. The minimal example keeps one real GT:AD:DP call.
[Provenance](../examples/provenance.json) records hashes and reductions; a ninth
query explicitly decodes a named sample's condensed GT cell. Advanced feature
fixtures and paper evidence remain synthetic teaching examples.

The paper evidence preserves all six FORMAT cells in both profiles and returns
`SAMPLE1`, `42` for the depth query. Complete metadata changes its graph sizes to
**172 expanded / 149 condensed triples**. These tiny fixtures establish behaviour,
not a storage or throughput benchmark. Author notes distinguish repaired working
examples from earlier manuscript snapshots.
The new [SWAT4HCLS 2027 manuscript draft](../SWAT4HCLS_2027/README.md) explains the
model and its implementation context; citation and acknowledgement files were
updated alongside the rename. The manuscript remains a draft, not publication
evidence for the release.

## Coverage metric assessment

Coverage has three different meanings here: **a construct can be represented**,
**its validity is checked**, and **a fixture exercises it**. None implies the
other two automatically.

The older assessment's historical 106-construct inventory reported:

| Logical-model area | Constructs | Full | Partial | Absent |
| --- | ---: | ---: | ---: | ---: |
| File/header structure | 20 | 20 | 0 | 0 |
| Declaration attributes | 8 | 8 | 0 | 0 |
| Type/arity value sets | 14 | 14 | 0 | 0 |
| Lexical/encoding rules | 9 | 5 | 1 | 3 |
| Fixed fields/alleles | 18 | 12 | 3 | 3 |
| FORMAT/genotypes | 21 | 18 | 2 | 1 |
| SV/repeats/gVCF | 16 | 15 | 1 | 0 |
| **Total at that review point** | **106** | **92** | **7** | **7** |

Thus **92/106 = 86.8%**, rounded to **87%**; arbitrary half-credit for partials
produces **90.1%**. Adding 122 registry resources gives **214/228 = 93.9%**, rounded
to **94%**. These are historical representation scores, not current validation
percentages. Registry weighting also changes the denominator substantially.

The original approximately 20% estimate had a different, unretained denominator
mixing logical syntax, serialization and BCF rules; it is not a sound v1.1.0
baseline for measuring improvement. The later 106-item assessment survives as
category totals and gap lists, not a complete, executable item-by-item scoring
ledger. Its categories also mix modelling and enforcement. It cannot support a
fresh percentage merely by subtracting repaired findings.

Current evidence is more usefully stated with explicit denominators:

| Axis | Current evidence | Interpretation |
| --- | --- | --- |
| Header forms | 11/11 forms in the assessment inventory, plus `#CHROM` | Typed model coverage; not every possible header constraint. |
| Type and symbolic Number values | 5/5 Types; 9/9 symbolic codes | Value-set coverage, supplemented by version-specific checks. |
| Reserved definitions | 122 resources; source regeneration identical | Complete extraction of the targeted tables/declarations, including families and aliases. |
| Ontology/shape inventory | OCG: 445 declared terms, 380 relationships; eight SHACL files, 123 node shapes, 75 SPARQL constraints | Implementation size, not a percentage of the specification. |
| Complete maintained RDF fixtures | 19/19 passed before the final real-call refresh | Historical full-suite result; the refresh received focused checks only. |
| Independent tests and demonstrations | 35 regression tests; 16 source pairs; nine exact-answer queries | The 16 source pairs and all nine queries passed after the refresh; the vector regression was rerun separately. |

The [coverage checklist](../coverage/curated/README.md) now maps specification areas to terms,
rules and probes. A defensible future percentage requires a versioned atomic
requirement inventory, explicit full/partial criteria and linked positive/negative
tests for every item. **Full VCF 4.5 conformance remains unclaimed.**

## Tooling and reproducible validation

Generators/publication helpers live in `scripts/`; executable validators and
regressions live in `tests/`. The generated ontology bundle and site are excluded
from source control. OCG 1.3.0 remains the documentation generator, now building a
unified modular reference and an explorer with quickstart/advanced examples,
source VCFs, version profiles, queries and expected answers.

`npm run ocg:check` now combines the checks above with the original negative
control and OCG configuration validation. This replaces v1.1.0's OCG-only package
command; its changelog separately records earlier targeted SHACL checks.
PR CI now runs the suite, and the Pages workflow runs it before building and
publishing. CI provisions Node 24 and Python 3.12 with pySHACL 0.30.1.

```sh
npm ci
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
npm run ocg:check
npm run ocg:build
# Supplied RDF; use the full runner to load all required layers:
.venv/bin/python tests/validate_shacl.py input.ttl --warnings-as-errors
```

The release-note review reran the check and local build using Node 24.16.0,
Python 3.14.2, pySHACL 0.30.1 and RDFLib 7.6.0. **Both passed.** Fixture summaries are in
[validation-results.json](../tests/generated/validation.json); the
[paper verifier's JSON](../coverage/paper/generated/verification.json) records its
narrower Node assertions. A passing local run does not assert that hosted CI or
publication has occurred.

For the later real-call refresh, the full suite was deliberately not rerun.
Focused checks passed: 31 selected SHACL shapes on the merged changed graphs
(zero violations/warnings), decoded validation, Turtle/N-Triples equivalence,
source-call preservation, all 16 source-pair and nine query checks, and the
truncated-vector regression. The obsolete one-off capture has been removed; current source reconstruction
and query checks are reproducible with `npm run validate:examples`, and full
fixture results with `npm run validate:force`.

## Migrating from v1.1.0

1. Replace the namespace/prefix in producers, RDF, queries and shape imports.
   `ExpandedRepresentation` in the tag retains its local name. For older draft
   `DenseRepresentation` data, use `vcfc:ExpandedRepresentation`.
2. Update class-based queries for Type/profile/encoding values to their individual
   types. Explicitly distinguish reusable definitions from file header lines.
3. Use `{recordKey}` for generated row identity, preserve actual source IDs, and
   supply the metadata/order/sample links required by the stronger shapes.
4. Load the full ontology and validation layers. Validate representative converter
   output, not just the supplied examples; the fixture materializer is not a
   substitute for converter integration tests.

The [migration utility](../scripts/migrate-namespace.mjs) supplies mechanical rewrite
and bridge-generation operations. Run it on a reviewable copy and inspect the
result: string substitution alone cannot implement these modelling changes.
The [legacy document](../legacy/legacy-vcf-rdfizer.ttl) supplies deprecation/replacement
links and equivalence or identity mappings, subject to the gap below. It does
not make old graphs automatically satisfy the new constraints.

## Remaining limits and release readiness

- VCF 4.0 has no overlay and is rejected as unsupported by the complete runner.
  The 4.1–4.5 profiles do not prove exhaustive historical-version validation.
- Complex breakpoint-event reconstruction, all repeat-list combinations,
  reference-aware padding/sequence interpretation and modifications inside
  reference blocks remain incompletely validated. BCF byte layout, UTF-8/BOM
  and line-ending preservation are outside the logical recovery guarantee.
- No full OWL consistency proof, production parser conformance run or cohort-scale
  benchmark is supplied. External alignments and passing example tests must not
  be promoted into those claims.
- **Resolve the legacy bridge against the actual tag before release.** The tag
  has 93 typed terms excluding the ontology IRI; the bridge has 95. It omits
  `vcfr:ExpandedRepresentation`, while including `DenseRepresentation`, `forSample`
  and `sampleDataRaw` from a different development snapshot. Add the missing
  identity mapping and check every tagged term before claiming complete legacy
  compatibility; reconcile the corresponding historical wording.
- **Complete publication metadata and routing.** The w3id configurations still
  contain `REPLACE-ME` host targets. They describe intended new/retired-namespace
  behaviour, not verified live resolution. Pin the final release commit/tag,
  supply its release date and any archival DOI, resolve the manuscript citation
  placeholder, and verify published assets/content negotiation before announcing
  release availability.

The current [coverage workspace](../coverage/README.md) consolidates the maintained
assessments, reviewer decisions and reproducible evidence. The earlier one-off
notes have been removed. Their obsolete statements that END was deprecated in
4.4, that reference blocks subclass ALT, or that parsed ID/filter resources remain
absent do not describe the current implementation. Use the retained source pins,
active inventories and executable reports when preparing the release archive.
