# Reproducible paper illustration

These authored fixtures support the [SWAT4HCLS manuscript](../../SWAT4HCLS_2027/main.tex).
They contain one synthetic VCF record, GT and DP, and three samples. This is a
bounded representation example, not a converter evaluation or storage benchmark.

| File | Role |
| --- | --- |
| [synthetic.vcf](synthetic.vcf) | Source row and headers. |
| [expanded.ttl](expanded.ttl) | Individual sample calls and FORMAT values. |
| [condensed.ttl](condensed.ttl) | A cohort matrix and sample-ordered value vectors. |
| [sample-depth.rq](sample-depth.rq) | Expanded-profile SPARQL query; expected answer is SAMPLE1, 42. |
| [verify.mjs](verify.mjs) | Node/N3 assertions and deterministic result writer. |
| [generated/verification.json](generated/verification.json) | Recorded Node assertions; checked by `--check`. |
| [check_figures.py](check_figures.py) | Compares manuscript figures with the curated report. |

From the repository root, with its existing dependencies installed:

```sh
npm run coverage:paper               # regenerate Node results
npm run coverage:paper -- --check    # execute and compare without rewriting
npm run validate:examples            # reconstruct VCF lines and execute SPARQL
npm run validate:shacl               # complete SHACL and decoded-value checks
npm run coverage:report              # curated counts and manuscript figures
```

The Node script reverses parsed RDF statement order, then checks sample indices,
profile identifiers, declarations, dimensions, typed depths, missing values and
recovery of all six raw FORMAT cells. Both representations recover `0/1:42`,
`0/0:18`, and `./.:.` in sample order. It also checks the decoded depth predicate;
the separate SPARQL query is executed by `validate:examples`, not by Node.

The supplied graphs contain 172 expanded and 149 condensed triples. Their
sample-specific resources number nine and three respectively; shared metadata
and optional raw values are included in the triple counts. These counts say
nothing about runtime, compressed size, memory, query latency or other VCF records.
Full-validator results are in [tests/generated/validation.json](../../tests/generated/validation.json).
