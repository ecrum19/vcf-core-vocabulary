# Mappings

Three things live here: the alignments `vcf-core` asserts, the third-party
mapping declarations it was compared against, and a template for producing
`vcf-core` RDF.

| Path | Kind | What it is |
| --- | --- | --- |
| [`vcf-core-alignments.sssom.tsv`](vcf-core-alignments.sssom.tsv) | **authored** | the single curated record of every alignment `vcf-core` asserts |
| [`vcf-core-alignments.ttl`](vcf-core-alignments.ttl) | generated | the deployable alignment module, built from that file |
| [`bh25/`](bh25/) | authored | SWAT4HCLS 2025 BioHackathon declarations, recorded verbatim |
| [`FUTURE-MAPPINGS.md`](FUTURE-MAPPINGS.md) | authored | targets surveyed but not asserted, and why |
| [`registry.json`](registry.json) | authored | machine-readable index of the above |
| [`vcf-to-vcf-core-construct.sparql`](vcf-to-vcf-core-construct.sparql) | authored | CONSTRUCT template turning a staging graph into `vcf-core` records |

## How this is organised, and why

**Alignments live outside the core vocabulary.** `vcf-core-alignments.ttl`
declares its own ontology IRI, `owl:imports` the core, and is *not* imported
back. Loading the core commits you to nothing about GA4GH VRS, HERO or GVO;
loading the alignment module opts you in. This is the ordinary bridge-module
pattern — the same reason OBO ships `*-bridge-to-*.owl` separately from the
ontologies it bridges — and it means an alignment can be revised, or rejected,
without touching a released vocabulary.

**SSSOM is the source of truth; Turtle is generated.** Curation happens in
`vcf-core-alignments.sssom.tsv`, because per-mapping confidence, justification
and curator notes are first-class columns there and awkward reification in
Turtle. `npm run mappings:build` renders the module: plain SKOS triples grouped
by target vocabulary, plus `owl:Axiom` blocks carrying the confidence and notes
so a consumer can filter on them without leaving RDF. Edit the TSV, never the
Turtle.

**SKOS, not OWL equivalence.** Every mapping uses `skos:exactMatch`,
`closeMatch`, `broadMatch`, `narrowMatch` or `relatedMatch`. `owl:equivalentClass`
between vocabularies built on different assumptions propagates unintended
inferences into anyone's reasoner; SKOS mapping properties state the
correspondence without merging the models. Even `skos:exactMatch` here means
"interchangeable for retrieval", not "identical in meaning".

**The module is a superset of the core's inline axioms.** 48 alignments are
also asserted inline in `ontology/*.ttl` and reach anyone loading the bundle;
they carry the comment *"Also asserted inline in the vcf-core ontology
modules"*. The build fails if the two ever disagree, so there is no way for a
mapping to exist in one place and be quietly contradicted in the other.
Consolidating them into the module alone would drop alignments from the
released bundle, so it is a 3.0.0 decision, not a cleanup.

## Building and checking

```sh
npm run mappings:build   # regenerate the module, then run every check
npm run mappings:check   # check only; fails if the module is stale
```

The checks are: required SSSOM columns populated; `predicate_id` a SKOS mapping
property; every CURIE prefix declared in the file's own `curie_map`; no
duplicate triples; confidences numeric and within 0..1; ISO 8601 dates; the
superset invariant above; and the generated Turtle parses.
`tests/test_mappings.py` runs the same checks in the regression suite.

## What `vcf-core` aligns to

| Target | Mappings | Note |
| --- | --- | --- |
| **GA4GH VRS 2.0** | 15 | The hub. Every BioHackathon set was curated against VRS, so this spoke is what makes them composable with `vcf-core`. |
| **HERO** | 17 | The only surveyed model with first-class VCF column terms; `hero:vcfChrom`, `vcfPos`, `vcfRef`, `vcfAlt`, `vcfQual` are near one-to-one with `vcf-core`'s. |
| **GVO** | 39 | Models VCF's columns as properties and splits normalised from VCF-as-written values with a `_vcf` suffix — the same distinction `vcf-core` draws. Its class hierarchy is the VCF symbolic-ALT vocabulary. |
| **GFVO** | 14 | Designed to cover VCF; the best available match for the reserved-key registry (`AC`, `AF`, `AN`, `DP`, `NS`, `MQ`, `BQ`, `GQ`). |
| **Med2RDF** | 3 | `reference_allele_vcf` and `alternative_allele_vcf` are defined by Med2RDF as the VCF-specification forms. |
| SO, GENO, ChEBI, FALDO | 35 | Pre-existing; asserted inline in the ontology modules. |

### A note on VRS versions

`vcf-core` targets **VRS 2.0**, prefix `vrs:`. The BioHackathon sheets were
curated against **VRS 1.2/1.3**, prefix `vrs1:`, and nine of the classes they
mapped to — `Genotype`, `Haplotype`, `SequenceInterval`, `ChromosomeLocation`,
`Text`, `Residue`, `Feature`, `Gene`, `UtilityVariation` — were removed in 2.0.
The two prefixes are kept distinct because collapsing them would silently
assert that those mappings still resolve.

### What `vcf-core` adds to the BioHackathon result

The curators marked **47** terms `sssom:NoTermFound` against GA4GH VRS. Eight of
them now have a `vcf-core` counterpart:

