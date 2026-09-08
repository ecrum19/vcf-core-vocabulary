"""First-review rule probes. Executes SELECT bodies, not whole-file conformance.

Negative controls that a rule misses are recorded as gaps, not test successes.
Run with --check to compare against the recorded, reproducible observations.
"""
import argparse
import json
import sys
import tempfile
from pathlib import Path
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF
from rdflib.plugins.sparql import prepareQuery
from evidence import fingerprint

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V = Namespace('https://w3id.org/vcf-core/vocab#')
S = Namespace('http://www.w3.org/ns/shacl#')
T = Namespace('urn:first-review:')
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'coverage/curated'))
from semantic_validation import validate_semantics
from check_serialization import inspect as inspect_serialization
from extract import extract
from workflow import ALL_VERSIONS, source_lock, verified_source


def run():
    graphs = {p.relative_to(ROOT).as_posix(): Graph().parse(p) for p in sorted((ROOT / 'shacl').glob('*.ttl'))}
    def query_for(message):
        matches = [(path, g.value(rule, S.select)) for path, g in graphs.items()
                   for rule in g.subjects(S.message, None) if str(g.value(rule, S.message)) == message]
        assert len(matches) == 1, message
        return prepareQuery(str(matches[0][1]), initNs={'vcfc': V}), matches[0][0]
    def rdf(text):
        return Graph().parse(data='@prefix v: <https://w3id.org/vcf-core/vocab#> . @prefix t: <urn:first-review:> . '+text, format='turtle')
    def observed(query, text, focus=T.file):
        return bool(list(rdf(text).query(query, initBindings={'this': focus})))
    seeds = []
    def probe(label, message, valid, invalid, focus=T.file):
        query, path = query_for(message)
        row = {'id': label, 'ruleFile': path, 'ruleMessage': message,
               'validControlFlagged': observed(query, valid, focus), 'invalidControlFlagged': observed(query, invalid, focus)}
        seeds.append(row)
    recs = 't:file v:hasRecord t:a,t:b,t:c . t:a v:chrom "1"; v:recordIndex 1 . t:b v:chrom "CHROM"; v:recordIndex 2 . t:c v:chrom "2"; v:recordIndex 3 .'
    probe('chrom-block', 'Records for one CHROM must form a contiguous record-index block.', recs.replace('CHROM','1'), recs.replace('CHROM','2').replace('t:c v:chrom "2"','t:c v:chrom "1"'))
    recs = 't:file v:hasRecord t:a,t:b . t:a v:chrom "1"; v:recordIndex 1; v:pos 10 . t:b v:chrom "1"; v:recordIndex 2; v:pos VALUE .'
    probe('positions-equal-boundary', 'Record positions must be nondecreasing within a CHROM block.', recs.replace('VALUE','10'), recs.replace('VALUE','9'))
    ids = 't:file v:hasRecord t:a,t:b . t:a v:hasIdentifier t:i . t:b v:hasIdentifier t:j . t:i v:identifierValue "rs1" . t:j v:identifierValue "VALUE" .'
    probe('component-identifiers', 'Individual record identifiers must be unique across records.', ids.replace('VALUE','rs2'), ids.replace('VALUE','rs1'))
    headers = 't:header v:hasHeaderLine t:a,t:b . t:a a v:CLASS; v:headerKey "CUSTOM"; v:hasAttribute t:i . t:b a v:CLASS; v:headerKey "CUSTOM"; v:hasAttribute t:j . t:i v:attributeKey "ID"; v:attributeValue "same" . t:j v:attributeKey "ID"; v:attributeValue "VALUE" .'
    message = 'Structured header-line ID attributes must be unique within their header type.'
    for cls in ['INFOHeaderLine','StructuredHeaderLine']:
        base = headers.replace('CLASS',cls).replace('CUSTOM', 'INFO' if cls == 'INFOHeaderLine' else 'CUSTOM')
        probe('header-id-'+cls, message, base.replace('VALUE','other'), base.replace('VALUE','same'), T.header)
    samples = 't:file v:hasSampleSet t:set . t:set v:hasSample t:a,t:b . t:a v:sampleName "S1"; v:sampleIndex 1 . t:b v:sampleName "VALUE"; v:sampleIndex 2 .'
    probe('sample-names', "Sample names and sample indices must be unique within a VCF file's SampleSet.", samples.replace('VALUE','S2'), samples.replace('VALUE','S1'))
    fmt = 't:file v:hasRecord t:r . t:r v:hasCall t:c . t:c v:formatRaw "VALUE" .'
    message = 'GT must be the first FORMAT key when it is present.'
    probe('gt-first', message, fmt.replace('VALUE','GT:DP'), fmt.replace('VALUE','DP:GT'))
    assert not observed(query_for(message)[0], fmt.replace('VALUE','DP'))
    phase = 't:sample v:hasFormatValue t:ps,t:psl . t:ps v:declaredBy t:d; v:fieldValue "VALUE" . t:d v:fieldId "PS" . t:psl v:declaredBy t:e; v:fieldValue "name" . t:e v:fieldId "PSL" .'
    probe('phase-set-exclusion', 'PS and PSL must not both be populated for the same sample call.', phase.replace('VALUE','.'), phase.replace('VALUE','100'), T.sample)
    # A list of missing values is also a permitted encoding of missingness.
    probe('phase-set-missing-list', 'PS and PSL must not both be populated for the same sample call.',
          phase.replace('VALUE','100').replace('"name"','".,."'), phase.replace('VALUE','100'), T.sample)
    decoded = []
    for version in ['4.1', '4.2', '4.3', '4.4', '4.5']:
        base = f't:file a v:VCFFile; v:fileFormat "VCFv{version}"; v:hasRecord t:a,t:b . t:a v:recordIndex 1; v:pos 1; v:recordId "rs1;rs2" . t:b v:recordIndex 2; v:pos 2; v:recordId "VALUE" .'
        def codes(text):
            return sorted({e.split(':', 1)[0] for e in validate_semantics(rdf(text))})
        for label, positive, negative in [('raw-individual-identifiers', 'rs3;rs4', 'rs2;rs3')]:
            decoded.append({'id': label, 'version': version,
                            'validControlErrors': codes(base.replace('VALUE',positive)),
                            'invalidControlErrors': codes(base.replace('VALUE',negative))})
    for version in ['4.4','4.5']:
        for profile in ['Expanded','Condensed']:
            base = f't:file a v:VCFFile; v:fileFormat "VCFv{version}"; v:representationProfile v:{profile}Representation; v:hasSampleSet t:set; v:hasRecord t:r . t:set v:hasSample t:s . t:s v:sampleIndex 1 . t:r v:recordIndex 1; v:pos 1; v:hasCall t:c . t:c v:formatRaw "PS:PSL" . t:pd v:fieldId "PS"; v:fieldNumber "1"; v:fieldType v:IntegerType . t:ld v:fieldId "PSL"; v:fieldNumber "P"; v:fieldType v:StringType . '
            if profile == 'Expanded':
                base += 't:c v:hasSampleCall t:sc . t:sc v:hasFormatValue t:pv,t:lv . t:pv v:declaredBy t:pd; v:fieldValue "100" . t:lv v:declaredBy t:ld; v:fieldValue "VALUE" .'
            else:
                base += 't:c v:hasCallMatrix t:m . t:m v:appliesToSampleSet t:set; v:hasFormatValueVector t:pv,t:lv . t:pv v:declaredBy t:pd; v:encodedValues "100" . t:lv v:declaredBy t:ld; v:encodedValues "VALUE" .'
            decoded.append({'id':'phase-set-exclusion', 'version':version, 'profile':profile,
                            'validControlErrors':codes(base.replace('VALUE','.')),
                            'invalidControlErrors':codes(base.replace('VALUE','x,y')),
                            'allMissingListErrors':codes(base.replace('VALUE','.,.'))})
    serialization = []
    with tempfile.TemporaryDirectory(prefix='.review-bytes-', dir=HERE) as tmp:
        path = Path(tmp) / 'control.vcf'
        for version in ['4.3', '4.4', '4.5']:
            raw = (f'##fileformat=VCFv{version}\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n1\t1\t.\tA\tG\t.\tPASS\t.\n').encode()
            cases = [('valid-LF', raw, True), ('valid-CRLF', raw.replace(b'\n', b'\r\n'), True),
                     ('invalid-UTF8', raw.replace(b'PASS', b'\xff'), False),
                     ('BOM', b'\xef\xbb\xbf'+raw, False),
                     ('missing-final-newline', raw[:-1], False),
                     ('NUL', raw.replace(b'PASS', b'PA\x00SS'), False),
                     ('stray-CR', raw.replace(b'PASS', b'PA\rSS'), False),
                     # The source permits CRLF or LF; it does not state a uniformity rule.
                     ('mixed-line-endings', raw.replace(b'\n', b'\r\n', 1), True)]
            for label, content, expected in cases:
                path.write_bytes(content)
                result = inspect_serialization(path)
                serialization.append(dict(id=label, version=version, expectedValid=expected,
                                          accepted=result['passed'], problems=result['problems']))
    reserved = []
    lock = source_lock()
    extraction = {'versions': [extract(v, verified_source(lock['versions'][v]), lock['versions'][v]['sha256'])
                               for v in ALL_VERSIONS]}
    for version in extraction['versions']:
        v = version['version']
        for kind in ['INFO','FORMAT']:
            candidates = [c for c in version['candidates'] if c.get('reservedField',{}).get('kind') == kind]
            query, path = query_for(f'VCFv{v}: reserved {kind} declarations must match this version.')
            batches = {}
            for mutation in ['valid','number','type']:
                data = Graph()
                for i,c in enumerate(candidates):
                    f = c['reservedField']; prefix = f'{v}/{kind}/{i}/'
                    key = f['key'].replace('[0-9]+[ACGTUN]','123A')
                    number = '999' if mutation == 'number' else f['number']
                    typ = ('String' if f['type'] != 'String' else 'Integer') if mutation == 'type' else f['type']
                    file, header, definition = [T[prefix+x] for x in ['file','header','definition']]
                    data += rdf(f'<{file}> v:fileFormat "VCFv{v}"; v:hasHeader <{header}> . <{header}> v:hasHeaderLine <{definition}> . <{definition}> a v:{kind}HeaderLine; v:fieldId {Literal(key).n3()}; v:fieldNumber {Literal(number).n3()}; v:fieldType v:{typ}Type .')
                batches[mutation] = {str(row[0]) for row in data.query(query)}
            for i,c in enumerate(candidates):
                focus = str(T[f'{v}/{kind}/{i}/file'])
                row = {'candidate': c['id'], 'version': v, 'kind': kind, 'key': c['reservedField']['key'], 'ruleFile': path,
                       'validFlagged': focus in batches['valid'], 'wrongNumberFlagged': focus in batches['number'], 'wrongTypeFlagged': focus in batches['type']}
                assert not row['validFlagged'], row
                reserved.append(row)
    inputs = sorted([*graphs, 'tests/semantic_validation.py', 'coverage/curated/check_serialization.py'])
    return {'reviewer': 'Codex (first reviewer)', 'scope': 'Isolated SELECT-body, decoded-check and source-byte probes, not complete-file conformance tests. Both missed invalid controls and flagged valid controls are findings. Mixed LF/CRLF expected acceptance is a continued-review interpretation, not an owner-approved decision.',
            'inputs': {p: fingerprint((ROOT/p).read_bytes()) for p in inputs}, 'seedProbes': seeds, 'decodedProbes':decoded, 'serializationProbes':serialization,
            'reservedDeclarationProbes': reserved, 'reservedRows': len(reserved),
            'reservedRowsRejectingBothMutations': sum(r['wrongNumberFlagged'] and r['wrongTypeFlagged'] for r in reserved)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    result = run(); raw = (json.dumps(result,indent=2)+'\n').encode(); path = HERE/'probes/rules.json'
    if args.check:
        assert path.read_bytes() == raw, 'Review probe observations changed; rerun and reassess.'
    else:
        path.write_bytes(raw)
    print(f"{len(result['seedProbes'])} rule controls; {result['reservedRowsRejectingBothMutations']}/{result['reservedRows']} reserved rows reject both mutations.")
