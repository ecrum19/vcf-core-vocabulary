# VCF Core Examples

The examples are grouped by purpose so that source VCF files, RDF serializations,
profile demonstrations and version-specific fixtures are easy to find.

## Start Here

The [quickstart graph](core/example-quickstart.ttl) and its [VCF source](core/example-quickstart.vcf)
show one site with complete metadata and no samples. The [header example](core/example-headers.ttl)
and [minimal record example](core/example-minimal-record.ttl) can be inspected together to see how
header declarations, a record and expanded sample calls fit together.

| Example | What to inspect |
| --- | --- |
| [`core/example-quickstart`](core/example-quickstart.ttl) | File, header, record, call, REF/ALT and missing values |
| [`core/example-headers`](core/example-headers.ttl) | A complete zero-record VCF with structured header attributes and sample columns |
| [`core/example-minimal-record`](core/example-minimal-record.ttl) | One source record and its real sample call, with GT, allele depths and read depth |
| [`core/example`](core/example.ttl) | Three real HaplotypeCaller records with GT:AD:DP:GQ:PL, INFO annotations and one sample |
| [`profiles/example-condensed-cohort`](profiles/example-condensed-cohort.ttl) | Eight 1000 Genomes samples across three SNPs, represented by ordered phased-GT vectors |
| [`profile-comparison/`](profile-comparison/README.md) | One synthetic record represented **twice**, once per sample profile, side by side |

## Real sample calls, small files

The [condensed VCF](profiles/example-condensed-cohort.vcf) retains the first eight
sample columns of the public [1000 Genomes Phase 3 chromosome 20 callset](https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/ALL.chr20.phase3_shapeit2_mvncall_integrated_v5b.20130502.genotypes.vcf.gz):
HG00096, HG00097, HG00099, HG00100, HG00101, HG00102, HG00103 and HG00105.
Three biallelic SNPs at positions 61795, 68749 and 69094 show reference,
heterozygous and alternate-homozygous calls, including both phased orientations.
The original VCF 4.1 / b37 reference context and all 24 GT calls are preserved.
AC, AF and AN are recalculated for these eight samples. The source provides GT
only; no DP, GQ or likelihood values have been invented.

The [expanded VCF](core/example.vcf) retains three records from
[`test-larger.vcf.gz`](https://github.com/ecrum19/VCF-RDFizer/blob/main/test/test_vcf_files/test-larger.vcf.gz)
in the VCF-RDFizer test fixtures, including the actual sample `NG131FQA1I` and its
GT:AD:DP:GQ:PL values. It keeps VCF 4.2 and GRCh38 coordinates; INFO is reduced
to AC/AF/AN/DP. The minimal example keeps one of these records with GT:AD:DP,
and the header example contains the same metadata with zero records.
The long caller command lines and unused declarations are omitted.

[provenance.json](provenance.json) records the source URL/hash, selected samples,
coordinates and exact reductions. These are small teaching subsets of source
calls, not representative population samples. The version-specific feature
fixtures below remain explicitly synthetic so that their advanced structures
can be explained without attributing invented observations to real samples.

The example instance IRIs intentionally use the portable local form
`file://<vcf-filename>.vcf#...`, for example
`file://example-file1.vcf#header` and
`file://example-file1.vcf#record/1`. These identifiers demonstrate the
ontology's canonical pattern and are not expected to resolve over HTTP. Use an
absolute `file:///...` IRI for a real local path, or a stable HTTP(S) base when
the generated RDF must be shared and dereferenced.

## Version Fixtures

The `vcf-versions/` directory contains examples that exercise version-specific
reserved declarations and structural-variant rules.

| Directory | Coverage |
| --- | --- |
| [`vcf-versions/vcf-4.1`](vcf-versions/vcf-4.1) | VCF 4.1 declarations and historical SV tuple behavior |
| [`vcf-versions/vcf-4.2`](vcf-versions/vcf-4.2) | VCF 4.2 declarations and historical SV tuple behavior |
| [`vcf-versions/vcf-4.3`](vcf-versions/vcf-4.3) | VCF 4.3 declarations and historical SV tuple behavior |
| [`vcf-versions/vcf-4.4`](vcf-versions/vcf-4.4) | VCF 4.4 declarations and historical SV tuple behavior |
| [`vcf-versions/vcf-4.5`](vcf-versions/vcf-4.5) | Breakends, linked features, gVCF reference blocks and repeats |

The versioned and profile fixtures have paired Turtle graphs with matching
basenames. The focused core examples intentionally use descriptive pairs such
as `example-file1.vcf` with `example-minimal-record.ttl`.

## Queries and Manifest

[`manifest.json`](manifest.json) pairs each VCF source with its RDF graph and
records exact expected answers for the executable SPARQL queries in [`queries/`](queries/).
For example, `reference-blocks.rq` returns S1 -> length 5/end 704 and S2 ->
length 10/end 709, while `mixed-phasing.rq` checks the three indicators `|`, `/`, `|`.
The new [cohort query](queries/cohort-genotypes.rq) uses `sampleIndex` to decode
HG00096's GT vector cell at each site: `1|0`, `1|1`, `1|0`. Change the sample
name to inspect another column. This query explicitly decodes the vector payload;
it does not assume a separate `SampleCall` resource exists in the condensed graph.

## Validation and Regeneration

```sh
npm run examples:build
# Regenerate only the condensed RDF:
.venv/bin/python scripts/vcf_examples.py --write --only examples/profiles/example-condensed-cohort.vcf
npm run validate:shacl
npm run validate:examples
npm run validate:regressions
# Validate a supplied graph, including version-specific overlays:
.venv/bin/python tests/validate_shacl.py examples/vcf-versions/vcf-4.3/example-vcf43.ttl
```

`npm run examples:build` refreshes the generated rich examples from their checked-in
VCF sources. The quickstart and the [profile comparison](profile-comparison/README.md)
are authored separately; `npm run validate:profiles` checks the latter.
`npm run examples:ttl` regenerates [`core/example.ttl`](core/example.ttl) from
[`core/example.nt`](core/example.nt). The validation suite checks logical VCF line
reconstruction, vocabulary declarations, property kinds, SHACL conformance and
the expected query answers; it does not promise byte-for-byte preservation of
arbitrary VCF serialization.

Current checks are reproducible with `npm run validate:examples` and
`npm run validate:force`; fixture results are in
[the complete validation report](../tests/generated/validation.json).
External FALDO and ChEBI links in synthetic feature fixtures demonstrate
integration points rather than a complete translation to a biological variation
ontology.
