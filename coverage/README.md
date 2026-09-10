# Coverage assessments

**The question this directory answers: if you convert a VCF file into RDF using
this vocabulary, what gets kept, and how do we know?**

Everything here is evidence for that question. Nothing here is part of the
vocabulary itself — you can use the vocabulary without reading any of it.

## Start here if you are new

VCF is a text format for genomic variants. This repository defines an RDF
vocabulary for representing VCF data. The obvious worry about any such
translation is **silent loss**: a field that quietly disappears, or that survives
only as an opaque blob of text you have to re-parse by hand.

So we test for it. Both assessments below ask the same two questions of each
piece of VCF information, and both answer them by running real queries against
RDF converted from real VCF files:

| Question | Name we give it | Why it matters |
| --- | --- | --- |
| Is the information still there at all? | **preservation** | If it is gone, the conversion lost data. |
| Can a query reach it without re-parsing text? | **structure** | Information hidden inside a string is preserved but not usable as data. |

A construct can pass the first and fail the second. That is the interesting
middle case, and it is why we never report a single number.

**What none of this claims.** No assessment here shows that the vocabulary
handles every VCF file, that a converter is correct, or that the biology is
right. They show that specific information from specific files could be
retrieved by specific queries. That is a real but bounded claim.

## Why there are two assessments

They have **different denominators** — they are counting different things — so
their percentages can never be added, averaged, or compared to each other.

| | [`methodology/`](methodology/README.md) | [`vcf45-inventory/`](vcf45-inventory/README.md) |
| --- | --- | --- |
| **What it counts** | Information requirements read out of the VCF specification text | Constructs in a hand-curated list of the VCF 4.5 logical model |
| **Where the list comes from** | Derived from the pinned specification sources, section by section | Authored by a maintainer as an inventory |
| **VCF versions** | 4.1, 4.2, 4.3, 4.4 and 4.5, scored separately | 4.5 only |
| **How a passing item is decided** | A query returns independently authored expected answers | A reviewer judges the two axes; the script checks the cited terms and files exist |
| **Sample profiles** | Expanded and condensed scored separately | Not separated |
| **Current result** | 94 requirements, 189 cases; per-version scores in its README | 104/104 constructs represented; 87 also have a validation rule |
| **Untested items** | Counted in the denominator as `unassessed` — they lower the score | Not applicable; every construct carries a verdict |
| **Best for** | An honest, conservative measure that shows its own gaps | A quick per-construct map from specification area to vocabulary term |

**The one-line version:** `methodology/` is the stricter and more defensible
measure, because it derives its own checklist from the specification and counts
untested requirements against itself. `vcf45-inventory/` is the friendlier map,
because it says construct-by-construct which term represents what.

### Why we keep both

They fail in opposite directions, which is the point of keeping them:

- `vcf45-inventory/` reports **100%**. That number is real but flattering: the
  denominator is a list a maintainer chose, so it cannot reveal something nobody
  thought to add. It is a coverage map, not a search for gaps.
- `methodology/` reports **41–48%** per version. That number is real but harsh:
  it counts every requirement it extracted from the specification, including the
  47 in VCF 4.5 that have no test yet. A requirement with no test scores zero
  even where the vocabulary would obviously handle it.

Reading only the first would overstate the work; reading only the second would
understate it. The honest summary is the pair, with the reason for the gap
stated — which is exactly what each README does.

If you only want one, use `methodology/`. It is the one under active review and
the one whose denominator was not chosen by the people being measured.

## Byte-level checks

The vocabulary deliberately mints no term for VCF's byte-level rules — UTF-8
encoding, no byte order mark, LF or CR+LF line endings. An RDF property claiming
"this file was valid UTF-8" would record an assertion without demonstrating
anything, so these are checked directly on the file bytes instead and reported
separately from either coverage denominator.

Currently **17/17 fixtures** satisfy the VCF 4.5 byte requirements, exercising
both LF and CRLF. Run it with `npm run validate:serialization`; the code is
[`vcf45-inventory/check_serialization.py`](vcf45-inventory/check_serialization.py).

## Running them

From the repository root, with the [local setup](../tests/README.md#local-setup) done:

```sh
npm run coverage:report      # byte checks, then regenerate the inventory report
npm run methodology:check    # recompute the spec-derived assessment; fail if stale
npm run methodology:build    # regenerate it after changing its inputs
npm run methodology:test     # its own regression tests
npm run validate:force       # the complete repository suite
```

Both assessments follow the same rule: **inputs are authored, outputs are
generated.** Edit the inputs and regenerate. Never edit a number in a
`generated/` file — the scripts recompute every total and will disagree with you.

| Directory | Edit by hand? |
| --- | --- |
| `methodology/inputs/`, `methodology/sources/`, `methodology/queries/`, `methodology/fixtures/` | Yes — these carry the judgments and source data |
| `vcf45-inventory/inventory.json` | Yes — the authored inventory and its rubric |
| any `generated/` | No — regenerated from the inputs |

## Where the numbers are used

The vocabulary's [root README](../README.md#what-does-the-coverage-evidence-show)
quotes the headline results. The per-construct and per-requirement evidence stays
here. A synthetic example showing the same record in both sample profiles lives
in [`examples/profile-comparison/`](../examples/profile-comparison/README.md) —
that is an illustration, not an assessment, which is why it is not in this
directory.
