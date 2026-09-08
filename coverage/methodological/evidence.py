"""Discover addressable evidence; presence is never a coverage verdict."""
from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

from rdflib import BNode, Graph, Namespace, RDF, RDFS, URIRef
from rdflib.compare import to_canonical_graph

from extract import digest

V = Namespace("https://w3id.org/vcf-core/vocab#")
SH = Namespace("http://www.w3.org/ns/shacl#")


def fingerprint(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def closure(graph, node):
    result, seen, queue = Graph(), set(), [node]
    while queue:
        subject = queue.pop()
        if subject in seen:
            continue
        seen.add(subject)
        for triple in graph.triples((subject, None, None)):
            result.add(triple)
            if isinstance(triple[2], BNode):
                queue.append(triple[2])
    return result


def graph_fingerprint(graph):
    canonical = to_canonical_graph(graph)
    rows = sorted(" ".join(term.n3() for term in triple) for triple in canonical)
    return fingerprint("\n".join(rows).encode())


def rule_scope(query: str, versions: list[str]):
    # Deliberately narrow: recognise the generated positive fileFormat triple.
    # Complex FILTERs/UNIONs cannot be evaluated by a text scan.
    exact = re.findall(r'\$this\s+vcfc:fileFormat\s+"VCFv(4\.[1-5])"\s*[;.]', query)
    mentions = re.findall(r"VCFv4\.[1-5]", query)
    if len(exact) == 1 and len(mentions) == 1 and "UNION" not in query.upper():
        return exact, "explicit positive fileFormat gate; graph prerequisites still need review"
    # Generated overlays use a common outer gate and nested UNIONs. Only the
    # prologue before the first nested group is used as evidence of a common gate.
    prologue = query.split("WHERE", 1)[-1].lstrip().removeprefix("{").split("{", 1)[0]
    if len(exact) == 1 and len(mentions) == 1 and re.search(
            r'\$this\s+vcfc:fileFormat\s+"VCFv' + re.escape(exact[0]) + r'"\s*[;.]', prologue):
        return exact, "common outer fileFormat gate; graph prerequisites still need review"
    if not mentions and "fileFormat" not in query:
        return versions, "ungated rule; target/materialization prerequisites need review"
    return [], "unresolved gate; explicit scope assessment required"


def catalogue(root: Path, versions: list[str], inventory: dict) -> list[dict]:
    targets = []
    for path in sorted((root / "shacl").glob("*.ttl")):
        graph = Graph().parse(path, format="turtle")
        relative = path.relative_to(root).as_posix()
        for shape in sorted(set(graph.subjects(RDF.type, SH.NodeShape)), key=str):
            if not isinstance(shape, URIRef):
                continue
            shape_graph = closure(graph, shape)
            queries = list(shape_graph.objects(None, SH.select))
            scopes = [rule_scope(str(q), versions)[0] for q in queries]
            gate_values = [str(v).removeprefix("VCFv") for v in shape_graph.objects(None, SH.hasValue)
                           if str(v).startswith("VCFv")]
            applies = sorted(set.intersection(*(set(s) for s in scopes))) if scopes else (gate_values or versions)
            local = str(shape).split("#")[-1]
            targets.append({"id": f"shape:{relative}#{local}", "type": "shape", "file": relative,
                            "iri": str(shape), "text": local + " " + " ".join(sorted(str(m) for m in shape_graph.objects(None, SH.message))),
                            "versions": applies, "scopeBasis": "intersection of recognised rule scopes; inspect full shape",
                            "fingerprint": graph_fingerprint(shape_graph)})
            for rule in graph.objects(shape, SH.sparql):
                messages = sorted(str(m) for m in graph.objects(rule, SH.message))
                if not messages:
                    continue
                rule_graph = closure(graph, rule)
                for predicate, value in graph.predicate_objects(shape):
                    if str(predicate).startswith(str(SH) + "target") or predicate == SH.deactivated:
                        rule_graph.add((shape, predicate, value))
                scope, basis = rule_scope(str(graph.value(rule, SH.select) or ""), versions)
                targets.append({"id": f"rule:{relative}#{local}@{digest('|'.join(messages))}",
                                "type": "rule", "file": relative, "iri": str(shape),
                                "text": " ".join(messages), "versions": scope, "scopeBasis": basis,
                                "fingerprint": graph_fingerprint(rule_graph)})
    for area in inventory["areas"]:
        for construct in area["constructs"]:
            targets.append({"id": f"inventory:{construct['id']}", "type": "inventory",
                            "file": "coverage/curated/inventory.json", "text": construct["construct"],
                            "versions": ["4.5"], "scopeBasis": "curated inventory explicitly assesses VCF 4.5 only",
                            "fingerprint": fingerprint(json.dumps(construct, sort_keys=True).encode()),
                            "construct": construct})
    # Ontology terms permit direct representational evidence without pretending
    # the VCF 4.5 curated inventory already assessed the earlier versions.
    ontology_paths = set((root / "ontology").glob("*.ttl")) | set((root / "ontology/versions").glob("*.ttl"))
    for path in sorted(ontology_paths):
        if ".bundle." in path.name:
            continue
        graph = Graph().parse(path, format="turtle")
        relative = path.relative_to(root).as_posix()
        for term in sorted(set(graph.subjects(RDF.type, None)), key=str):
            if not isinstance(term, URIRef) or not str(term).startswith(str(V)):
                continue
            description = " ".join(str(x) for x in graph.objects(term, RDFS.label))
            # A reserved 4.5 definition is not automatically evidence for 4.1.
            reserved = [str(v).removeprefix("VCFv") for v in graph.objects(term, V.reservedIn)]
            target = {"id": f"term:{relative}#{str(term).split('#')[-1]}", "type": "term",
                            "file": relative, "iri": str(term), "text": str(term).split('#')[-1] + " " + description,
                            "versions": reserved or versions, "scopeBasis": "declared reservedIn" if reserved else "shared ontology term; semantic applicability requires review",
                            "fingerprint": graph_fingerprint(closure(graph, term))}
            for kind, cls in [('INFO', V.InfoFieldDefinition), ('FORMAT', V.FormatFieldDefinition)]:
                if (term, RDF.type, cls) in graph:
                    key = graph.value(term, V.fieldId)
                    if key is None:
                        key = graph.value(term, V.keyPattern)
                    if key is not None:
                        target['reservedField'] = {'kind': kind, 'key': str(key),
                                                   'description': str(graph.value(term, V.fieldDescription) or '')}
            targets.append(target)
    decoded = root / "tests/semantic_validation.py"
    tree = ast.parse(decoded.read_text())
    codes = {}
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "err"
                and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
            codes.setdefault(node.args[0].value, []).append(node.lineno)
    for code, lines in sorted(codes.items()):
        targets.append({"id": f"decoded:{code}", "type": "decoded", "file": "tests/semantic_validation.py",
                        "text": code, "lines": sorted(lines), "versions": [],
                        "scopeBasis": "Python control flow needs an explicit version-scope assessment",
                        "fingerprint": fingerprint(decoded.read_bytes())})
    checker = root / "coverage/curated/check_serialization.py"
    tree = ast.parse(checker.read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "inspect":
            targets.append({"id": "serialization:inspect", "type": "serialization",
                            "file": "coverage/curated/check_serialization.py", "text": "UTF-8 BOM LF CRLF final newline non-printable characters",
                            "lines": [node.lineno, node.end_lineno], "versions": versions,
                            "scopeBasis": "version-independent byte predicates; applicability follows the separately reviewed source clause, not the checker's introductory VCF 4.5 label",
                            "fingerprint": fingerprint(checker.read_bytes())})
    ids = [t["id"] for t in targets]
    if len(ids) != len(set(ids)):
        raise ValueError("evidence target IDs are not unique")
    return sorted(targets, key=lambda t: t["id"])


def compare_reserved_definitions(extractions, entries, root: Path):
    """Compare literal Number/Type facts; this is not a semantic discharge."""
    results = []
    for extraction, entry in zip(extractions, entries):
        reserved = entry['reservedKeys']
        if reserved['mode'] == 'snapshot':
            artifact = reserved['snapshot']
            definitions = json.loads((root / artifact).read_text())['definitions']
        else:
            artifact = reserved['graph']
            graph = Graph().parse(root / artifact, format='turtle')
            definitions = []
            for kind, cls in [('INFO', V.InfoFieldDefinition), ('FORMAT', V.FormatFieldDefinition)]:
                for term in graph.subjects(RDF.type, cls):
                    key = graph.value(term, V.fieldId)
                    if key is None:
                        key = graph.value(term, V.keyPattern)
                    typ = graph.value(term, V.fieldType)
                    number = graph.value(term, V.fieldNumber)
                    definitions.append({'kind': kind, 'id': str(key), 'number': str(number),
                                        'type': str(typ).split('#')[-1].removesuffix('Type')})
        index = {}
        for definition in definitions:
            index.setdefault((definition['kind'], definition['id']), []).append(
                {'number': definition['number'], 'type': definition['type']})
        rows = []
        for candidate in extraction['candidates']:
            field = candidate.get('reservedField')
            if field is None:
                continue
            actual = index.get((field['kind'], field['key']), [])
            expected = {'number': field['number'], 'type': field['type']}
            rows.append({'candidate': candidate['id'], 'kind': field['kind'], 'key': field['key'],
                         'sourceDefinition': expected, 'artifactDefinitions': actual,
                         'result': 'exact' if actual and all(a == expected for a in actual) else
                                   'missing' if not actual else 'different'})
        results.append({'version': extraction['version'], 'artifact': artifact,
                        'sourceRows': len(rows), 'sourceKeys': len({(r['kind'], r['key']) for r in rows}),
                        'exact': sum(r['result'] == 'exact' for r in rows),
                        'missing': sum(r['result'] == 'missing' for r in rows),
                        'different': sum(r['result'] == 'different' for r in rows), 'rows': rows})
    return {'note': 'Literal Number/Type comparison for independently extracted explicit source rows only. '
                    'Matching metadata does not establish value enforcement, source completeness, or full requirement coverage.',
            'versions': results}
