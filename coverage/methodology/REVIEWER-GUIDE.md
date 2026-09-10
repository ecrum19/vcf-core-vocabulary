# Reviewer guide: files, fields and results

How to review the [specification-derived coverage assessment](README.md): what every
file and field means, which ones you edit, and how acceptance is recorded.
Track your progress in the [reviewer checklist](REVIEW-CHECKLIST.md); the previous
pass's findings are in [REVIEW-REPORT.md](REVIEW-REPORT.md).

Scope, axes, denominators, limitations and current results stay in the
[assessment README](README.md) — read that first.

---

**Start with `disposition: "needs-review"` in the source audit. Answer its
`reviewQuestions` in `note`, or report the section ID and your decision.** No
requirement or test is created automatically by a disposition change. Codex can
implement the resulting corrections; human acceptance is recorded separately.

### A. Source audit: what each row means

One row inventories a **source section**, not a test outcome. Its generated
`requirements` now contains **explicit semantic links from the authored
assertions**. The old line-overlap suggestions are retained as `anchorRequirements`;
an overlap alone never establishes that a passage is accounted for.

| Field in [source-audit.json](generated/source-audit.json) | Read it as |
| --- | --- |
| `version`, `start`, `end`, `title`, `zone` | Where to read the corresponding pinned source passage. |
| `assertions[].statement`, `start`, `end`, `requirements` | What information was identified and which registered requirements account for it. Check missing or overbroad interpretations, including examples and changelogs. |
| `assertions[].caseIds`, `testStatus`, `testGap` | Cases specifically checked against that assertion. `targeted-tests` = cases identified; `partial-tests` = some evidence with a stated gap; `no-targeted-test` = no suitable case. These labels do not mean pass/fail. |
| `requirementTests` | All cases registered for each linked requirement **in this version**. Some may not target this particular assertion. Empty `caseIds` explicitly means no registered case. |
| `exclusions`, `reviewQuestions` | Reasons to exclude material and concrete unresolved interpretation/test-oracle questions. |
| `priorAnnotation` | Your annotation before this agent audit, preserved verbatim when one existed. |
| `disposition`, `note`, `relatedRequirements` | **The only fields you edit here.** Supply your decision/rationale and any additional existing requirement IDs. |

Original annotations also remain in
`inputs/review.json.sourceSectionsBeforeAssertionAudit`; they were not converted
into human acceptance. New annotations are saved under `sourceSections`.

**FILTER example:** section `4.1:74-80` now links R51 and the relevant record-code
requirement. Its declaration case checks `q10 → Quality below ten` and
`s50 → Sample threshold`; a separate query follows failed record codes to those
file-local declarations. Both are registered cases, with outcomes in the results.

### B. Remaining files, fields and results

| File / scope | Required judgment |
| --- | --- |
| This README | Are the scope, axes, denominator and limits appropriate for the intended claim? |
| [requirements.json](inputs/requirements.json): every requirement | Check `question`, `interpretation`, `testPlan` where present, `versions`, `anchors.{version}.start/end`, and `area`. Are capability and version scope faithful to the source? Report additions/splits/anchor corrections by ID; keep existing IDs stable. |
| [cases.json](inputs/cases.json): every case | Check `requirement`, `version`, `fixture`, `note`, and each axis/profile's `query` and `expected`. Read the relevant VCF records, query and RDF triples. Does the expected answer follow from the source/question? Reused query code needs reading once, but each case's expected answers/version need checking. |
| [declarations.json](generated/declarations.json) | Check `version`, `line`, `kind`, `key`, `number`, `type` against reserved definitions, and `artifact`/`identifierProperty` against the proper version. Check extraction omissions too. `status`/`actual` report literal comparisons; do not edit generated answers. |
| [results.json](generated/results.json) | Join `requirements[].requirement` and `queries[].case` to input IDs. Inspect every applicable version/profile, both axes, `status`, `expected`, `actual`, `query`, `witness`, and controls. Check meaningful passes as well as failures. `review: pending` is not a failed test. |
| [summary.json](generated/summary.json) | Inspect `byVersion` denominators, axis counts, `percentDemonstrated`, `sourceAssertions`, `declarations`, `sourceAuditAccepted`, and `pendingReviews`. Arithmetic is automated; judge whether the scope and limitations support the claims. |

Within `expected`, outer arrays are answer rows; columns follow SPARQL `SELECT`.
Row order is ignored; duplicate rows count. JSON `null` means unbound;
`"."` is the VCF missing-value token. Never change expected answers merely to
match execution.

Prioritize the flagged source conflicts, assertions with test gaps, requirements
without cases, and condensed structural failures (including R18–R21, R27–R30 and R60
in VCF 4.5). A missing test requires implementation or an acknowledged limitation.
A challenging interpretation remains `needs-review` until its question is resolved.
You do not have to make every test pass to accept an accurate assessment.

### C. Dispositions and recording acceptance

| Disposition | Meaning |
| --- | --- |
| `pending` | Passage not reviewed. |
| `mapped` | All identified in-scope information is linked to requirements; this does not mean tests pass or even exist. |
| `needs-requirement` | A requirement needs adding, splitting or correcting. |
| `needs-review` | Source meaning, scope or a defensible expected-answer test needs your judgment. Read `reviewQuestions`. |
| `duplicate` | Adds nothing beyond the linked requirements; identify them. |
| `context-only` | Heading/background with no information capability. |
| `out-of-scope` | Entire passage concerns excluded matters; explain why. |
| `needs-clarification` | Older equivalent label for an unresolved question; prefer `needs-review`. |

Use one label and a short `note`. For mixed passages, retain the in-scope
assertions; an example is not automatically excluded. Additional links go in
`relatedRequirements`, not the generated `requirements` field.

Save annotations **before** changing requirements, cases or the assertion input:

```sh
.venv/bin/python coverage/methodology/scripts/assess.py save-source-review
npm run methodology:build
```

Rebuilding refuses unsaved review annotations. Changes to authored assertions
belong in `inputs/source-assertions.json`. Questions there must be resolved before
source acceptance; changing a disposition alone cannot close them.

After corrections and a rebuild, record acceptance in [review.json](inputs/review.json):

| Entry | What acceptance covers |
| --- | --- |
| `sourceAudit` | All source passages, assertion mappings, exclusions and reserved-declaration extraction; no unresolved questions/dispositions. |
| `requirements.<ID>` | That requirement's interpretation, all applicable versions, cases/results and acknowledged test gaps. Untested versions may remain unassessed. |

Each entry requires **`fingerprint`** (current matching ID in the
[review queue](generated/review-queue.json)), **`reviewer`** (your name),
**`date`** (`YYYY-MM-DD`), and **`rationale`** (what you checked and any limitation
you accept). Copying a fingerprint alone is not a review. Do not edit the queue,
generated results, hashes or totals. Scripts/tests/provenance are supporting
machinery, not additional mandatory line-by-line reviews.
