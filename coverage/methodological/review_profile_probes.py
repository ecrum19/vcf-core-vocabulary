"""Reproduce first-review counterexamples through the complete RDF validator.

These are assessment observations, including accepted invalid controls, not a
claim that the validator is conformant. --check verifies recorded observations.
"""
import argparse
import json
import sys
from pathlib import Path
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from validate_shacl import check, load_schema
from evidence import fingerprint

V = Namespace('https://w3id.org/vcf-core/vocab#')
T = Namespace('urn:first-review:complete:')
FIXTURE = 'examples/vcf-versions/vcf-4.5/example-vcf45-breakends.ttl'


def run():
    shapes, ontology = load_schema()
    base = Graph().parse(ROOT / FIXTURE)
    file = next(base.subjects(RDF.type, V.VCFFile))
    header = base.value(file, V.hasHeader)
    start = max(int(base.value(h, V.lineIndex)) for h in base.objects(header, V.hasHeaderLine)) + 1
    observations = []

    def assess(label, data, expected):
        passed, violations, warnings, _ = check(label, data, shapes, ontology, strict=True, verbose=False)
        observations.append(dict(id=label, expectedValid=expected, accepted=passed,
                                 violations=violations, warnings=warnings))
        print(f'{label}: expectedValid={expected}, accepted={passed}', flush=True)

    def line(data, index, key, attrs, cls):
        node = T[f'line/{index}']
        data.add((header, V.hasHeaderLine, node))
        for predicate, value in [(RDF.type, cls), (V.lineIndex, Literal(index)), (V.headerKey, Literal(key)),
                                 (V.headerValue, Literal('<'+','.join(k+'='+v for k,v in attrs)+'>'))]:
            data.add((node, predicate, value))
        for i, (k, v) in enumerate(attrs, 1):
            attribute = T[f'line/{index}/attribute/{i}']
            data.add((node, V.hasAttribute, attribute))
            for predicate, value in [(RDF.type, V.HeaderAttribute), (V.attributeIndex, Literal(i)),
                                     (V.attributeKey, Literal(k)), (V.attributeValue, Literal(v.strip('"')))]:
                data.add((attribute, predicate, value))
        return node

    assess('baseline', base, True)
    for label, second_key, ids, expected in [
        ('extension-distinct-ids', 'CUSTOM', ['a','b'], True),
        ('extension-same-id-different-prefix', 'OTHER', ['a','a'], True),
        ('extension-duplicate-id', 'CUSTOM', ['a','a'], False),
        ('extension-missing-id', 'CUSTOM', [None,None], False),
    ]:
        data = Graph() + base
        for offset, identifier in enumerate(ids):
            line(data, start+offset, 'CUSTOM' if offset == 0 else second_key,
                 [('ID',identifier)] if identifier is not None else [('Note','no-id')], V.StructuredHeaderLine)
        assess(label, data, expected)
    for key, typ in [('M123A','Float'),('DPM123A','Integer'),('ADM123A','Integer')]:
        for mutation in ['valid','number','type']:
            data = Graph() + base
            number = '999' if mutation == 'number' else 'M'
            field_type = 'String' if mutation == 'type' else typ
            node = line(data, start, 'FORMAT', [('ID',key),('Number',number),('Type',field_type),
                                               ('Description','"Review probe"')], V.FORMATHeaderLine)
            for predicate, value in [(V.fieldId,Literal(key)), (V.fieldNumber,Literal(number)),
                                     (V.fieldType,V[field_type+'Type']), (V.fieldDescription,Literal('Review probe'))]:
                data.add((node,predicate,value))
            assess(key+'-'+mutation, data, mutation == 'valid')
    # Include the actual runtime inputs, not just the source modules that build them.
    inputs = sorted({p for pattern in ['ontology/*.ttl','ontology/versions/*.ttl','shacl/*.ttl',
                                      'tests/validate_shacl.py','tests/semantic_validation.py',FIXTURE]
                     for p in ROOT.glob(pattern)})
    return dict(reviewer='Codex (first reviewer)', scope='Full SHACL plus decoded validation, strict warnings, RDFS inference, complete positive fixture with appended declarations.',
                inputs={p.relative_to(ROOT).as_posix():fingerprint(p.read_bytes()) for p in inputs}, observations=observations)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=run(); raw=(json.dumps(result,indent=2)+'\n').encode(); path=HERE/'probes/profiles.json'
    if args.check:
        if path.read_bytes()!=raw:raise SystemExit('Review profile observations changed; rerun and reassess.')
    else:path.write_bytes(raw)
    mismatches=[r for r in result['observations'] if r['expectedValid'] != r['accepted']]
    print(f'{len(result["observations"])} observations; {len(mismatches)} validator/spec expectation mismatches.')
