# Recording and reviewing assessment decisions

The [assessment overview](README.md) records decisions and findings.
Run `npm run methodological:audit` to generate the optional readable register
(`generated/audit/reviewed-decisions.md`) and worksheets. The primary
`generated/changelog-reconciliation.json` records unfinished source reconciliation.
The instructions below also apply to continuing and amending that assessment.
Record decisions in [decisions.json](decisions.json). Generated suggestions are only
review aids. Every decision needs a named `reviewer` and a nonempty `reason`.
Use your own identity for your decisions, and preserve earlier reviewers' names.

The repository owner has agreed to the six methodological choices recorded in
`assessmentPolicy`, including a qualification about complex semantic concepts.
Each policy records its author, response, rationale and scope. These agreements
do **not** approve every mapping or establish corpus completeness. A `secondReview`
annotation identifies any narrower interpretation confirmed on a specific entry;
`reviewHistory` preserves earlier judgments. `reviewBasis` distinguishes observed
evidence from interpretive adequacy judgments in the readable register.

## Suggested first assessment session

1. Generate the audit workspace and open `generated/audit/seed-review.md`, which
   collects the source statements, IDs, versions, suggested rules, fingerprints,
   and specific assessment points. Use [the corpus](generated/corpus.json) and
   [the evidence catalogue](generated/evidence-catalogue.json) for the full detail.
2. Decide the requirement's granularity, kind, and strength. For example, the
   record-identifier uniqueness sentence uses **should**, despite the plan's
   description as normative. Decide how advice is to be discussed; the extraction
   preserves that wording. Sample-ID uniqueness and sample-index uniqueness also
   should not be conflated just because a single SHACL message mentions both.
3. Review the **4.4 → 4.5 changelog** before trusting large-scale alignment.
   In particular, compare Number=P in the maintained 4.4 source with its mention
   in the 4.5 transition list and the erratum. A textual mismatch may reflect
   revision history, not a missing vocabulary capability.
4. Resolve alignment pairs, then triage the remaining union. Check unselected
   `proseAudit` blocks, especially early-version field definitions. Add anything
   missed with source anchors, without pretending it came from a mechanical sweep.
5. Map evidence and review version applicability. Missing or partial mappings are
   results worth publishing, provided they are assessed and explained.

## Triage and map one entry

Generate a copyable starter using an actual ID from the corpus:

```sh
.venv/bin/python coverage/methodological/workflow.py review-template --id REQ-bbd9462b0b2cdc864e83
```

Paste the resulting entry into the ledger's `triage` object. Fill in the reviewer
and rationale; choose `representational`, `validity`, `serialization`, `processing`,
or `bcf`. The suggested kind is a heuristic and has no authority.

A decision has this form (the fingerprint must be copied from the **current**
catalogue; the placeholders below are intentionally not valid evidence):

```json
{
  "status": "requirement",
  "kind": "validity",
  "reviewer": "YOUR NAME",
  "reason": "Explain the atomic obligation and why this is the appropriate kind.",
  "owner": "YOUR NAME",
  "mappingComplete": true,
  "evidence": [
    {
      "target": "EXACT ID FROM evidence-catalogue.json",
      "fingerprint": "EXACT fingerprint FROM THAT TARGET",
      "role": "enforcement",
      "assessment": "full",
      "versions": ["4.1", "4.2", "4.3", "4.4", "4.5"],
      "reason": "Explain why this rule fully checks this obligation in these versions, including graph prerequisites."
    }
  ]
}
```

Use only versions present in the corpus entry and supported by the target.
Multiple overlays can collectively discharge one shared requirement. Use
`assessment: "partial"` when a target addresses only part of an obligation.
For targets with unknown version scope, also provide evidence-level `scopeReason`
based on actual code inspection. This is not a way to override a known conflicting
version gate. A different ledger entry or explicit source/code improvement may
be needed if the catalogue cannot support a proposed claim.

Leave `mappingComplete: false` while the evidence search is unfinished. Set it
to true with `evidence: []` only after reviewing the requirement and concluding
that no relevant mapping exists. The rationale should describe that search.
A complete mapping assessment need not find full coverage.

Other triage statuses:

