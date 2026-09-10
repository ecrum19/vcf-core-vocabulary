# Contributing

Thanks for your interest. This repository holds an RDF vocabulary, its
validation profiles and the evidence for its coverage claims. Issues and pull
requests are welcome.

## Setup

From the repository root, with Node 24+ and Python 3.10+:

```sh
npm ci
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
npm run ontology:bundle
```

Optionally install the pre-commit hook, which validates the documentation site's
source configuration:

```sh
git config core.hooksPath .githooks
```

## Before opening a pull request

```sh
npm run validate
```

This always runs the fast checks and runs the slow SHACL and regression suite
only when a normative input changed. If it ran the slow suite, **commit the
updated `tests/.validation-stamp.json`** — CI fails when the committed stamp is
stale. Use `npm run validate:force` to run everything unconditionally.

## The one rule that matters

**Inputs are authored; outputs are generated.** Every `generated/` directory and
every artefact listed below is rebuilt from committed inputs. Editing generated
output is the most common way to break a build here, because the scripts
recompute the values and then disagree with what you wrote.

| If you want to change | Edit | Then run |
| --- | --- | --- |
| A vocabulary term | the relevant `ontology/vcf-core-*.ttl` module | `npm run validate` |
| Reserved key definitions | `ontology/versions/registry.json` | `npm run versions:build` |
| Validation rules | the generator inputs, not `shacl/vcf-*.shacl.ttl` | `npm run validation:build` |
| An example graph | the `.vcf` source | `npm run examples:build` |
| An external alignment | the authored SSSOM set in `mappings/` | `npm run mappings:build` |
| A coverage judgment | the assessment's `inputs/` | `npm run methodology:build` |

Adding a VCF version has its own procedure — see
[`scripts/README.md`](scripts/README.md#adding-a-vcf-version).

## Changing the coverage assessments

Read [`coverage/README.md`](coverage/README.md) first: there are two assessments,
they count different things, and their numbers must not be combined.

Two constraints specific to them:

- **Expected query answers are authored from the specification, never copied from
  query output.** A test that records what the code already does proves nothing.
  Do not change an expected answer to make a test pass.
- **Review acceptance is content-addressed.** Acceptance entries in
  `coverage/methodology/inputs/review.json` carry a fingerprint over the evidence
  they cover. Changing the evidence invalidates the acceptance, which is
  intended — copying a fingerprint forward is not a review. This also means the
  assessment directory cannot be renamed or moved without invalidating all of
  them, so please do not relocate it as part of unrelated cleanup.

## Style

Match the surrounding code and prose. In documentation, state limits alongside
results — the existing text is deliberately careful to say what a check does
*not* establish, and that convention is worth keeping.

## Licence

Contributions are accepted under the repository's [CC BY 4.0](LICENSE) licence.
