# One record, both sample profiles

This is the smallest complete side-by-side illustration of the vocabulary's two
sample representations. One synthetic VCF record, three samples, two FORMAT keys
(`GT` and `DP`) — represented twice, once in each profile, so you can read the
same data in both shapes and see what changes.

It is an **illustration**, not a coverage assessment and not a benchmark. It says
nothing about runtime, file size, query latency, or any other VCF record.

| File | What it holds |
| --- | --- |
| [synthetic.vcf](synthetic.vcf) | The source: headers and one data row. |
| [expanded.ttl](expanded.ttl) | Expanded profile — an individual `SampleCall` and `FormatFieldValue` per sample. |
| [condensed.ttl](condensed.ttl) | Condensed profile — one `CohortCallMatrix` with a sample-ordered value vector per FORMAT key. |
| [sample-depth.rq](sample-depth.rq) | Expanded-profile query for read depth; the expected answer is `SAMPLE1, 42`. |

## What the comparison shows

The record's three samples carry `0/1:42`, `0/0:18` and `./.:.` — a normal call, a
homozygous reference call, and a wholly missing call.

- **Both profiles recover all six raw FORMAT cells in sample order**, including
  the missing one. Neither profile loses data.
- **They differ in how you reach a value.** The expanded profile gives each
  sample its own resource, so a plain graph pattern finds a depth. The condensed
  profile stores one tab-separated literal per FORMAT key, so you must decode it
  against the ordered `SampleSet` — you need the sample's index to read its cell.
- The supplied graphs contain **172 expanded** and **149 condensed** triples.
  Those counts include shared metadata and optional raw values, so treat them as
  a description of these two files, not as a compression result.

This trade-off is the reason the spec-derived coverage assessment scores the two
profiles separately: the condensed profile is preserving but, by design, not
structurally queryable for per-sample FORMAT values. See
[the coverage assessments](../../coverage/README.md) for what that means for the
reported numbers.

## Verify it

```sh
npm run validate:profiles           # assert the fixtures; fail if the record is stale
npm run validate:profiles:update    # re-record tests/generated/profile-comparison.json
```

[`tests/verify-profile-comparison.mjs`](../../tests/verify-profile-comparison.mjs)
parses both graphs with N3 — deliberately reversing statement order first, since
RDF statement order is not sample order — then checks sample indices, profile
identifiers, FORMAT declarations, typed depths, missing values and recovery of
all six raw cells. Its recorded output is
[`tests/generated/profile-comparison.json`](../../tests/generated/profile-comparison.json).

The SPARQL query is executed separately by `npm run validate:examples`, via
[`examples/manifest.json`](../manifest.json). Both graphs are also covered by the
SHACL suite, because it validates every `.ttl` under `examples/`.
