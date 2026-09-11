# Validation profiles

Load `ontology/vcf-core-vocabulary.bundle.ttl` with RDFS inference, then merge:

1. `vcf-core-vocabulary.shacl.ttl`: structural, datatype and local constraints.
2. `vcf-core-vocabulary-sparql.shacl.ttl`: common ordering and cross-resource rules.
3. `vcf-core-consistency.shacl.ttl`: raw/parsed agreement and value cardinalities.
4. `vcf-4.1.shacl.ttl` through `vcf-4.5.shacl.ttl`: one overlay per version in
   `ontology/versions/registry.json`.

Every overlay may be loaded at once: their rules follow the owning file's
`fileFormat`. The optional `VCF41File`…`VCF45File` classes additionally check
their version gates.
The core retains syntactic VCF 4.0 file labels, but **no 4.0 conformance overlay is
claimed**; the complete CLI validator reports that version as unsupported.

The overlays cover version-specific Number codes, reserved declarations and SV
aggregate widths. For example, CIPOS has two values in 4.1–4.3, and two per ALT
in 4.4–4.5. Older CN/SVLEN declarations are not checked against the 4.5 registry.
The legacy snapshots in `ontology/versions/` record official source URLs and
SHA-256 hashes.

Both the overlays and the `VCF4xFile` gates are generated from
`ontology/versions/registry.json`, which declares each version's permitted Number
codes, phase-indicator rule and SV tuple widths. Edit that table rather than the
generated `.ttl` files; see [scripts/README.md](../scripts/README.md). For 4.1–4.2, only explicit declarations are captured; prose-only
INFO fields whose exact format is left to producers are not assigned invented
Number/Type requirements.

Raw-only fields remain supported. If a record materializes ALT resources, SV
confidence/mobile-element tuples must also materialize their complete indexed
items. Other materialized lists must agree with their raw token sequence.
Plain `xsd:integer` and integer-derived XSD datatypes are accepted with numeric
bounds; decimal-valued indices are rejected. Custom `VCFFloat` and
`GenotypeString` literals have explicit lexical checks. Missing `vcfc:Null`
literals must contain the dot token.

The Python runner separately reports decoded-value checks from
`tests/semantic_validation.py`: arbitrary-ploidy G/LG cardinalities,
Number=M counts for explicit alleles, numeric ranges, repeats, condensed values
and sample reference blocks. SHACL G/LG formulas currently cover ploidy 1–8;
Python uses the general combinatorial formula. Neither layer infers eligible
base-modification sites inside reference blocks without a reference sequence.
This separation is deliberate and visible in validation output.

For supplied data, warnings do not fail validation unless `--warnings-as-errors`
is requested. The maintained examples must have zero warnings in CI.

```sh
.venv/bin/python tests/validate_shacl.py input.ttl
.venv/bin/python tests/validate_shacl.py headers.ttl records.ttl --warnings-as-errors
npm run validation:build  # regenerate checked-in SPARQL files offline
# Refresh historical source snapshots only after reviewing official changes:
.venv/bin/python scripts/build-shacl-profiles.py --spec-dir /path/to/hts-specs
```

See [the coverage checklist](../coverage/vcf45-inventory/README.md) for tested requirements and
remaining limits. These profiles are not an exhaustive VCF certification.
