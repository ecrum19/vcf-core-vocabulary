# Coverage assessments

Start here. The repository contains two different assessments; their percentages
have different denominators and must not be combined.

| Assessment | Entry point | What it measures |
| --- | --- | --- |
| Original VCF 4.5 assessment | [curated/README.md](curated/README.md) | **104/104** curated logical-model constructs under its preservation/structure rubric. |
| Methodological VCF 4.1–4.5 assessment | [methodological/README.md](methodological/README.md) | **333/333** extracted Number/Type rows match; **133/491** retained requirements have full evidence under the reviewed criteria. Overall semantic coverage remains undetermined. |
| Paper illustration | [paper/README.md](paper/README.md) | One synthetic VCF record, two RDF representations and reproducible checks. |

## Reproduce

After installing the repository's Node and Python dependencies, from its root:

```sh
npm run methodological:build       # pinned sources + decisions → primary reports
npm run coverage:report          # curated report + source-byte and manuscript checks
npm run coverage:paper           # paper illustration → recorded verification
npm run validate:force           # complete fixture/regression suite + validation stamp
```

`npm run methodological:check` verifies the committed specification-derived reports.
`npm run methodological:review-probes` replays the recorded counterexamples; a
reproduced validator failure is still a finding, not conformance success.

## Files to edit and keep

- **Inputs:** `curated/inventory.json`, `methodological/decisions.json`, the source
  lock and pinned specification copies, and the paper fixtures. These contain
  judgments or source data and cannot be reconstructed from generated reports.
- **Code:** each assessment's scripts and regression tests.
- **Primary outputs:** each `generated/` directory contains reproducible reports.
  Edit the inputs and regenerate; do not edit report counts by hand.
- **Optional audit workspace:** `npm run methodological:audit` generates extraction
  diagnostics, worksheets and a readable decision register in
  `methodological/generated/audit/`. That directory is ignored by Git. Check it
  with `npm run methodological:check -- --audit` and regenerate after changing inputs.

Superseded implementation plans, duplicate coverage checklists, the old alignment
snapshot and one-off assessment reports have been consolidated or removed.
Reviewer history and the six owner-approved policies remain in the active ledger.
`npm run clean` removes optional audit output and build caches while retaining
source inputs, primary reports, installed dependencies and the paper PDF.
