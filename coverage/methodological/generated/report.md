# VCF 4.1–4.5 requirement traceability

**Assessment status: review-required.** Generated offline; do not edit.

1024 candidate occurrences form 662 corpus entries. 491 are retained requirements (including unfinished mappings); 133 have reviewed discharge evidence for every applicable version.

An unreviewed entry is **unassessed**, not a demonstrated vocabulary gap. No coverage percentages are calculated.

| VCF | Candidates | Obligation / prohibition candidates | Corpus entries | Reviewed requirements | Discharged | Pending triage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4.1 | 105 | 27 | 169 | 129 | 36 | 0 |
| 4.2 | 110 | 27 | 175 | 134 | 37 | 0 |
| 4.3 | 185 | 64 | 334 | 249 | 77 | 0 |
| 4.4 | 273 | 105 | 441 | 332 | 88 | 0 |
| 4.5 | 351 | 115 | 607 | 448 | 130 | 0 |

Obligation density is sensitive to wording: 4.1/4.2 are more descriptive. The column above is a candidate count, not a comparable denominator.

## Automatically checked reserved-field facts

Literal Number/Type comparisons against the versioned vocabulary artifacts, using independently extracted source rows. Counts include repeated definitions; this checks metadata agreement, not semantic discharge or enforcement.

| VCF | Source rows | Distinct field keys | Exact matches | Missing | Different |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4.1 | 31 | 31 | 31 | 0 | 0 |
| 4.2 | 31 | 31 | 31 | 0 | 0 |
| 4.3 | 69 | 67 | 69 | 0 | 0 |
| 4.4 | 79 | 78 | 79 | 0 | 0 |
| 4.5 | 123 | 122 | 123 | 0 | 0 |

Details: [reserved-definition-comparison.json](reserved-definition-comparison.json).

## Decisions awaiting review

- Triage/classification: 0 entries.
- Mapping: 0 reviewed requirements.
- Alignment: 0 proposed pairs (not accepted automatically).
- Changelog: 0 items; 193 transition observations lack reviewed links.

Read the [assessment and method](../README.md) and [review instructions](../DECISIONS.md). The active judgments are in [decisions.json](../decisions.json). Run `npm run methodological:audit` for optional worksheets, extraction diagnostics and a readable decision register.

## Seed checks from the plans

These are extraction acceptance checks and evidence suggestions. They carry no reviewed coverage credit.

| Seed | VCF 4.5 candidates found | Evidence targets found |
| --- | ---: | ---: |
| CHROM blocks | 1 | 1 |
| Sorted positions (declarative) | 1 | 1 |
| Record ID uniqueness (advisory wording) | 1 | 1 |
| Structured header IDs | 1 | 1 |
| Sample names | 1 | 1 |
| GT first | 1 | 1 |
| PS / PSL exclusion | 1 | 1 |

## Limits

- Candidates are mechanically selected statements, not yet reviewed atomic requirements.
- Modal/declarative sweeps are incomplete; unselected prose and skipped regions remain auditable.
- Earlier specifications use less normative wording. Counts cannot rank versions by coverage.
- Exact text/context grouping is mechanical; fuzzy alignment and semantic applicability require decisions.
- Text absence is not withdrawal, and deprecation is not removal.
- Evidence suggestions are not discharges. Reviewed mappings establish traceability, not rule correctness or conformance.
- This workflow does not execute the vocabulary validators. Run the repository validation suite separately.

## Reproduce

```sh
npm run methodological:build
npm run methodological:check
npm run methodological:test
```

The exact inputs and their SHA-256 hashes are in [provenance.json](provenance.json). Source line anchors refer to [the pinned LaTeX copies](../sources/).
