<img src="assets/branding/vcf-core-mark.png" align="right" width="112" height="112" alt="VCF Core Vocabulary logo">

# VCF Core Vocabulary

[![Vocabulary version: 2.1.0](https://img.shields.io/badge/vocabulary-v2.1.0-006875)](docs/RELEASE-NOTES-v2.1.0.md)
[![VCF validation profiles: 4.1–4.5](https://img.shields.io/badge/VCF_profiles-4.1%E2%80%934.5-006875)](shacl/README.md)
[![License: CC BY 4.0](https://img.shields.io/badge/license-CC_BY_4.0-006875)](LICENSE)

[![Vocabulary and example validation](https://github.com/ecrum19/vcf-core-vocabulary/actions/workflows/validate.yml/badge.svg?event=pull_request)](https://github.com/ecrum19/vcf-core-vocabulary/actions/workflows/validate.yml)
[![Documentation publication](https://github.com/ecrum19/vcf-core-vocabulary/actions/workflows/publish-pages.yml/badge.svg?branch=main)](https://github.com/ecrum19/vcf-core-vocabulary/actions/workflows/publish-pages.yml)
[![Coverage review: ongoing](https://img.shields.io/badge/coverage_review-ongoing-d89a4a)](coverage/methodological/README.md#current-findings-and-review-status)

**An RDF vocabulary for Variant Call Format (VCF) data, with validation profiles
for VCF 4.1–4.5.**

VCF Core represents files, header declarations, records, alleles and sample
genotypes as linked data. It preserves the source context needed to interpret a
VCF call and provides links to external models of sequence variation. Any
converter can adopt the vocabulary.

**Version 2.1.0** · [Release notes](docs/RELEASE-NOTES-v2.1.0.md) ·
[Examples](examples/README.md) · [Validation](shacl/README.md) ·
[Coverage assessment](coverage/README.md)

## Start with an example

Open the [quickstart VCF](examples/core/example-quickstart.vcf) alongside its
[RDF graph](examples/core/example-quickstart.ttl): one site, its header and its
call, with no sample columns. Load the Turtle graph into an RDF store and run:

```sparql
PREFIX vcfc: <https://w3id.org/vcf-core/vocab#>

SELECT ?chrom ?position ?ref ?alt
WHERE {
  ?record a vcfc:VCFRecord ;
          vcfc:chrom ?chrom ;
          vcfc:pos ?position ;
          vcfc:ref ?ref ;
          vcfc:alt ?alt .
}
```

The result is `chr1`, `100`, `A`, `G`. For sample data, explore the
[expanded sample example](examples/core/example-minimal-record.ttl) or the
[eight-sample condensed cohort](examples/profiles/example-condensed-cohort.ttl).
The [example guide](examples/README.md) includes source provenance, versioned
fixtures and queries for genotypes, phasing and structural variation.

## Use the vocabulary

The namespace is `https://w3id.org/vcf-core/vocab#`, conventionally `vcfc:`.
VCF specification versions (4.1–4.5) and vocabulary releases (2.1.0) are separate.

The vocabulary is supplied as five Turtle modules. Load all five when working
with the complete model; the core module alone does not contain every term.

| Module | What it describes |
| --- | --- |
| [Core](ontology/vcf-core-vocabulary.ttl) | Files, headers, records, calls, sample representations, ordering and missing values |
| [Alleles and values](ontology/vcf-core-alleles.ttl) | REF/ALT alleles, indexed field values and padding interpretations |
| [Genotypes](ontology/vcf-core-genotypes.ttl) | Parsed genotypes, phasing, phase sets and local alleles |
| [Structural variation](ontology/vcf-core-sv.ttl) | Breakends, repeats, copy number, reference blocks and base modifications |
| [Reserved keys](ontology/vcf-core-reserved-keys.ttl) | VCF 4.5 INFO/FORMAT definitions with specification provenance |

[Historical reserved-key definitions](ontology/versions/) accompany the earlier
VCF profiles. The model retains VCF syntax and can link to FALDO, SO, GENO, VRS
and ChEBI where appropriate. These links do not establish biological equivalence
on their own.

Use a stable project-specific HTTP(S) base for instance identifiers you intend
to share. The examples' `file://…` identifiers illustrate local resources;
[IRI guidance](examples/README.md#real-sample-calls-small-files) explains the convention.

## Choose a sample representation

A file declares its choice with `vcfc:representationProfile`.

| Profile | How sample values are represented | How to access them |
| --- | --- | --- |
| `ExpandedRepresentation` | Individual `SampleCall` and `FormatFieldValue` resources | Direct RDF graph patterns |
| `CondensedRepresentation` | A `CohortCallMatrix` with one `FormatValueVector` per FORMAT key | Decode each vector using the ordered `SampleSet` |

With `VCFTextVector`, tabs separate samples and commas stay inside each sample's
value. Every sample keeps its position, including missing values. The
[cohort query](examples/queries/cohort-genotypes.rq) demonstrates accessing an
individual genotype from a vector.

Where VCF permits missing values, scalar RDF values use `"."^^vcfc:Null`.
Inside raw fields and vector payloads, the dot remains part of the source text.

## Validate your data

The [validation guide](shacl/README.md) explains the shared SHACL rules,
version-specific overlays and supplementary Python checks. The complete runner
checks both RDF structure and decoded values; running SHACL alone omits the
Python checks. It selects version rules from each file's `fileFormat`.

After the [local setup](tests/README.md#local-setup), validate your Turtle graph:

```sh
.venv/bin/python tests/validate_shacl.py input.ttl
```

Warnings are reported separately; add `--warnings-as-errors` to make them fail
validation. VCF 4.0 has no validation overlay. BCF byte layout and exact
byte-for-byte reconstruction are outside the vocabulary's scope.

## What does the coverage evidence show?

The repository provides two assessments with different denominators:

| Assessment | Recorded result | Interpretation |
| --- | --- | --- |
| [Curated VCF 4.5 inventory](coverage/curated/README.md) | **104/104** constructs represented; **87** with enforcement evidence | Coverage of the selected inventory under its preservation and structure rubric |
| [Methodological VCF 4.1–4.5 assessment](coverage/methodological/README.md) | **333/333** extracted Number/Type rows match; **133/491** retained requirements have full evidence | Specification-derived traceability under reviewed criteria; complex semantic adequacy still requires judgment |

Neither result establishes complete VCF conformance or an overall semantic
coverage percentage. The methodological assessment records known validation gaps
and unfinished source-review work. See the [current report](coverage/methodological/generated/report.md)
for the results and [review decisions](coverage/methodological/DECISIONS.md) for
their interpretation.

## Releases, citation and contributions

[Version 2.1.0](docs/RELEASE-NOTES-v2.1.0.md) adds structured assembly-contig,
padding and FORMAT-key representations and documents the coverage methods.
Users of the former VCF-RDFizer namespace should follow the
[2.0.0 migration guide](docs/RELEASE-NOTES-v2.0.0.md#migrating-from-v110).
The [VCF-RDFizer converter](https://github.com/ecrum19/VCF-RDFizer) is a separate
project with its own releases.

Use [CITATION.cff](CITATION.cff) when citing the vocabulary. The vocabulary is
licensed under [CC BY 4.0](LICENSE); [acknowledgements](ACKNOWLEDGEMENTS.md)
record attribution and development assistance.

Report problems or propose changes through the repository's issues and pull
requests. For maintenance work, see the [build tools](scripts/README.md),
[test guide](tests/README.md) and [coverage reproduction instructions](coverage/README.md).
