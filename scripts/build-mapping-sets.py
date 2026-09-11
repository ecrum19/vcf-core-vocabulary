#!/usr/bin/env python3
"""Build and validate the mapping sets under ``mappings/``.

Three kinds of artifact live there:

``mappings/vcf-core-alignments.sssom.tsv``
    Authored. The single curated record of every alignment ``vcf-core`` asserts
    against an external vocabulary. Source of truth; edit this by hand.

``mappings/vcf-core-alignments.ttl``
    Generated from that TSV. The deployable alignment module: it declares its
    own ontology IRI, imports ``vcf-core`` and is *not* imported back, so the
    core vocabulary stays free of outward commitments a consumer may not want.

``mappings/bh25/*.sssom.tsv``
    Authored. Transcriptions of the SWAT4HCLS 2025 BioHackathon spreadsheets,
    recording what *other* projects asserted about their own terms. Validated,
    never rewritten, and deliberately not folded into the alignment module.

The build also enforces one invariant: every ``skos:*Match`` asserted inline in
``ontology/*.ttl`` must appear in the curated set. The alignment module is a
superset of the core's own axioms, so the two can never silently disagree.

  --check   exit 1 if the module is stale, the invariant is broken, or any set
            fails validation
  (default) regenerate the module, then run the same checks
"""
from __future__ import annotations

import argparse
import pathlib
import sys

from rdflib import Graph, URIRef
from rdflib.namespace import SKOS

ROOT = pathlib.Path(__file__).resolve().parent.parent
ONTOLOGY = ROOT / "ontology"
MAPPINGS = ROOT / "mappings"
CURATED = MAPPINGS / "vcf-core-alignments.sssom.tsv"
MODULE = MAPPINGS / "vcf-core-alignments.ttl"
BUNDLE = "vcf-core-vocabulary.bundle.ttl"

REQUIRED = {"subject_id", "predicate_id", "object_id", "mapping_justification"}
PREDICATES = {f"skos:{p}" for p in
              ("exactMatch", "closeMatch", "broadMatch", "narrowMatch", "relatedMatch")}
CORE_NOTE = "Also asserted inline in the vcf-core ontology modules."

# Order the alignment module groups its mappings by, and the heading each gets.
TARGETS = [
    ("vrs", "GA4GH Variation Representation Specification 2.0"),
    ("hero", "HERO, the Hereditary Ontology for Genomics Data"),
    ("gvo", "GVO, the Genome Variation Ontology"),
    ("gfvo", "GFVO, the Genomic Feature and Variation Ontology"),
    ("med2rdf", "Med2RDF"),
    ("so", "Sequence Ontology"),
    ("geno", "GENO, the Genotype Ontology"),
    ("chebi", "ChEBI"),
    ("faldo", "FALDO"),
    ("sio", "SIO, the Semanticscience Integrated Ontology"),
]


# --------------------------------------------------------------------------
# reading


def read_set(path: pathlib.Path) -> tuple[dict[str, str], dict[str, object], list[dict[str, str]]]:
    """Split an SSSOM TSV into its curie_map, its other metadata, and its rows.

    The metadata block is commented YAML. Values are returned as strings, or as
    lists of strings for the multivalued slots written as ``- item`` lines.
    """
    prefixes: dict[str, str] = {}
    metadata: dict[str, object] = {}
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    in_curie_map = False
    pending_list: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            body = line[1:]
            stripped = body.strip()
            if stripped == "curie_map:":
                in_curie_map, pending_list = True, None
            elif in_curie_map and body.startswith("   "):
                prefix, _, iri = stripped.partition(": ")
                prefixes[prefix] = iri
            elif pending_list and stripped.startswith("- "):
                metadata[pending_list].append(stripped[2:])
            else:
                in_curie_map, pending_list = False, None
                key, _, value = stripped.partition(": ")
                if value:
                    metadata[key] = value
                elif key.endswith(":"):
                    pending_list = key[:-1]
                    metadata[pending_list] = []
            continue
        if header is None:
            header = line.split("\t")
            continue
        rows.append(dict(zip(header, line.split("\t"))))
    return prefixes, metadata, rows


def mapping_sets() -> list[pathlib.Path]:
    return sorted(MAPPINGS.rglob("*.sssom.tsv"))


def ontology_axioms(prefixes: dict[str, str]) -> set[tuple[str, str, str]]:
    """The skos:*Match triples asserted inline in the ontology modules."""
    graph = Graph()
    for module in sorted(ONTOLOGY.glob("*.ttl")):
        if module.name != BUNDLE:
            graph.parse(module, format="turtle")

    def shorten(iri: str) -> str:
        best = None
        for prefix, namespace in prefixes.items():
            if iri.startswith(namespace) and (best is None or len(namespace) > len(best[1])):
                best = (prefix, namespace)
        return f"{best[0]}:{iri[len(best[1]):]}" if best else iri

    found = set()
    for predicate in ("exactMatch", "closeMatch", "broadMatch", "narrowMatch", "relatedMatch"):
        for subject, _, obj in graph.triples((None, getattr(SKOS, predicate), None)):
            if isinstance(subject, URIRef) and isinstance(obj, URIRef):
                found.add((shorten(str(subject)), f"skos:{predicate}", shorten(str(obj))))
    return found


