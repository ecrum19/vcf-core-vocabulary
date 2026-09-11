#!/usr/bin/env python3
"""Reproduce a requirements-to-query assessment; never infer semantic review.

Build writes deterministic evidence and the README result block. Check recomputes
without writing. A failed witness is an assessment result, not a workflow error;
bad inputs, undeclared RDF terms, stale output, and uninformative tests are errors.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

import rdflib
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF, OWL

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from vcf_examples import materialize
from source import sha, declarations
from source_review import make_audit, resolved, save_annotations, unsaved

V = Namespace("https://w3id.org/vcf-core/vocab#")
PROFILES = ("expanded", "condensed")
AXES = ("preservation", "structure")


def encoded(value):
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def fingerprint(value):
    return sha(encoded(value).encode())


def status(results):
    """No fractional credit and no dropping untested components from a denominator."""
    if not results or all(x == "unassessed" for x in results):
        return "unassessed"
    if all(x == "pass" for x in results):
        return "demonstrated"
    return "partial" if "pass" in results else "not-demonstrated"


def answers(graph, query):
    # Compare bags, not sets: extra rows and duplicate answers also fail the case.
    return sorted([[str(v) if v is not None else None for v in row] for row in graph.query(query)], key=encoded)


def run_query(graph, query, expected, axis):
    if not expected:
        raise ValueError("A positive witness must have a nonempty independent expected answer")
    if axis == "structure" and re.search(r"\b(REPLACE|SUBSTR|STRBEFORE|STRAFTER)\s*\(", query, re.I):
        raise ValueError("A structural query cannot decode compound VCF literals")
    target = sorted(expected, key=encoded)
    if answers(Graph(), query) == target:
        raise ValueError("Query gives its expected answer without data")
    actual = answers(graph, query)
    passed = actual == target
    # Remove each used predicate in turn. At least one deletion must change a
    # passing answer. This checks data dependence; it is not a semantic proof.
    sensitive = []
    if passed:
        for predicate in sorted(set(graph.predicates()), key=str):
            if str(predicate).startswith(str(V)) and re.search(r"vcfc:"+re.escape(str(predicate)[len(str(V)):])+r"\b", query):
                reduced = Graph()
                for s, p, o in graph:
                    if p != predicate:
                        reduced.add((s, p, o))
                if answers(reduced, query) != target:
                    sensitive.append(str(predicate))
                    break
        if not sensitive:
            raise ValueError("Passing query has no effective vocabulary-predicate deletion control")
    return {"status": "pass" if passed else "fail", "actual": actual, "expected": target,
            "emptyGraphRejected": True, "predicateDeletionRejected": sensitive}


def evidence(path):
    """Hash what a file asserts, not the release it was stamped with.

    A version bump rewrites owl:versionInfo and owl:versionIRI in every ontology
    module. That changes no term, no fixture and no expected answer, so it must
    not re-open a recorded review. Only the stamped value is blanked; the triple
    stays, and every other byte of the file still counts. The VCF specification
    version a registry describes is a different property and is untouched.
    """
    data = path.read_bytes()
    if path.suffix != ".ttl":
        return data
    data = re.sub(rb'owl:versionInfo\s+"[^"]*"', b'owl:versionInfo ""', data)
    return re.sub(rb"owl:versionIRI\s+<[^>]*>", b"owl:versionIRI <>", data)


def input_hashes():
    """Conservative provenance: changing any normative module or converter helper
    invalidates every semantic review. Generated outputs never hash themselves."""
    paths = set(HERE.glob("sources/*")) | set(HERE.glob("scripts/*.py")) | set(HERE.glob("queries/*.rq")) | set(HERE.glob("fixtures/*"))
    paths |= {HERE/"sources.lock.json", HERE/"requirements.txt"}
    paths |= {p for p in HERE.glob("inputs/*.json") if p.name != "review.json"}
    paths |= set(ROOT.glob("ontology/*.ttl")) | set(ROOT.glob("ontology/versions/*"))
    paths |= {ROOT/"scripts/vcf_examples.py", ROOT/"scripts/version_registry.py"}
    paths = {p for p in paths if p.is_file() and not p.name.endswith(".bundle.ttl")}
    return {p.relative_to(ROOT).as_posix(): sha(evidence(p)) for p in sorted(paths)}


def reviewed(entry, digest):
    return bool(entry and entry.get("fingerprint") == digest and
                all(entry.get(k) for k in ("reviewer", "date", "rationale")))


def load_sources():
    lock = json.loads((HERE / "sources.lock.json").read_text())
    source_text = {}
    for version, pin in lock["versions"].items():
        data = (HERE / pin["file"]).read_bytes()
        assert sha(data) == pin["sha256"], f"Source pin mismatch: {version}"
        source_text[version] = data.decode("utf-8")
    return lock, source_text


def source_audit(source_text, requirements, review, cases):
    """Use authored semantic mappings, with live checks against the case register."""
    inventory = json.loads((HERE / "inputs/source-assertions.json").read_text())
    return make_audit(source_text, requirements, review.get("sourceSections", {}),
                      inventory["sections"], cases, review.get("sourceSectionsBeforeAssertionAudit", {}))


def save_source_review():
    """Save worksheet annotations without accepting the overall source audit."""
    _, source_text = load_sources()
    requirements = json.loads((HERE / "inputs/requirements.json").read_text())
    path = HERE / "inputs/review.json"
    review = json.loads(path.read_text())
    worksheet_path = HERE / "generated/source-audit.json"
    worksheet = json.loads(worksheet_path.read_text())
    cases = json.loads((HERE / "inputs/cases.json").read_text())
    current = source_audit(source_text, requirements, review, cases)
    changed = len(unsaved(worksheet))
    review = save_annotations(worksheet, current, review)
    # Validate before either write, including requirement links supplied by hand.
    updated = source_audit(source_text, requirements, review, cases)
    path.write_text(encoded(review))
    worksheet_path.write_text(encoded(updated))
    print(f"Saved {changed} source-section annotations; no review accepted. Run methodology:build next.")


def evaluate():
    lock, source_text = load_sources()
    requirements = json.loads((HERE / "inputs/requirements.json").read_text())
    cases = json.loads((HERE / "inputs/cases.json").read_text())
    review = json.loads((HERE / "inputs/review.json").read_text())
    ids = [r["id"] for r in requirements]
    assert len(ids) == len(set(ids)), "Duplicate requirement ID"
    assert len(cases) == len({c["id"] for c in cases}), "Duplicate case ID"
    for r in requirements:
        assert r["versions"] and set(r["versions"]) == set(r["anchors"]), r["id"]
        for version, a in r["anchors"].items():
            lines = source_text[version].splitlines()
            assert 1 <= a["start"] <= a["end"] <= len(lines), r["id"]
            assert sha("\n".join(lines[a["start"]-1:a["end"]]).encode()) == a["sha256"], f"Anchor changed: {r['id']} {version}"
    case_by_req = {rid: [] for rid in ids}
    for c in cases:
        assert c["requirement"] in ids, c["id"]
        req = requirements[ids.index(c["requirement"])]
        assert c["version"] in req["versions"], f"Wrong-version evidence: {c['id']}"
        fixture = HERE / c["fixture"]
        assert fixture.read_text().splitlines()[0] == "##fileformat=VCFv"+c["version"], c["id"]
        case_by_req[c["requirement"]].append(c)

    hashes = input_hashes()
    evidence_digest = fingerprint(hashes)
    ontology = Graph()
    for path in sorted(ROOT.glob("ontology/*.ttl")):
        if not path.name.endswith(".bundle.ttl"):
            ontology.parse(path)
    graphs = {}
    runs = []
    for c in cases:
        for profile in PROFILES:
            key = (c["fixture"], profile)
            if key not in graphs:
                g = materialize(HERE/c["fixture"], profile,
                                f"urn:vcf-coverage:{Path(c['fixture']).stem}:{profile}")
                for s, p, o in g:
                    for term in (p, o) if p == RDF.type else (p,):
                        if str(term).startswith(str(V)):
                            assert any(ontology.triples((term, None, None))), f"Undeclared term: {term}"
                    assert (p, RDF.type, OWL.ObjectProperty) not in ontology or not isinstance(o, Literal), str(p)
                    assert (p, RDF.type, OWL.DatatypeProperty) not in ontology or isinstance(o, Literal), str(p)
                graphs[key] = g
            for axis in AXES:
                test = c[axis].get(profile, c[axis].get("both"))
                row = {"case": c["id"], "requirement": c["requirement"], "version": c["version"], "profile": profile, "axis": axis,
                       "witness": f"generated/witnesses/{Path(c['fixture']).stem}-{profile}.nt"}
                if test is None:
                    row.update(status="unassessed", reason="No independent expected-answer test supplied")
                else:
                    query = (HERE/test["query"]).read_text()
                    row.update(run_query(graphs[key], query, test["expected"], axis), query=test["query"])
                runs.append(row)

    ledger, queue = [], []
    for r in requirements:
        digest = fingerprint({"requirement": r, "cases": case_by_req[r["id"]], "evidence": evidence_digest})
        accepted = reviewed(review.get("requirements", {}).get(r["id"]), digest)
        if not accepted:
            queue.append({"id": r["id"], "question": r["question"], "fingerprint": digest,
                          "cases": [c["id"] for c in case_by_req[r["id"]]],
                          "untestedVersions": [v for v in r["versions"] if not any(c["version"] == v for c in case_by_req[r["id"]])],
                          "reason": "Review source interpretation, version scope, RDF pattern, and independent expected answers"})
        for version in r["versions"]:
            for profile in PROFILES:
                axes = {}
                for axis in AXES:
                    selected = [x["status"] for x in runs if (x["requirement"], x["version"], x["profile"], x["axis"]) == (r["id"], version, profile, axis)]
                    axes[axis] = status(selected)
                ledger.append(dict(requirement=r["id"], version=version, profile=profile, review="accepted" if accepted else "pending", **axes))

    audit = source_audit(source_text, requirements, review, cases)
    definitions = []
    registry = json.loads((ROOT/"ontology/versions/registry.json").read_text())
    for version, text in source_text.items():
        spec = next(s for s in registry["versions"] if s["id"] == version)
        artifact = spec["reservedKeys"]["graph"]
        g = Graph().parse(ROOT/artifact)
        for d in declarations(text):
            cls = V.InfoFieldDefinition if d["kind"] == "INFO" else V.FormatFieldDefinition
            observed = []
            # Three VCF 4.5 declarations identify regex families, not concrete
            # fields. Compare their literal keyPattern; never expand the family
            # or claim that arbitrary matching identifiers have been tested.
            identity = V.keyPattern if "[0-9]" in d["key"] else V.fieldId
            for node in g.subjects(identity, Literal(d["key"])):
                if (node, RDF.type, cls) in g:
                    observed.append({"number": str(g.value(node, V.fieldNumber)), "type": str(g.value(node, V.fieldType)).removeprefix(str(V)).removesuffix("Type")})
            wanted = {"number": d["number"], "type": d["type"]}
            definitions.append(dict(version=version, **d, artifact=artifact, identifierProperty=str(identity), actual=observed,
                                    status="exact" if observed == [wanted] else "missing" if not observed else "different"))

    audit_digest = fingerprint({"sections": audit, "requirements": requirements, "sources": lock})
    audit_ok = resolved(audit) and reviewed(review.get("sourceAudit"), audit_digest)
    if not audit_ok:
        queue.insert(0, {"id": "sourceAudit", "fingerprint": audit_digest,
                        "needsReviewSections": [r["id"] for r in audit if r["disposition"] == "needs-review"],
                        "reason": "Review explicit source assertions, test gaps and scope exclusions; resolve listed source questions"})
    by_version = []
    for version in source_text:
        for profile in PROFILES:
            rows = [r for r in ledger if r["version"] == version and r["profile"] == profile]
            axes = {}
            for axis in AXES:
                count = Counter(r[axis] for r in rows)
                axes[axis] = {s: count[s] for s in ("demonstrated", "partial", "not-demonstrated", "unassessed")}
                axes[axis]["percentDemonstrated"] = round(100*count["demonstrated"]/len(rows), 1)
            by_version.append(dict(version=version, profile=profile, denominator=len(rows), **axes))
    summary = {"method": "LOT requirements + source-to-RDF mapping + SAMOD-style answer tests (retrospective adaptation)",
               "claim": "Coverage of registered information requirements; specification completeness not established",
               "requirements": len(requirements), "cases": len(cases), "queryExecutions": len(runs),
               "sourceAuditAccepted": audit_ok, "pendingReviews": len(queue), "byVersion": by_version,
               "declarations": dict(rows=len(definitions), **Counter(x["status"] for x in definitions))}
    # This inventory reports existence/adequacy gaps, never an additional coverage
    # percentage. Requirements and assertions deliberately have different units.
    summary["sourceAssertions"] = {
        "sections": len(audit), "assertions": sum(len(r["assertions"]) for r in audit),
        "needsReviewSections": sum(r["disposition"] == "needs-review" for r in audit),
        "testStatus": dict(Counter(a["testStatus"] for r in audit for a in r["assertions"])),
    }
    provenance = {"schemaVersion": 1, "rdflib": rdflib.__version__, "inputs": hashes,
                  "reviewInputSha256": sha((HERE/"inputs/review.json").read_bytes()), "evidenceFingerprint": evidence_digest}
    output = {"summary.json": summary, "results.json": {"requirements": ledger, "queries": runs},
            "source-audit.json": audit, "declarations.json": definitions,
            "review-queue.json": queue, "provenance.json": provenance}
    # Fixed witness IRIs and sorted triples make RDF inspectable and reproducible
    # without relying on a serializer's arbitrary output order.
    for (fixture, profile), graph in graphs.items():
        output[f"witnesses/{Path(fixture).stem}-{profile}.nt"] = "\n".join(sorted(
            f"{s.n3()} {p.n3()} {o.n3()} ." for s, p, o in graph)) + "\n"
    return output


def result_block(summary):
    lines = ["<!-- results:start -->", f"**{summary['requirements']} registered requirements; {summary['cases']} cases; {summary['queryExecutions']} query slots** (two profiles × two axes).",
             "", "| VCF | Requirements | Expanded: preservation / structure | Condensed: preservation / structure |", "| --- | ---: | --- | --- |"]
    for version in sorted({r["version"] for r in summary["byVersion"]}):
        rows = [r for r in summary["byVersion"] if r["version"] == version]
        cells = [" / ".join(f"{r[a]['demonstrated']} ({r[a]['percentDemonstrated']}%)" for a in AXES) for r in rows]
        lines.append(f"| {version} | {rows[0]['denominator']} | {' | '.join(cells)} |")
    d = summary["declarations"]
    lines += ["", f"**Reserved declarations:** {d.get('exact',0)}/{d['rows']} explicit source rows match RDF Number/Type; {d.get('missing',0)} missing, {d.get('different',0)} different.",
              f"**Human review:** {summary['pendingReviews']} pending items; source completeness {'accepted' if summary['sourceAuditAccepted'] else 'not accepted'}."]
    if "sourceAssertions" in summary:
        a = summary["sourceAssertions"]
        t = a["testStatus"]
        lines += ["", f"**Source audit:** {a['sections']} sections; {a['assertions']} authored assertion entries; {a['needsReviewSections']} sections flagged `needs-review`.",
                  f"**Assertion test inventory:** {t.get('targeted-tests', 0)} with targeted cases, {t.get('partial-tests', 0)} with partial test evidence, {t.get('no-targeted-test', 0)} without a targeted case. These are test-presence categories, not passing-coverage scores."]
    current = next(r for r in summary["byVersion"] if r["version"] == "4.5" and r["profile"] == "condensed")
    lines += ["", f"For VCF 4.5, {current['structure']['not-demonstrated']} condensed structural witnesses fail; {current['structure']['unassessed']} requirements lack tests.", "<!-- results:end -->"]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("build", "check", "save-source-review"))
    p.add_argument("--require-reviewed", action="store_true")
    args = p.parse_args()
    if args.command == "save-source-review":
        save_source_review()
        return 0
    worksheet_path = HERE / "generated/source-audit.json"
    if args.command == "build" and worksheet_path.exists() and unsaved(json.loads(worksheet_path.read_text())):
        print("Unsaved source-audit annotations: run assess.py save-source-review before rebuilding.", file=sys.stderr)
        return 1
    outputs = evaluate()
    stale = []
    # Retired generated witnesses must not remain available as current evidence.
    for path in (HERE/"generated").rglob("*"):
        if path.is_file() and path.suffix in {".json", ".nt"} and path.relative_to(HERE/"generated").as_posix() not in outputs:
            if args.command == "build":
                path.unlink()
            else:
                stale.append(str(path.relative_to(ROOT)))
    for name, value in outputs.items():
        path = HERE/"generated"/name
        text = value if isinstance(value, str) else encoded(value)
        if args.command == "build":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        elif not path.exists() or path.read_text() != text:
            stale.append(str(path.relative_to(ROOT)))
    readme = HERE/"README.md"
    before = readme.read_text()
    after, count = re.subn(r"<!-- results:start -->.*?<!-- results:end -->", lambda _: result_block(outputs["summary.json"]), before, flags=re.S)
    assert count == 1, "README needs exactly one result block"
    if args.command == "build":
        readme.write_text(after)
    elif after != before:
        stale.append(str(readme.relative_to(ROOT)))
    if stale:
        print("Stale assessment outputs: " + ", ".join(stale), file=sys.stderr)
        return 1
    summary = outputs["summary.json"]
    print(f"Assessment {args.command}: {summary['requirements']} requirements, {summary['cases']} cases; {summary['pendingReviews']} human reviews pending.")
    return 2 if args.require_reviewed and summary["pendingReviews"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
