"""Supplement SHACL with decoded-vector and arbitrary-ploidy checks.

This module reports its checks separately: these are Python checks, not SHACL
constraints. It never repairs or materializes triples in the graph under test.
"""
import math
import re
from urllib.parse import unquote
from rdflib import Namespace, Literal
from rdflib.namespace import RDF
V=Namespace('https://w3id.org/vcf-core/vocab#')
FLOAT=re.compile(r'(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?|[-+]?(?:INF|INFINITY|NAN))',re.I)
GT=re.compile(r'[|/]?(?:[0-9]+|\.)(?:[|/](?:[0-9]+|\.))*')


def validate_semantics(g,ontology=None):
    errors=[]
    def err(code,node,text):errors.append(f'{code}: {node}: {text}')
    def obj(node,prop):
        if node is None:return None
        v=g.value(node,V[prop])
        return v if v is not None else ontology.value(node,V[prop]) if ontology is not None else None
    def text(node,prop,default=''):
        value=obj(node,prop);return str(value) if value is not None else default
    def integer(node,prop,default=0):
        try:return int(obj(node,prop))
        except (TypeError,ValueError,OverflowError):
            err('structural-integer',node,prop+' is missing or is not an integer')
            return default
    def ordered(node,path,index):return sorted(g.objects(node,V[path]),key=lambda x:integer(x,index)) if node is not None else []
    def components(raw):return [] if raw=='' else raw.split(',')
    def definition(n):
        d=obj(n,'declaredBy');return text(d,'fieldId'),text(d,'fieldNumber'),text(d,'fieldType').split('#')[-1].removesuffix('Type')
    def check_percent_encoding():
        # SHACL cannot percent-decode, so raw/decoded agreement is checked here.
        for item in g.subjects(V.rawValue,None):
            raw_form=text(item,'rawValue');decoded=text(item,'decodedValue')
            if not decoded:err('percent-decoded-missing',item,'rawValue without decodedValue')
            elif unquote(raw_form)!=decoded:
                err('percent-decoded-disagreement',item,f'{raw_form!r} decodes to {unquote(raw_form)!r}, not {decoded!r}')
    def check_values(node,key,num,typ,raw,alts,values,version):
        if raw=='.':return
        vals=components(raw)
        for value in vals:
            if value=='.':continue
            if typ=='Integer':
                if not re.fullmatch(r'[+-]?[0-9]+',value):err('integer-lexical',node,key+' is not Integer')
                elif version>='VCFv4.3' and not -2147483640<=int(value)<=2147483647:err('integer-range',node,key+' outside VCF Integer range')
            elif typ=='Float' and not FLOAT.fullmatch(value):err('float-lexical',node,key+' is not Float')
            elif typ=='Character' and len(unquote(value))!=1:err('character-width',node,key+' is not one decoded character')
            elif typ=='Flag':err('flag-value',node,'Flag must have no payload')
            if '%' in value and re.search(r'%(?![0-9A-Fa-f]{2})',value):err('percent-encoding',node,'invalid percent escape')
        gt=values.get('GT');tokens=re.findall(r'[0-9]+|\.',gt) if gt is not None else []
        ploidy=len(tokens) if gt is not None else 2
        local=[] if values.get('LAA','.') in ('','.') else values['LAA'].split(',')
        expected=int(num) if num.isdigit() else {'A':len(alts),'R':len(alts)+1,'P':ploidy,'LA':len(local),'LR':len(local)+1}.get(num)
        if num in ('G','LG'):expected=math.comb((len(local) if num=='LG' else len(alts))+ploidy,ploidy)
        if expected is not None and len(vals)!=expected:err('number-cardinality',node,f'{key}: expected {expected}, got {len(vals)}')
        if num in ('LA','LR','LG') and 'LAA' not in values:err('local-alleles',node,'local field requires LAA')
        if num=='M':
            if not gt or not GT.fullmatch(gt):err('modification-GT',node,'Number=M requires GT')
            elif 'LEN' not in values:
                residue=key[-1:];bases={'A':'AT','T':'AT','U':'AT','C':'CG','G':'CG','N':'ACGTN'}.get(residue)
                if bases:
                    sequences=[values.get('_REF','')]+alts;expected=0
                    for token in tokens:
                        if token=='.' or int(token)>=len(sequences):continue
                        seq=sequences[int(token)].upper()
                        if re.fullmatch('[ACGTN]+',seq):expected+=sum(base in bases for base in seq)*(2 if residue=='N' else 1)
                    if len(vals)!=expected:err('modification-cardinality',node,f'{key}: expected {expected} eligible sites')
        if key=='SVCLAIM' and any(v not in ('D','J','DJ','.') for v in vals):err('svclaim',node,'unsupported SVCLAIM code')
        if key in ('CIPOS','CIEND','CILEN','CICN') and len(vals)%2==0:
            for low,high in zip(vals[::2],vals[1::2]):
                if low=='.' or high=='.':continue
                try:
                    if float(low)>float(high):err('interval-order',node,key+' lower > upper')
                    if version>='VCFv4.4' and key in ('CIPOS','CIEND') and not float(low)<=0<=float(high):err('interval-origin',node,key+' must span zero')
                except ValueError:pass
    for file in g.subjects(RDF.type,V.VCFFile):
        version=text(file,'fileFormat')
        if version not in ('VCFv4.1','VCFv4.2','VCFv4.3','VCFv4.4','VCFv4.5'):err('unsupported-version',file,'complete validation profiles are available for VCF 4.1–4.5')
        sample_set=obj(file,'hasSampleSet');samples=ordered(sample_set,'hasSample','sampleIndex') if sample_set else []
        indices=[integer(s,'sampleIndex') for s in samples]
        if indices!=list(range(1,len(samples)+1)):err('sample-order',file,'sample indices must be contiguous from 1')
        header=obj(file,'hasHeader');column=obj(header,'hasColumnHeader')
        if column and set(g.objects(column,V.hasGenotypeColumns))!=set(samples):err('sample-columns',file,'column header and SampleSet differ')
        ids=set();block_ends={}
        for record in ordered(file,'hasRecord','recordIndex'):
            chrom=text(record,'chrom');pos=integer(record,'pos');ref=text(record,'ref');alt=text(record,'alt');alts=[] if alt=='.' else alt.split(',')
            rawids=[] if text(record,'recordId','.')=='.' else text(record,'recordId').split(';')
            if any(not rid or rid in ids for rid in rawids) or len(rawids)!=len(set(rawids)):err('record-IDs',record,'duplicate or empty individual identifier')
            ids.update(rawids)
            parsedids=[text(n,'identifierValue') for n in ordered(record,'hasIdentifier','componentIndex')]
            if parsedids and parsedids!=rawids:err('record-ID-components',record,'parsed IDs disagree with raw column')
            for call in g.objects(record,V.hasCall):
                rawfilter=text(call,'filter','.')
                codes=[] if rawfilter in ('.','PASS') else rawfilter.split(';')
                if any(x in ('0','','.','PASS') or re.search(r'\s',x) for x in codes) or len(codes)!=len(set(codes)):err('filter-codes',call,'invalid or duplicate FILTER code')
                infos={}
                for fv in g.objects(call,V.hasInfoValue):
                    key,num,typ=definition(fv);raw=text(fv,'fieldValue')
                    if typ=='Flag':
                        if obj(fv,'fieldValue') is not None or list(g.objects(fv,V.hasValueItem)):err('flag-value',fv,'Flag has a payload')
                        continue
                    check_values(fv,key,num,typ,raw,alts,{'_REF':ref},version);infos[key]=raw
                if 'RN' in infos and infos['RN']!='.':
                    try:
                        total=sum(int(x) for x in infos['RN'].split(',') if x!='.')
                        for key in ('RUS','RUL','RUC','RB'):
                            if key in infos and infos[key]!='.' and len(infos[key].split(','))!=total:err('repeat-cardinality',call,key+' must have sum(RN) items')
                    except ValueError:pass
                fmt=text(call,'formatRaw');keys=fmt.split(':') if fmt else []
                if len(keys)!=len(set(keys)):err('FORMAT-keys',call,'duplicate FORMAT key')
                sample_calls=list(g.objects(call,V.hasSampleCall));matrices=list(g.objects(call,V.hasCallMatrix))
                if sample_calls and len(sample_calls)!=len(samples):err('sample-call-count',call,'one expanded call per sample is required')
                if sample_calls and text(file,'representationProfile')!=str(V.ExpandedRepresentation):err('representation-profile',call,'expanded data conflicts with file profile')
                if matrices and text(file,'representationProfile')!=str(V.CondensedRepresentation):err('representation-profile',call,'matrix conflicts with file profile')
                rows=[]
                for sample in sample_calls:
                    values={};fields=list(g.objects(sample,V.hasFormatValue))
                    for fv in fields:
                        key,num,typ=definition(fv)
                        raw=obj(fv,'fieldValue')
                        if raw is None:
                            raw=obj(fv,'fieldValueInteger')
                            if raw is None:raw=obj(fv,'fieldValueDecimal')
                        if raw is not None:values[key]=str(raw)
                    rows.append((sample,values,fields))
                    gt=obj(sample,'hasGenotype')
                    if gt:
                        if text(gt,'genotypeString')!=values.get('GT'):err('GT-format-agreement',sample,'parsed genotype differs from FORMAT GT')
                        for gc in g.objects(gt,V.hasAlleleCall):
                            a=obj(gc,'calledAllele')
                            if a and a not in set(g.objects(record,V.hasAltAllele))|set(g.objects(record,V.hasReferenceAllele)):err('GT-record-allele',gc,'called allele belongs to a different record')
                        local=obj(gt,'hasLocalAlleleSet')
                        if local:
                            try:wanted=[] if values.get('LAA','.') in ('','.') else list(map(int,values['LAA'].split(',')))
                            except ValueError:
                                err('LAA-indices',sample,'non-integer LAA');wanted=[]
                            got=[integer(obj(m,'localAllele'),'alleleIndex') for m in ordered(local,'hasLocalAlleleMembership','localIndex')]
                            if got!=wanted:err('local-membership',local,'ordered memberships differ from LAA')
                for matrix in matrices:
                    vectors={};vector_defs={}
                    if obj(matrix,'appliesToSampleSet')!=sample_set:err('matrix-sample-set',matrix,'matrix belongs to another SampleSet')
                    for vec in g.objects(matrix,V.hasFormatValueVector):
                        key,num,typ=definition(vec);vectors[key]=text(vec,'encodedValues').split('\t');vector_defs[key]=(num,typ)
                    if set(vectors)!=set(keys):err('matrix-keys',matrix,'vectors do not match FORMAT keys')
                    if any(len(col)!=len(samples) for col in vectors.values()):err('vector-size',matrix,'vector/sample dimensions differ');continue
                    for i,sample in enumerate(samples):
                        values={key:col[i] for key,col in vectors.items()}
                        for key,(num,typ) in vector_defs.items():check_values(matrix,key,num,typ,values[key],alts,dict(values,_REF=ref),version)
                        rows.append((sample,values,[]))
                for sample,values,fields in rows:
                    for fv in fields:
                        key,num,typ=definition(fv)
                        if key in values:check_values(fv,key,num,typ,values[key],alts,dict(values,_REF=ref),version)
                    gt=values.get('GT')
                    if gt is not None:
                        if not GT.fullmatch(gt):err('GT-lexical',sample,'invalid GT token');continue
                        if any(int(t)>len(alts) for t in re.findall('[0-9]+',gt)):err('GT-allele-range',sample,'GT references absent ALT')
                    if values.get('PS','.')!='.' and values.get('PSL','.')!='.':err('phase-sets',sample,'PS and PSL both populated')
                    if values.get('LAA','.') not in ('','.'):
                        try:
                            local=list(map(int,values['LAA'].split(',')))
                            if len(local)!=len(set(local)) or any(i<1 or i>len(alts) for i in local):err('LAA-indices',sample,'LAA must name distinct record ALT alleles')
                        except ValueError:err('LAA-indices',sample,'non-integer LAA')
                    identity=obj(sample,'forSample') or sample;block_key=(identity,chrom)
                    if pos<=block_ends.get(block_key,-1) and (gt!='.' or any(k not in ('GT','LAA') and v!='.' for k,v in values.items())):err('reference-block-overlap',sample,'covered positions must be implicit reference calls')
                    if values.get('LEN','.')!='.':
                        try:
                            length=int(values['LEN'])
                            if length<1 or not any(a in ('<*>','<NON_REF>') for a in alts):err('reference-block',sample,'LEN requires an unspecified allele and positive length')
                            block_ends[block_key]=pos+length-1
                        except ValueError:err('reference-block',sample,'non-integer LEN')
    check_percent_encoding()
    return errors