# --------------------------------------------------------------------------
# generating the alignment module


def escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def curation_date(rows: list[dict[str, str]]) -> str:
    """The newest curated mapping_date in the set.

    dct:modified has to come from the curated data rather than the clock. Stamping
    date.today() made the generated module differ from the committed one on every
    day after it was built, so the staleness check in tests/test_mappings.py failed
    for a reason that had nothing to do with the mappings.
    """
    dates = sorted(d for d in (r.get("mapping_date", "").strip() for r in rows) if d)
    if not dates:
        raise SystemExit("no mapping_date in the set; cannot stamp dct:modified")
    return dates[-1]


def render_module(prefixes: dict[str, str], metadata: dict[str, str],
                  rows: list[dict[str, str]]) -> str:
    version = metadata.get("subject_source_version", "0.0.0")
    used = sorted({r["subject_id"].split(":", 1)[0] for r in rows} |
                  {r["object_id"].split(":", 1)[0] for r in rows} |
                  {"vcfc", "owl", "rdfs", "dct", "skos", "sssom", "semapv"})

    lines = [
        "#################################################################",
        "# VCF Core Vocabulary -- external alignments",
        "#",
        "# Generated by scripts/build-mapping-sets.py from",
        "# mappings/vcf-core-alignments.sssom.tsv. Do not edit by hand: curate",
        "# the SSSOM file and rebuild with `npm run mappings:build`.",
        "#",
        "# This module is NOT imported by the core vocabulary. Load it only if",
        "# you want vcf-core's outward alignments; the core stays usable without",
        "# committing to any external model.",
        "#################################################################",
        "",
    ]
    standard = {
        "owl": "http://www.w3.org/2002/07/owl#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "dct": "http://purl.org/dc/terms/",
    }
    for prefix in used:
        iri = prefixes.get(prefix) or standard.get(prefix)
        if iri:
            lines.append(f"@prefix {prefix + ':':9} <{iri}> .")
    lines.append("")

    lines += [
        "<https://w3id.org/vcf-core/alignments> a owl:Ontology ;",
        '  rdfs:label "VCF Core Vocabulary: external alignments"@en ;',
        f'  dct:description "{escape(metadata.get("mapping_set_description", ""))}"@en ;',
        "  dct:license <https://creativecommons.org/licenses/by/4.0/> ;",
        f'  dct:modified "{curation_date(rows)}"^^<http://www.w3.org/2001/XMLSchema#date> ;',
        f"  owl:versionIRI <https://w3id.org/vcf-core/alignments/{version}> ;",
        f'  owl:versionInfo "{version}" ;',
        "  owl:imports <https://w3id.org/vcf-core/vocab> ;",
        "  dct:source <https://w3id.org/vcf-core/mappings/vcf-core-alignments.sssom.tsv> ;",
        "  rdfs:seeAlso <https://mapping-commons.github.io/sssom/> .",
        "",
    ]

    # Mappings, grouped by target vocabulary then by subject, so the file reads
    # as "what do we say about VRS", not as a flat dump.
    by_target: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_target.setdefault(row["object_id"].split(":", 1)[0], []).append(row)

    ordered = [t for t, _ in TARGETS if t in by_target]
    ordered += sorted(t for t in by_target if t not in dict(TARGETS))

    annotated: list[dict[str, str]] = []
    for target in ordered:
        heading = dict(TARGETS).get(target, target)
        lines += ["#" * 65, f"# {heading}", "#" * 65, ""]
        by_subject: dict[str, list[dict[str, str]]] = {}
        for row in by_target[target]:
            by_subject.setdefault(row["subject_id"], []).append(row)
        for subject in sorted(by_subject):
            statements = []
            for row in sorted(by_subject[subject], key=lambda r: (r["predicate_id"], r["object_id"])):
                statements.append(f'{row["predicate_id"]} {row["object_id"]}')
                if row.get("confidence") or row.get("comment"):
                    annotated.append(row)
            lines.append(f"{subject} {' ;\n  '.join(statements)} .")
        lines.append("")

    if annotated:
        lines += ["#" * 65,
                  "# Per-mapping provenance",
                  "#",
                  "# Confidence and curation notes, reified so a consumer can filter on",
                  "# them without leaving RDF. The SSSOM file carries the same values.",
                  "#" * 65,
                  ""]
        for row in annotated:
            lines.append("[] a owl:Axiom ;")
            lines.append(f'  owl:annotatedSource {row["subject_id"]} ;')
            lines.append(f'  owl:annotatedProperty {row["predicate_id"]} ;')
            lines.append(f'  owl:annotatedTarget {row["object_id"]} ;')
            lines.append(f'  sssom:mapping_justification {row["mapping_justification"]} ;')
            if row.get("confidence"):
                lines.append(f'  sssom:confidence {row["confidence"]} ;')
            if row.get("comment"):
                lines.append(f'  rdfs:comment "{escape(row["comment"])}"@en ;')
            lines[-1] = lines[-1][:-2] + " ."
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# --------------------------------------------------------------------------
# validating