| Status | Additional fields and meaning |
| --- | --- |
| `not-a-requirement` | `reason` explains the false positive; the candidate remains in the register. |
| `excluded` | `kind` and `scopeReason` explain a scope decision. Typical examples are processing and BCF; no discharge credit. |
| `duplicate-of` | `target` is a retained, already triaged requirement covering every source version; no duplicate chains. Use alignment for version-spanning restatements. |
| `split-into` | `children` lists two or more manually defined entries; their `manualRequirements` records name this entry as `parent`. Every version must survive the split. |

Optional `lifecycle` entries use `version`, `state` (`deprecated` or `withdrawn`),
and `reason`. These annotate a reviewed interpretation; they do not erase source
occurrences or change applicability by themselves. If a grouped sentence's
semantics actually differ by version, align/split and explain the distinction.

## Align or distinguish two known statements

Add to `alignments`:

```json
{
  "source": "REQ-ID-TO-MERGE",
  "target": "REQ-ID-TO-KEEP",
  "relation": "same",
  "reviewer": "YOUR NAME",
  "reason": "Explain why the two texts express the same requirement despite the wording change."
}
```

`relation: "different"` suppresses a reviewed false match. Merges are applied in
ledger order. The target ID survives and the source becomes an alias. Source
occurrences are never discarded. Review decisions must use surviving IDs; moving
a triage decision after a merge is an explicit edit, not an automatic transfer
of an old verdict to a broader requirement. Exact-text grouping is provisional:
if identical wording has different semantics, use a reviewed split by version.

## Add a missed requirement or split a compound statement

Append to `manualRequirements`:

```json
{
  "id": "MAN-descriptive-permanent-id",
  "text": "An atomic requirement, with its meaning grounded in the cited source.",
  "versions": ["4.5"],
  "anchors": [
    {
      "version": "4.5",
      "sha256": "37f13e0d2e8e741ea8505b0342b6e6034637a1f476eeb3af1b8acc25d70246c5",
      "lineStart": 1,
      "lineEnd": 1
    }
  ],
  "reviewer": "YOUR NAME",
  "reason": "Explain the extraction miss or the split. Replace the illustrative line range with the actual source location."
}
```

Each applicable version needs an anchor to its actual pinned source. For split
children, add `parent: "REQ-parent-id"`, and triage every child separately. A
manual entry alone is not an accepted coverage verdict. Its ID remains permanent;
do not renumber existing manual entries when inserting a new one.

## Reconcile the independent changelog

Use an exact `CHANGE-…` ID as a key in `changelog`:

```json
{
  "status": "linked",
  "requirements": ["REQ-surviving-id"],
  "reviewer": "YOUR NAME",
  "reason": "Explain which source change these requirements account for.",
  "disagreementReason": "Required when none of these entries changes in the derived transition; explain errata, unchanged wording, or an extraction limitation."
}
```

Other statuses are `out-of-scope` (for example, binary-only changes), `editorial`,
and `unresolved`. Mixed VCF/BCF bullets require a reason accounting for the whole
item; do not silently discard the VCF part. `unresolved` stays in the review queue.

For a derived change with no matching changelog item, add a `transitions` entry
keyed by `FROM->TO:REQ-id`, for example `4.4->4.5:REQ-surviving-id`:

```json
{
  "status": "specification-omission",
  "reviewer": "YOUR NAME",
  "reason": "The observed source change is real, but no corresponding changelog item was located."
}
```

Other transition-note statuses are `editorial`, `alignment-artifact`,
`extraction-limit`, and `out-of-scope`. Fix extraction/alignment when appropriate;
an explanation is not a substitute for fixing a known parser bug. Rewordings and
absent statements are not automatically semantic introductions or withdrawals.

## Validate a review batch

```sh
npm run methodological:build
npm run methodological:check
npm run methodological:test
git diff -- coverage/methodological
```

Review the ledger and generated diffs together. If a reviewed target changed,
inspect it and reassess the claim before updating its fingerprint. Run positive
and negative vocabulary validation evidence when confirming enforcement; this
workflow does not execute those checks or infer correctness from a passing build.

When all recorded assessment work is complete, `check --require-reviewed` exits
successfully. This includes explanations for both directions of the changelog
comparison. Publishing “complete coverage” would require a separate defensible
interpretation of the remaining limitations and any assessed gaps.
