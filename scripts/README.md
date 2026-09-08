# Repository Scripts

Scripts in this directory generate repository artifacts or extend the OCG build.
Validation and regression checks live in `tests/`. Assessment-specific scripts
and results live in [coverage/](../coverage/README.md).
Use `npm run clean` to remove optional audits, generated site output and build caches.

- `build-ontology-bundle.mjs` combines the normative ontology modules for OCG.
- `build-shacl-profiles.py` generates the consistency rules and every version-scoped artifact.
- `build-mapping-sets.py` renders the alignment module from the curated SSSOM set and validates every mapping set under [mappings/](../mappings/README.md).
- `validation-gate.py` fingerprints the normative inputs so the slow suite only reruns when they change.
- `convert-example-nt-to-ttl.mjs` formats the canonical N-Triples example as Turtle.
- `generate-reserved-keys.mjs` creates the full reserved-key registry for one VCF version.
- `insert-class-hierarchy.mjs` adds the configured class-hierarchy extension after OCG builds the site.
- `migrate-namespace.mjs` provides the one-shot 1.1.0 namespace migration utility.
- `vcf_examples.py` materializes the generated example graphs from their VCF sources.
- `version_registry.py` loads and validates `ontology/versions/registry.json` for the Python generators.
- The independent [requirement-traceability workflow](../coverage/methodological/README.md)
  lives under `coverage/methodological/`; `methodological:build` regenerates it and
  `methodological:check` checks reproducibility without accepting pending decisions.

All commands are exposed through `package.json`; run them from the repository root
so relative source and output paths remain stable.

## The version registry

`ontology/versions/registry.json` declares which VCF specification versions the
vocabulary covers and how each differs from its neighbours. It is the only place
those facts are written down. Derived from it are:

| Artifact | Generator |
| --- | --- |
| `shacl/vcf-<version>.shacl.ttl` overlays | `build-shacl-profiles.py` |
| `ontology/versions/vcf-<version>-reserved.{json,ttl}` | `build-shacl-profiles.py --spec-dir` |
| `ontology/vcf-core-reserved-keys.ttl` | `generate-reserved-keys.mjs` |
| `VCF4xFile` classes in `ontology/vcf-core-vocabulary.ttl` | `build-shacl-profiles.py` |
| version entries in `ocg.config.json` | `build-shacl-profiles.py` |
| supported fixture versions and their SV/CN behaviour | `vcf_examples.py` |

A version is one of two modes. A `snapshot` version records only the explicit
reserved declarations its specification states, parsed from the LaTeX source into
a hashed JSON snapshot. The `registry` version — there is exactly one, the
`current` one — gets the full treatment: descriptions, arities, key patterns and
ChEBI alignments.

### Adding a VCF version

1. Append an entry to `ontology/versions/registry.json`. Read its Number codes,
   phase-indicator rule, copy-number scope and SV tuple widths off the official
   specification; do not copy the previous version's values on the assumption
   that nothing changed.
2. If the reserved keys come from a LaTeX source, refresh the snapshot from a
   local `hts-specs` checkout:
   `.venv/bin/python scripts/build-shacl-profiles.py --spec-dir /path/to/hts-specs`
3. Run `npm run versions:build`.
4. Run `npm run validate`.

`tests/test_version_registry.py` fails if the checked-in artifacts and the table
disagree, so step 3 cannot be skipped silently.

Promoting a version to `current` is deliberately not automatic: move
`reservedKeys.mode: "registry"` onto the new version, give the previous one a
`snapshot` entry, and regenerate. A specification that introduces genuinely new
constructs also needs terms added to the core vocabulary, which is an ontology
release rather than a table edit.

Versions whose specification has no machine-readable source — anything before
VCF 4.1, which is where `hts-specs` begins — need a hand-curated snapshot in the
same JSON shape, citing the archival source URL and its hash. The parser cannot
produce one.
