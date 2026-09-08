# Validation Tests

This directory contains executable validation code and its small negative/edge-case
fixtures. It is intentionally separate from `scripts/`, which contains generators,
build steps and publication helpers.

- `test_validation.py` contains focused SHACL regression probes.
- `test_requirement_traceability.py` loads the [independent coverage workflow's tests](../coverage/methodological/test_workflow.py), including pin failures, stable extraction, stale evidence, and wrong-version mappings.
- `validate_shacl.py` runs the complete SHACL and semantic validation suite.
- `check_examples.py` reconstructs logical VCF lines and executes the example queries.
- `verify-vcf45-implementation.mjs` performs fast RDF parsing and VCF 4.5 registry checks.
- `semantic_validation.py` contains the decoded-value checks used by the SHACL runner.
- `shacl/` contains negative and generic validation fixtures.
- `generated/validation.json` records the latest machine-readable complete-suite summary.
- `test_serialization.py` tests the [source-byte checker](../coverage/curated/check_serialization.py).
- Coverage inventories, reports and manuscript checks live in [coverage/](../coverage/README.md).
- `.validation-stamp.json` records the fingerprint of the last full run (see the gate section below).

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
```

The regression command filters the specific `DeprecationWarning: 'count' is
passed as positional argument` emitted by the pinned RDFLib 7.6.0 SPARQL
`REPLACE` implementation on newer Python versions. The filter matches that
message, category and module only; other warnings and test failures remain
visible. It does not patch RDFLib or change validation results. Remove it when
the pinned dependency uses a keyword argument for this call. To inspect the
unfiltered warnings, run `python -m unittest discover -s tests -p 'test_*.py'`
inside the activated environment.

## Why `npm run validate` is usually fast

The complete suite takes several minutes, but
most commits touch the manuscript or documentation rather than the vocabulary.
`scripts/validation-gate.py` fingerprints the normative inputs — ontology modules,
SHACL profiles, per-version registries, examples, mappings, validation code and the
declared version — into `tests/.validation-stamp.json`. When that fingerprint is
unchanged, `npm run validate` runs only the fast lane (RDF parse, coverage report,
paper-figure check, examples and paper evidence) and skips the rest.

Desktop metadata (`.DS_Store`) and Python caches are excluded from the fingerprint,
so `npm run clean` does not invalidate a successful full validation.

Changing any normative file, or bumping the version in `package.json`, makes the gate
require a full run. `npm run validate:gate:status` shows what it thinks changed. The
manuscript is deliberately outside the fingerprint, so editing prose never costs three
minutes; the paper-figure check that guards its statistics is in the fast lane.

**Commit the stamp.** CI does not trust it — pull-request validation is scoped by path
filters and always runs `validate:force` — but it does fail the build if the stamp you
committed is out of date.
