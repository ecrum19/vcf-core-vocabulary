# VCF Core Vocabulary 2.1.3

A records-only patch release. **No vocabulary term, fixture, query or expected answer
changes**, and no coverage figure moves.

## What changed

82 of the 94 requirement review entries in
`coverage/methodology/inputs/review.json` still carried the placeholder reviewer

```
"Claude Opus 5 - VCF-expert agent review pass (replace with the countersigning human reviewer's name)"
```

The queries and expected answers behind those entries have since been hand-checked, so
the field now names the countersigning human reviewer, as the placeholder itself
instructed. All 94 entries now read `Elias Crum`.

## Why the evidence does not move

`assess.py` excludes `inputs/review.json` from `input_hashes()`, and `reviewed()` tests
only that the `reviewer` field is non-empty rather than inspecting its value. Measured
against 2.1.2:

| | |
| --- | --- |
| Requirement fingerprints | 94/94 unchanged |
| Input hashes and `evidenceFingerprint` | unchanged |
| `generated/summary.json` | byte-identical |

The only generated change is `provenance.json`'s `reviewInputSha256`, the separate hash
of the review file itself, which exists so the review record can change without
disturbing the evidence fingerprint.

The version bump likewise re-opens nothing: `evidence()` blanks `owl:versionInfo` and
`owl:versionIRI` before hashing, so stamping a new release does not invalidate a
recorded review.

## Verification

- `assess.py check --require-reviewed` — 0 human reviews pending
- `npm run validate` — passes
- `npm run methodology:test` — 25 tests pass
