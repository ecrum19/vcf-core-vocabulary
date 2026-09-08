# Mappings to investigate

Alignment targets that were surveyed but **not** asserted. Nothing here is a
commitment; each entry says what the vocabulary is, why it might be worth
aligning against, and what stopped it from being curated now.

Asserted alignments live in
[vcf-core-alignments.sssom.tsv](vcf-core-alignments.sssom.tsv). To promote
something from this file, curate the rows there and run
`npm run mappings:build`.

## Secondary vocabularies

### VariO — Variation Ontology
`http://purl.obolibrary.org/obo/VariO_` · OBO Foundry · actively maintained

Describes the *effects, consequences and mechanisms* of variation in DNA, RNA
and protein. It already touches this repository indirectly: one Med2RDF row
maps `VariO_0001` alongside `SO_0001060`, and GVO cross-references VariO
throughout its class definitions.

**Why not now:** `vcf-core` deliberately stops at the file's logical model and
leaves consequence and interpretation to annotation layers. Aligning against
VariO would mean asserting things about biological effect that a VCF record
does not by itself carry. Worth revisiting only if the vocabulary ever grows an
annotation profile.

### SPHN — Swiss Personalized Health Network
[`biomedit.ch/rdf/sphn-schema/sphn`](https://www.biomedit.ch/rdf/sphn-schema/sphn) · RDF/OWL · reuses SO, GENO, HGNC

A production clinical-genomics schema, and a SWAT4HCLS 2025 BioHackathon
participant. Its genomics concepts arrived in the 2023 release, and it uses
SPARQLing Genomics to get VCF data in.

**Why not now:** the model is framed around clinical records and consent, so the
overlap with a file-format model is thin and mostly mediated by SO and GENO,
which `vcf-core` already aligns against directly. A mapping would likely be a
handful of `skos:relatedMatch` rows carrying little information.

### sparqling-genomics `vcf2rdf`
[UMCUGenetics/sparqling-genomics](https://github.com/UMCUGenetics/sparqling-genomics) · GPL

The closest prior art in intent: a maintained command-line tool that converts
VCF to RDF, with a `VariantCall` class and per-column properties. Conceptually
the nearest neighbour this survey found.

**Why not now:** its vocabulary is defined inside the converter's C source
rather than published as a resolvable ontology document, so there is no stable
IRI to map to and no versioned artifact to pin. Worth revisiting if the project
ever publishes its ontology separately.

### VCF2RDF (Bioinformatics, 2017)
[doi:10.1093/bioinformatics/btw554](https://academic.oup.com/bioinformatics/article/33/4/547/2593587)

The paper that argued for an isomorphic VCF-to-RDF map, and the direct
intellectual predecessor of this vocabulary.

**Why not now:** it describes a mapping approach, not a maintained published
vocabulary. Cite it; there is nothing to align to.

### Wikidata
[w.wiki/DDzd](https://w.wiki/DDzd) · CC0 · a BioHackathon participant

Enormous reach and stable identifiers, and it does carry variant items.

**Why not now:** Wikidata holds instance-level variant data rather than a model
of the VCF format, so the alignment would be between `vcf-core` classes and
Wikidata *properties* used ad hoc across items — a different and much softer
kind of mapping than the rest of this file.

## Deferred within vocabularies already aligned

### GVO complex structural variants
GVO carries eleven complex SV classes drawn from gnomAD-SV — `gvo:DelInv`,
`gvo:DelInvDel`, `gvo:DelInvDup`, `gvo:DupInv`, `gvo:DupInvDel`,
`gvo:DupInvDup`, `gvo:InvDel`, `gvo:InvDup`, `gvo:DDup`, `gvo:DDupIdel`,
`gvo:InsIDel` — that have **no** VCF 4.5 symbolic ALT code.

This is the most interesting open direction. It would let a `vcfc:VariantEvent`
be typed more precisely than the ALT column allows, and precise typing of
complex SVs is the reason GVO was built.

**What is needed:** a decision on whether `vcf-core` should assert
`skos:narrowMatch` from `vcfc:EventType` to classes describing variation the
VCF syntax cannot express. That is a modelling question, not a curation one.

### GVO reference-path bounds
`gvo:lft` and `gvo:rgt` are the leftmost and rightmost positions on a reference
*path*. They superficially resemble `vcfc:ciLower` / `vcfc:ciUpper`.

**Why not now:** they are not the same thing. GVO's are graph-path bounds on a
pangenome reference; `vcf-core`'s are confidence-interval endpoints around an
imprecise breakpoint. Asserting even `skos:relatedMatch` needs someone who knows
GVO's pangenome intent to confirm it.

### The 39 remaining BioHackathon gaps
Of the 47 terms the BioHackathon curators marked `sssom:NoTermFound` against
GA4GH VRS, 8 now have a `vcf-core` counterpart. The other 39 — `med2rdf:Disease`,
`med2rdf:Evidence`, `ggw:VariantEffect`, `ggw:VariantImpact`, `oa:Annotation` and
similar — are annotation, evidence and clinical-interpretation concepts.

**Why not now:** they are outside this vocabulary's scope by design, not by
oversight. They are listed here so the distinction stays deliberate.

## Sources

- VariO — <http://purl.obolibrary.org/obo/vario.owl>
- SPHN RDF Schema — <https://sphn-semantic-framework.readthedocs.io/en/latest/sphn_framework/sphnrdfschema.html>
- sparqling-genomics — <https://github.com/UMCUGenetics/sparqling-genomics>
- GVO ontology — <http://genome-variation.org/resource/gvo.ttl>
- Kawashima, Fujisawa & Katayama, SWAT4HCLS 2023 — <https://ceur-ws.org/Vol-3415/paper-22.pdf>