| Term | no VRS match | `vcf-core` |
| --- | --- | --- |
| `hero:VCFFile` | file-level, out of VRS scope | `vcfc:VCFFile` |
| `hero:vcfQual` | " | `vcfc:qual` |
| `hero:vcfFilter` | " | `vcfc:filter` |
| `hero:vcfInfo` | " | `vcfc:infoRaw` |
| `hero:variantQuality` | " | `vcfc:qual` |
| `hero:VariantQuality` | " | `vcfc:FilterStatus` |
| `med2rdf:reference_allele_vcf` | " | `vcfc:ref` |
| `med2rdf:alternative_allele_vcf` | " | `vcfc:alt` |

These are exactly the file-level, syntax-carrying terms a variation model like
VRS has no reason to define — which is the gap this vocabulary exists to fill.
The remaining 39 are annotation and clinical-interpretation concepts, out of
scope by design; they are listed in [FUTURE-MAPPINGS.md](FUTURE-MAPPINGS.md).

## The BioHackathon sets

[`bh25/`](bh25/) records what four participating projects asserted about their
own terms at the **SWAT4HCLS 2025 BioHackathon**. These are third-party
assertions, kept verbatim and deliberately not folded into the alignment
module.

The authoritative source is the project's [Google Sheets
workbook](https://docs.google.com/spreadsheets/d/1JCVV3GB7t4cp4GrKcfn0OG4dJjJHI9dp5BEHEl-3xN8/edit).
Each set records its own sheet under `mapping_set_source`, and
[registry.json](registry.json) lists all five. The transcription was diffed
against the live workbook on 2026-09-08: all 116 mappings match, with no
differences beyond the normalisations below.

**Why a copy is kept here.** The workbook is authoritative but is not a
citable, versioned or content-addressable artifact — it can be edited or
unshared without notice, and there is no revision to pin. The upstream paper
repository publishes no mapping data, and the SSSOM conversion its text refers
to ("publicly available on Github") was never released; both links in the paper
are unfilled placeholders. A validated, checked-in transcription that names its
source is the durable form.

| Set | Subject model | Mappings |
| --- | --- | --- |
| [`hero-to-vrs.sssom.tsv`](bh25/hero-to-vrs.sssom.tsv) | [HERO](https://hereditary.dei.unipd.it/ontology/genomics/) | 25 |
| [`med2rdf-to-vrs.sssom.tsv`](bh25/med2rdf-to-vrs.sssom.tsv) | [med2rdf](http://med2rdf.org/) | 50 |
| [`gigwa-to-vrs.sssom.tsv`](bh25/gigwa-to-vrs.sssom.tsv) | [GIGWA](https://gigwa.southgreen.fr/gigwa/) | 30 |
| [`sembeacon-to-vrs.sssom.tsv`](bh25/sembeacon-to-vrs.sssom.tsv) | [SemBeacon](https://gitlab.univ-nantes.fr/bodrug-a/genomic-variants-schema) | 11 |

Composing `X → VRS` with `vcf-core → VRS` to get `X → vcf-core` is **not**
sound: SKOS mapping properties do not compose, and `closeMatch` least of all.
The BioHackathon sets were used to *find* candidates; every alignment in the
curated set was then judged directly against the term definitions.

### Transcription notes

Assertions are unchanged; syntax was normalised so the files parse.

- Decimal commas in `confidence` (`0,6`) became decimal points, and `1` became `1.0`.
- Dates in `DD/MM/YYYY` became ISO 8601.
- Object prefixes `ga4gh:` and `ga4ghvrs:`, used interchangeably across the sheets, became `vrs1:`.
- The typo `g44gh:` (five Med2RDF rows) was corrected, flagged per row.
- OBO and SIO CURIEs were normalised, so `so:SO_0000704`, `GENO:GENO_0000002` and `sio:SIO_000897` became `so:0000704`, `geno:0000002` and `sio:000897`.
- Cells holding several CURIEs were split into one row each, flagged in `comment`.
- Targets naming a field of a class (`ga4ghvrs:SequenceInterval#start`) keep the class as `object_id` and name the field in `comment`, since `#` cannot appear in a CURIE's local part.
- `SIO_000897` appeared twice in the Med2RDF sheet under two labels, asserting the same triple; merged.
- `ga4gh:oneOf` and `ga4gh:definition` are JSON Schema keywords rather than VRS terms, and `ga4gh:CopyNumber` existed only in VRS 1.2; all three are flagged in `comment`.
- `mapping_justification`, required by SSSOM and absent from the sheets, is `semapv:ManualMappingCuration` throughout.
- Rows too incomplete to be assertions are in [`bh25/UNRESOLVED.md`](bh25/UNRESOLVED.md).

Two subjects carry competing mappings in the source sheets (`med2rdf:Genome`,
and `faldo:Position` in SemBeacon). Both are kept, with their original
confidences, because the disagreement is part of the record.

## References

- BioHackathon paper — <https://github.com/NuriaQueralt/SWAT4HCLS-BH25-variant-rdf-representations/blob/main/paper/paper.md>
- Project site — <https://swat4hcls-2025-genomic-variation.github.io/genomic-variant-schema/>
- SSSOM specification — <https://mapping-commons.github.io/sssom/>
- SSSOM mapping predicates — <https://mapping-commons.github.io/sssom/mapping-predicates/>
- GA4GH VRS 2.0 — <https://vrs.ga4gh.org/en/stable/>
- HERO — <https://w3id.org/hereditary/ontology/genomics/schema/>
- GVO — <http://genome-variation.org/resource/gvo>
- GFVO — <https://github.com/BioInterchange/Ontologies>
- Med2RDF ontology — <https://github.com/med2rdf/med2rdf-ontology>
