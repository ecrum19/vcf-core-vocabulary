# VCF Core Vocabulary v2.1.2 — release notes

**Prepared 14 September 2026 · changes since 2.1.1**

A patch release: **no vocabulary terms change**, so nothing a consumer queries or validates
against moves. It records interpretation guidance for one deliberately permissive shape,
after a cross-producer check found two conforming graphs of the same VCF file differing
there. The `https://w3id.org/vcf-core/vocab#` namespace, both sample representation profiles
and every existing term IRI are unchanged. These notes describe the repository version; they
do not assert that a tag or hosted release has been published.

## Ontology changes

**None.** No term was added, removed, renamed or redefined. The module version IRIs and
`owl:versionInfo` values move to 2.1.2 so a merged graph does not mix release versions;
reserved registries continue to carry their **VCF specification** versions.

The alignment module moves with them. Its version comes from `subject_source_version` in
[`mappings/vcf-core-alignments.sssom.tsv`](../mappings/vcf-core-alignments.sssom.tsv), the
curated source of truth; `mappings/vcf-core-alignments.ttl` is regenerated from it by
`npm run mappings:build`. The 123 mappings themselves are unchanged.

## QUAL datatype guidance

`vcfc:QualityShape` accepts six datatypes on purpose. The VCF specification allows QUAL to be
a number or one of `INF`, `-INF`, `INFINITY` or `NAN` in any case; `xsd:double` covers the
numeric forms plus `INF`/`-INF`/`NaN`, but no XSD numeric datatype accepts the `INFINITY`
spelling or the case variants. Narrowing the range would therefore reject conforming data.

The cost of that permissiveness is that **two correct producers can serialize the same QUAL
differently and both conform**. This repository's own materializer writes
`"60"^^vcfc:VCFFloat`; VCF-RDFizer writes `"60"^^xsd:decimal`. A cross-producer replay of the
coverage queries over both producers' graphs found exactly this, on every QUAL case in the
subset it exercises — 20 checks, requirement R11. Neither producer is wrong, and only a query
that projects `DATATYPE(?qual)` can tell them apart.

The shape is unchanged. What is new is a normative comment recording the consequence:

- Producers **SHOULD** write `vcfc:VCFFloat`, the only branch that also carries
  `INF`/`INFINITY`/`NAN`.
- Consumers **MUST NOT** branch on `DATATYPE(?qual)`. Compare the lexical value, or accept the
  alternatives explicitly.

The guidance lives in [`shacl/vcf-core-vocabulary.shacl.ttl`](../shacl/vcf-core-vocabulary.shacl.ttl)
rather than as an `rdfs:comment` on `vcfc:qual`. That placement is deliberate:
`coverage/methodology/scripts/assess.py` hashes `ontology/*.ttl` into the review fingerprint,
so a comment there would invalidate all 95 recorded review acceptances for no semantic change.
`shacl/` is not hashed. `npm run methodology:check -- --require-reviewed` still reports zero
reviews pending.

## Why the version bump does not re-open the review

`assess.py` blanks `owl:versionInfo` and `owl:versionIRI` values before hashing an ontology
module, so moving the release version leaves the evidence digest unchanged while every other
byte of those files still counts. This release exercises that property for the first time: the
version strings move, the fingerprints do not, and the recorded acceptances stand.

## Validation

Full suite re-run for this release: 21 fixtures with 0 violations, 101 regression tests OK,
333/333 reserved Number/Type rows in agreement, 104/104 inventoried VCF 4.5 constructs
represented with 87 enforced. Because SHACL is a normative input, editing it invalidated the
build cache and forced the heavy suite rather than the fast path.

## Upgrading

Nothing to do. No term changed, so no query, SHACL profile or stored graph needs revision.
Consumers that currently branch on `DATATYPE(?qual)` should stop; that pattern was never
reliable and is now documented as unsupported.