def validate(path: pathlib.Path) -> list[str]:
    prefixes, _, rows = read_set(path)
    name = path.relative_to(ROOT)
    problems = []
    if not prefixes:
        problems.append(f"{name}: no curie_map in the metadata block")
    if not rows:
        problems.append(f"{name}: no mappings")
    seen = set()
    for index, row in enumerate(rows, start=1):
        where = f"{name}:{index}"
        missing = [c for c in REQUIRED if not row.get(c)]
        if missing:
            problems.append(f"{where}: empty required column(s) {', '.join(sorted(missing))}")
        predicate = row.get("predicate_id", "")
        if predicate and predicate not in PREDICATES:
            problems.append(f"{where}: unexpected predicate_id {predicate!r}")
        triple = (row.get("subject_id"), predicate, row.get("object_id"))
        if row.get("object_id") != "sssom:NoTermFound":
            if triple in seen:
                problems.append(f"{where}: duplicate mapping {triple[0]} {triple[1]} {triple[2]}")
            seen.add(triple)
        for column in ("subject_id", "object_id"):
            value = row.get(column, "")
            if value and ":" in value and not value.startswith("http"):
                prefix = value.split(":", 1)[0]
                if prefix not in prefixes:
                    problems.append(f"{where}: {column} prefix {prefix!r} is not in the curie_map")
        confidence = row.get("confidence", "")
        if confidence:
            try:
                if not 0.0 <= float(confidence) <= 1.0:
                    problems.append(f"{where}: confidence {confidence!r} outside 0..1")
            except ValueError:
                problems.append(f"{where}: confidence {confidence!r} is not a number")
        date = row.get("mapping_date", "")
        if date and (len(date) != 10 or date[4] != "-" or date[7] != "-"):
            problems.append(f"{where}: mapping_date {date!r} is not ISO 8601 (YYYY-MM-DD)")
    return problems


def check_superset() -> list[str]:
    """The curated set must cover every alignment the ontology asserts inline."""
    prefixes, _, rows = read_set(CURATED)
    curated = {(r["subject_id"], r["predicate_id"], r["object_id"]) for r in rows}
    flagged = {(r["subject_id"], r["predicate_id"], r["object_id"])
               for r in rows if r.get("comment") == CORE_NOTE}
    inline = ontology_axioms(prefixes)

    problems = []
    for triple in sorted(inline - curated):
        problems.append("ontology asserts a mapping the curated set is missing: "
                        f"{triple[0]} {triple[1]} {triple[2]}")
    for triple in sorted(inline - flagged):
        if triple in curated:
            problems.append(f"curated row {triple[0]} {triple[1]} {triple[2]} is asserted "
                            f"inline in the ontology but not marked with the core note")
    for triple in sorted(flagged - inline):
        problems.append(f"curated row {triple[0]} {triple[1]} {triple[2]} claims to be "
                        f"asserted inline in the ontology, but is not")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail instead of rewriting the alignment module")
    args = parser.parse_args()

    prefixes, metadata, rows = read_set(CURATED)
    rendered = render_module(prefixes, metadata, rows)
    current = MODULE.read_text(encoding="utf-8") if MODULE.is_file() else None
    problems = []
    if args.check:
        if current != rendered:
            problems.append(f"{MODULE.relative_to(ROOT)} is stale; "
                            f"run npm run mappings:build")
    elif current != rendered:
        MODULE.write_text(rendered, encoding="utf-8")
        print(f"wrote {MODULE.relative_to(ROOT)}")

    # Every check runs even when an earlier one failed, so one rebuild fixes
    # everything the report names rather than uncovering the next problem.
    problems += [p for path in mapping_sets() for p in validate(path)]
    problems += check_superset()
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        return 1

    Graph().parse(MODULE, format="turtle")
    total = sum(len(read_set(p)[2]) for p in mapping_sets())
    core = sum(1 for r in rows if r.get("comment") == CORE_NOTE)
    print(f"{len(mapping_sets())} mapping sets, {total} mappings, all valid")
    print(f"alignment module: {len(rows)} mappings ({core} also inline in the ontology, "
          f"{len(rows) - core} module-only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
