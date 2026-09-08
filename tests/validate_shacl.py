#!/usr/bin/env python3
"""Validate complete examples or supplied RDF with SHACL and decoded-value checks.

Usage: python tests/validate_shacl.py [data.ttl ...] [--warnings-as-errors]
Multiple supplied files are merged (useful for split RDF documents). The suite
requires zero warnings; ad-hoc validation treats recommendations as warnings.
"""
from pathlib import Path
import argparse
import json
import sys
from pyshacl import validate
from rdflib import Graph, Namespace
from rdflib.namespace import RDF
from semantic_validation import validate_semantics
ROOT=Path(__file__).resolve().parent.parent
SH=Namespace('http://www.w3.org/ns/shacl#')
V=Namespace('https://w3id.org/vcf-core/vocab#')


def load_turtle(path):return Graph().parse(path,format='nt' if str(path).endswith('.nt') else 'turtle')
def load_schema():
    ontology=load_turtle(ROOT/'ontology/vcf-core-vocabulary.bundle.ttl')
    for p in sorted((ROOT/'ontology/versions').glob('*.ttl')):ontology+=load_turtle(p)
    shapes=Graph()
    for p in sorted((ROOT/'shacl').glob('*.ttl')):shapes+=load_turtle(p)
    return shapes,ontology

def result_summary(report):
    if not isinstance(report,Graph):raise RuntimeError(str(report))
    rows=list(report.subjects(RDF.type,SH.ValidationResult))
    return (sum(report.value(r,SH.resultSeverity)==SH.Violation for r in rows),sum(report.value(r,SH.resultSeverity)==SH.Warning for r in rows),{str(m) for r in rows for m in report.objects(r,SH.resultMessage)})

def check(label,data,shapes,ontology,strict=False,verbose=True):
    conforms,report,details=validate(data_graph=data,shacl_graph=shapes,ont_graph=ontology,inference='rdfs',advanced=True,allow_warnings=not strict)
    violations,warnings,messages=result_summary(report)
    semantic=validate_semantics(data,ontology)
    if verbose:
        print(f'{label}: SHACL violations={violations}; warnings={warnings}; semantic errors={len(semantic)}',flush=True)
        if not conforms or semantic:
            for message in sorted(messages):print('  '+message,flush=True)
            for message in semantic:print('  '+message,flush=True)
    return bool(conforms and not semantic),violations,warnings,messages

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('files',nargs='*',type=Path);parser.add_argument('--warnings-as-errors',action='store_true');args=parser.parse_args()
    shapes,ontology=load_schema()
    if args.files:
        data=Graph()
        for p in args.files:data+=load_turtle(p)
        return 0 if check('merged input',data,shapes,ontology,args.warnings_as_errors)[0] else 1
    failures=[];results=[]
    files=sorted((ROOT/'examples').rglob('*.ttl'))+[ROOT/'examples/core/example.nt']+sorted((ROOT/'coverage/paper').glob('*.ttl'))+[ROOT/'tests/shacl/generic-vcf44.ttl']
    fixtures=[(str(p.relative_to(ROOT)),load_turtle(p)) for p in files]
    merged=load_turtle(ROOT/'examples/core/example-headers.ttl');merged+=load_turtle(ROOT/'examples/core/example-minimal-record.ttl');fixtures.append(('headers + minimal merged',merged))
    fixtures.append(('CONSTRUCT template',Graph().query((ROOT/'mappings/vcf-to-vcf-core-construct.sparql').read_text()).graph))
    for label,data in fixtures:
        passed,v,w,_=check(label,data,shapes,ontology,strict=True)
        results.append(dict(fixture=label,violations=v,warnings=w,passed=passed))
        if not passed:failures.append(label)
    invalid=load_turtle(ROOT/'tests/shacl/invalid-vcf45.ttl')
    _,_,_,messages=check('negative control',invalid,shapes,ontology,strict=True,verbose=False)
    expected={'VCF 4.5 conformance requires fileFormat VCFv4.5.','The fileformat header line must have lineIndex 1.','Record positions must be nondecreasing within a CHROM block.'}
    if not expected<=messages:failures.append('negative control missing expected failures')
    print(f'{len(fixtures)} complete RDF fixtures checked; {len(failures)} failures.',flush=True)
    # The default suite intentionally regenerates machine-readable evidence.
    (ROOT/'tests/generated').mkdir(exist_ok=True)
    (ROOT/'tests/generated/validation.json').write_text(json.dumps(results,indent=2)+'\n')
    return bool(failures)
if __name__=='__main__':raise SystemExit(main())
