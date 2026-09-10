# Validation Tests

This directory contains executable validation code and its small negative/edge-case
fixtures. It is intentionally separate from `scripts/`, which contains generators,
build steps and publication helpers.

- `test_validation.py` contains focused SHACL regression probes.
- `test_requirement_traceability.py` loads the [coverage measurement tests](../coverage/methodology/tests/test_assessment.py): source pins, wrong-version evidence, incomplete reviews, answer controls and fixed denominators.
- `validate_shacl.py` runs the complete SHACL and semantic validation suite.
- `check_examples.py` reconstructs logical VCF lines and executes the example queries.
- `verify-vcf45-implementation.mjs` performs fast RDF parsing and VCF 4.5 registry checks.
- `semantic_validation.py` contains the decoded-value checks used by the SHACL runner.
- `shacl/` contains negative and generic validation fixtures.
- `generated/validation.json` records the latest machine-readable complete-suite summary.
- `test_serialization.py` tests the [source-byte checker](../coverage/vcf45-inventory/check_serialization.py).
- `verify-profile-comparison.mjs` asserts the [two-profile example](../examples/profile-comparison/README.md);
  its recorded output is `generated/profile-comparison.json`.
- Coverage inventories and reports live in [coverage/](../coverage/README.md).
- `.validation-stamp.json` caches the digest of the last full run (see the gate section below).

## Local setup

From the repository root, install Node dependencies and create a Python
environment (Python 3.10 or newer):

```sh
npm ci
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
npm run ontology:bundle
```

To validate a supplied graph, run
`.venv/bin/python tests/validate_shacl.py input.ttl`.
See [the validation profiles](../shacl/README.md) for rule selection and warnings.

## Repository checks

Run the supported entry points from the repository root:

```sh
npm run validate           # fast checks always; slow suite only if normative inputs changed
npm run validate:force     # unconditional full run, then refresh the stamp
npm run validate:regressions
npm run validate:examples
npm run validate:profiles  # the two-profile example fixtures
```

## Why `npm run validate` is usually fast

The complete suite takes several minutes, but most commits touch documentation
rather than the vocabulary. `scripts/validation-gate.py` hashes the normative
inputs — ontology modules, SHACL profiles, per-version registries, examples,
mappings, validation code, coverage inputs and the declared version — into a
single digest in `tests/.validation-stamp.json`. When that digest is unchanged,
`npm run validate` runs only the fast lane (RDF parse, coverage report, examples
and the two-profile fixtures) and skips the rest.

The stamp stores **one digest, not a per-file hash table**: it is a build cache,
and `git status` already tells you which files differ. Provenance hashes that do
matter live with the assessment that depends on them, in
[`coverage/methodology/`](../coverage/methodology/README.md).

Changing any normative file, or bumping the version in `package.json`, makes the gate
require a full run. `npm run validate:gate:status` reports which way it will go.

**Commit the stamp.** CI does not trust it — pull-request validation is scoped by path
filters and always runs `validate:force` — but it does fail the build if the stamp you
committed is out of date.
