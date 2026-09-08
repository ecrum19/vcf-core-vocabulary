# Unresolved rows from the BioHackathon spreadsheets

Curation at the SWAT4HCLS 2025 BioHackathon ran out of time before every row
was finished. The rows below carry a subject but no usable predicate/object
pair, so they are not assertions and are not present in the `.sssom.tsv` sets.
They are kept here because they record which terms the curators had queued,
which is useful when the mapping effort is picked up again.

## SemBeacon

From the *SemBeacon SSSOM* sheet, final block:

| subject_id | subject_label | what was recorded | what is missing |
| --- | --- | --- | --- |
| `faldo:location` | — | object cells held `ga4gh:interval` and `ga4gh:start` | no predicate; two candidate objects, no choice made |
| `faldo:begin` | — | nothing | predicate and object |
| `faldo:end` | — | object cell held `ga4gh:end` | no predicate |
| `faldo:position` | — | nothing | predicate and object |
| `geno:0000382` | has variant part | nothing | predicate and object |
| `geno:0000207` | has sequence attribute | nothing | predicate and object |
| `sio:000300` | has value | nothing | predicate and object |

The corresponding Med2RDF rows (`faldo:location` → `vrs:location`,
`faldo:begin` → `vrs:start`, `faldo:end` → `vrs:end`, all `skos:closeMatch` at
confidence 0.8) are complete and were asserted in
[med2rdf-to-vrs.sssom.tsv](med2rdf-to-vrs.sssom.tsv). They are a reasonable
starting point for finishing the SemBeacon block, but the two efforts curated
independently, so they were not copied across.

## Gigwa

The *Gigwa SSSOM* sheet ends with a row carrying only a `mapping_date` and an
`author_id`. It has no subject and is dropped entirely.
