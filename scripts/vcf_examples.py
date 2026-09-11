#!/usr/bin/env python3
"""Materialize the repository's explicit VCF fixtures; not a production converter.

No reference sequence or remote ontology is fetched. Unknown declarations and
unsupported fixture syntax fail instead of guessing. Use --write to refresh RDF.
"""
from pathlib import Path
import argparse
import re
from urllib.parse import quote, unquote
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, XSD
import version_registry

ROOT = Path(__file__).resolve().parent.parent
# Supported fixture versions and their per-version behaviour come from the
# registry, so a new VCF version needs no edit here.
SPECS = version_registry.by_code()
V = Namespace('https://w3id.org/vcf-core/vocab#')
F = Namespace('http://biohackathon.org/resource/faldo#')
C = Namespace('http://purl.obolibrary.org/obo/CHEBI_')
ARITIES = dict(zip(['A','R','G','.','LA','LR','LG','P','M'], ['ArityPerAlt','ArityPerAllele','ArityPerGenotype','ArityVariable','ArityPerLocalAlt','ArityPerLocalAllele','ArityPerLocalGenotype','ArityPerGTAllele','ArityPerBaseModification']))
# ChEBI identifiers for the VCF 4.5 base-modification aliases, and the base each
# one occurs on. scripts/generate-reserved-keys.mjs holds the same table for the
# reserved-key ontology; an alias outside it is an error rather than a guess.
MODIFICATION_ALIASES = {'5mC':'27551','5hmC':'76792','5fC':'76794','5caC':'76793','5hmU':'16964','5fU':'80961','5caU':'17477','6mA':'28871','8oxoG':'44605','XaoN':'18107'}
MODIFICATION_PROPERTIES = {'':'modificationFraction','DP':'modificationDepth','AD':'modificationAlleleDepth'}
COMPLEMENT = {'A':'T','C':'G','G':'C','T':'A'}
LINE_CLASSES = {'fileformat':'FileFormatHeaderLine','fileDate':'FileDateHeaderLine','source':'SourceHeaderLine','reference':'ReferenceHeaderLine','contig':'ContigHeaderLine','INFO':'INFOHeaderLine','FORMAT':'FORMATHeaderLine','FILTER':'FILTERHeaderLine','ALT':'ALTHeaderLine','META':'MetaHeaderLine','SAMPLE':'SampleHeaderLine','PEDIGREE':'PedigreeHeaderLine','pedigreeDB':'PedigreeDBHeaderLine','assembly':'AssemblyHeaderLine'}


def attributes(text):
    """Split attributes outside quoted strings and bracketed META value lists."""
    parts=[]; start=0; quoted=False; escaped=False; depth=0
    for i,ch in enumerate(text):
        if escaped: escaped=False; continue
        if ch=='\\' and quoted: escaped=True; continue
        if ch=='"': quoted=not quoted
        if not quoted:
            if ch=='[': depth+=1
            if ch==']': depth-=1
            if ch==',' and depth==0: parts.append(text[start:i]); start=i+1
    if quoted or depth: raise ValueError('Unbalanced structured header')
    parts.append(text[start:]); result=[]
    for p in parts:
        k,sep,val=p.strip().partition('=')
        if not sep: raise ValueError('Header attribute without =: '+p)
        if val.startswith('"'):
            if not val.endswith('"'): raise ValueError('Unclosed quote')
            val=re.sub(r'\\(["\\])',r'\1',val[1:-1])
        result.append((k,val))
    if len({k for k,v in result})!=len(result): raise ValueError('Duplicate header attribute')
    return result


def modification_key(key):
    """Split a Number=M FORMAT key into value property, ChEBI ID and modified base.

    VCF 4.5 reserves M, DPM and ADM followed by either a ChEBI identifier or one
    of the documented aliases, then the base letter the modification occurs on.
    U is synonymous with T.
    """
    match=re.fullmatch(r'(DP|AD)?M(.+)',key)
    if not match:raise ValueError('Not a base-modification key: '+key)
    numeric=re.fullmatch(r'([0-9]+)([ACGTUN])',match[2])
    if numeric:chebi,letter=numeric[1],numeric[2]
    elif match[2] in MODIFICATION_ALIASES:chebi,letter=MODIFICATION_ALIASES[match[2]],match[2][-1]
    else:raise ValueError('Unsupported fixture modification: '+key)
    return MODIFICATION_PROPERTIES[match[1] or ''],chebi,'T' if letter=='U' else letter


def modification_sites(seq, letter):
    """Yield (offset, is forward strand) for every base that could carry it.

    The order is the order the bases occur in the allele. A stranded
    modification also applies to the complementary base on the reverse strand;
    for N the negative-strand value immediately follows the positive one.
    """
    for k,base in enumerate(seq.upper()):
        if letter=='N':yield k,True;yield k,False
        elif base==letter:yield k,True
        elif base==COMPLEMENT[letter]:yield k,False


def materialize(path, profile='expanded', base=None):
    path=Path(path)
    # Keep fixture IRIs portable and aligned with the ontology's file-based pattern.
    base=base or 'file://'+path.name
    g=Graph();g.bind('vcfc',V);g.bind('xsd',XSD);g.bind('faldo',F);g.bind('chebi',C);g.bind('ex',Namespace(base+'#'))
    def node(s,cls=None):
        n=URIRef(base+('#'+s if s else ''))
        if cls:g.add((n,RDF.type,V[cls]))
        return n
    def put(s,p,o):g.add((s,V[p],o if isinstance(o,(URIRef,Literal)) else Literal(o)))
    file=node('','VCFFile');header=node('header','VCFHeader');put(file,'hasHeader',header)
    put(file,'representationProfile',V.ExpandedRepresentation if profile=='expanded' else V.CondensedRepresentation)
    defs={}; contigs={}; names=[]; records=[]; byid={}; assembly=[]
    lines=path.read_text().splitlines()
    if not lines or not lines[0].startswith('##fileformat='):raise ValueError('Missing first fileformat line')
    version=lines[0].split('=',1)[1]
    if version not in SPECS:raise ValueError(f'Unsupported fixture version {version}; registry.json declares {", ".join(SPECS)}')
    spec=SPECS[version];tuple_widths=version_registry.sv_tuple_widths(spec)
    put(file,'fileFormat',version);g.add((file,RDF.type,V[spec['className']]))
    for i,line in enumerate(lines,1):
        if line.startswith('##'):
            key,raw=line[2:].split('=',1); structured=raw.startswith('<')
            n=node('header/line/'+str(i),LINE_CLASSES.get(key,'StructuredHeaderLine' if structured else 'UnstructuredHeaderLine'))
            put(header,'hasHeaderLine',n);put(n,'headerKey',key);put(n,'headerValue',raw);put(n,'lineIndex',i)
            attrs=attributes(raw[1:-1]) if structured else []
            a=dict(attrs)
            for j,(k,val) in enumerate(attrs,1):
                attr=node(f'header/line/{i}/attribute/{j}','HeaderAttribute')
                put(n,'hasAttribute',attr);put(attr,'attributeIndex',j);put(attr,'attributeKey',k);put(attr,'attributeValue',val)
            if key in ('INFO','FORMAT','META'):
                for k,p in [('ID','fieldId'),('Number','fieldNumber'),('Description','fieldDescription'),('Source','fieldSource'),('Version','fieldVersion')]:
                    if k in a:put(n,p,a[k])
                if 'Type' in a:put(n,'fieldType',V[a['Type']+'Type'])
                if a['Number'] in ARITIES:put(n,'fieldArity',V[ARITIES[a['Number']]])
                else:put(n,'fieldNumberInteger',int(a['Number']))
                defs[(key,a['ID'])]=(n,a)
                if key=='META':
                    for val in a.get('Values','[]')[1:-1].split(','):put(n,'metaAllowedValue',val.strip())
            elif key=='contig':
                put(n,'contigId',a['ID']);contigs[a['ID']]=n
                if 'length' in a:put(n,'contigLength',int(a['length']))
                if 'URL' in a:put(n,'contigUrl',Literal(a['URL'],datatype=XSD.anyURI))
            elif key in ('FILTER','ALT'):
                put(n,'filterId' if key=='FILTER' else 'altId',a['ID']);put(n,'fieldDescription',a['Description']);defs[(key,a['ID'])]=(n,a)
            elif key=='SAMPLE':put(n,'declaresSample',node('declaration/'+quote(a['ID']),'SampleDeclaration'))
            elif key=='PEDIGREE':
                for k,p in [('Mother','pedigreeMother'),('Father','pedigreeFather'),('Original','pedigreeOriginal')]:
                    if k in a:put(n,p,node('declaration/'+quote(a[k]),'SampleDeclaration'))
            elif key in ('reference','source'):put(file,'referenceGenome' if key=='reference' else 'sourceSoftware',raw)
            elif key=='fileDate' and re.fullmatch('[0-9]{8}',raw):put(file,'fileDate',Literal(raw[:4]+'-'+raw[4:6]+'-'+raw[6:],datatype=XSD.date))
            elif key in ('assembly','pedigreeDB'):
                put(n,'assemblyUrl' if key=='assembly' else 'pedigreeDbUrl',Literal(raw,datatype=XSD.anyURI))
                if key=='assembly':assembly.append(n)
        elif line.startswith('#CHROM'):
            cols=line.split('\t')
            if cols[:8]!=['#CHROM','POS','ID','REF','ALT','QUAL','FILTER','INFO']:raise ValueError('Invalid fixed column header')
            if len(cols)>8 and cols[8]!='FORMAT':raise ValueError('Missing FORMAT column')
            names=cols[9:];col=node('header/columns','ColumnHeaderLine');put(header,'hasColumnHeader',col)
            if names:
                ss=node('samples','SampleSet');put(file,'hasSampleSet',ss)
                for idx,name in enumerate(names,1):
                    sn=node('samples/'+quote(name),'VCFSample');put(sn,'sampleName',name);put(sn,'sampleIndex',idx);put(ss,'hasSample',sn);put(col,'hasGenotypeColumns',sn)
        elif line:
            cols=line.split('\t')
            if len(cols)!=(9+len(names) if names else 8):raise ValueError(f'{path}:{i}: sample columns must be tab-delimited')
            records.append(cols)
    def assembly_contig(cid):
        # An angle-bracketed name denotes a contig in the ##assembly file, not a
        # declared reference sequence, so it gets its own resource rather than a
        # fabricated ContigHeaderLine. Both CHROM and a breakend mate can use one.
        if not assembly:raise ValueError(f'{path}: <{cid}> needs an ##assembly line')
        ac=node('assembly/contig/'+quote(cid),'AssemblyContig')
        put(ac,'assemblyContigId',cid);put(ac,'declaredInAssembly',assembly[0])
        return ac
    for ri,cols in enumerate(records,1):
        chrom,pos,rid,ref,alt,qual,flt,info=cols[:8];r=node(f'record/{ri}','VCFRecord');call=node(f'call/{ri}','VariantCall')
        for p,val in [('recordIndex',ri),('chrom',chrom),('pos',int(pos)),('recordId',Literal('.',datatype=V.Null) if rid=='.' else rid),('ref',ref),('alt',Literal('.',datatype=V.Null) if alt=='.' else alt),('hasCall',call)]:put(r,p,val)
        put(file,'hasRecord',r)
        if chrom in contigs:put(r,'chromosome',contigs[chrom])
        elif re.fullmatch(r'<[^<>,\s]+>',chrom):
            # VCF 4.5 fixed field 1: an angle-bracketed CHROM names an assembly contig.
            put(r,'chromAssemblyContig',assembly_contig(chrom[1:-1]))
        elif chrom not in contigs:raise ValueError(f'{path}: CHROM {chrom} is neither a declared contig nor a bracketed assembly contig')
        for j,idval in enumerate([] if rid=='.' else rid.split(';'),1):
            n=node(f'record/{ri}/id/{j}','RecordIdentifier');put(r,'hasIdentifier',n);put(n,'identifierValue',idval);put(n,'componentIndex',j);byid[idval]=ri
        put(call,'qual',Literal('.',datatype=V.Null) if qual=='.' else Literal(qual,datatype=V.VCFFloat))
        put(call,'filter',Literal('.',datatype=V.Null) if flt=='.' else flt);put(call,'infoRaw',info)
        def filters(parent,raw):
            put(parent,'filterStatus',V.FiltersPassed if raw=='PASS' else V.FiltersNotApplied if raw=='.' else V.FiltersFailed)
            for j,code in enumerate([] if raw in ('.','PASS') else raw.split(';'),1):
                n=URIRef(str(parent)+f'/filter/{j}');g.add((n,RDF.type,V.FilterCode));put(parent,'hasFilterCode',n);put(n,'filterCodeValue',code);put(n,'componentIndex',j)
                if ('FILTER',code) in defs:put(n,'declaredByFilter',defs['FILTER',code][0])
        filters(call,flt)
        alleles=[];seqs=[ref]+([] if alt=='.' else alt.split(','))
        for ai,seq in enumerate(seqs):
            a=node(f'record/{ri}/allele/{ai}','ReferenceAllele' if ai==0 else 'AltAllele');alleles.append(a)
            put(r,'hasReferenceAllele' if ai==0 else 'hasAltAllele',a);put(a,'alleleIndex',ai);put(a,'alleleValue',seq)
            kind='BaseSequenceAllele' if re.fullmatch('[ACGTNacgtn]+',seq) else 'OverlappingDeletionAllele' if seq=='*' else 'UnspecifiedAllele' if seq in ('<*>','<NON_REF>') else 'SymbolicAllele' if seq.startswith('<') else 'BreakendAllele'
            put(a,'alleleKind',V[kind])
            if seq.startswith('<') and ('ALT',seq[1:-1]) in defs:put(a,'declaredByAlt',defs['ALT',seq[1:-1]][0])
            if kind=='BreakendAllele':
                g.add((a,RDF.type,V.Breakend));put(a,'breakendReplacementString',Literal(seq,datatype=V.BreakendString))
                single=seq.startswith('.') or seq.endswith('.');put(a,'isSingleBreakend',single)
                if not single:
                    # Four syntax carriers are looked up by their documented forms below.
                    form=('s' if seq[0] not in '[]' else '')+('[' if '[' in seq else ']')
                    orientation={'s[':'SequenceBeforeLeftBracket','s]':'SequenceBeforeRightBracket','[':'SequenceAfterLeftBracket',']':'SequenceAfterRightBracket'}[form]
                    put(a,'breakendOrientation',V[orientation])
                    match=re.search(r'[\[\]](.+):([0-9]+)[\[\]]',seq)
                    if not match:raise ValueError('Unparseable breakend '+seq)
                    loc=node(f'record/{ri}/allele/{ai}/remote','')
                    # A large insertion places the mate on an assembly contig
                    # rather than on a declared reference sequence.
                    remote=assembly_contig(match[1][1:-1]) if re.fullmatch(r'<[^<>,\s]+>',match[1]) else contigs[match[1]]
                    g.add((loc,RDF.type,F.ExactPosition));g.add((loc,F.position,Literal(int(match[2]))));g.add((loc,F.reference,remote));g.add((a,F.location,loc))
        # Padding-base interpretation (VCF 4.5 fixed field 4). Asserted only where
        # the specification determines it; a shared prefix alone is not evidence.
        alts=[x for x in seqs[1:] if x not in ('.','*')]
        symbolic=[x for x in alts if x.startswith('<') and x not in ('<*>','<NON_REF>')]
        unspecified_only=bool(alts) and all(x in ('<*>','<NON_REF>') for x in alts)
        plain=[x for x in alts if re.fullmatch('[ACGTNacgtn]+',x)]
        # A pure indel differs from REF by a whole prefix or a whole suffix. Which
        # end is shared decides which base is padding: a shared FIRST base is the
        # ordinary leading padding, whereas a shared LAST base is the trailing
        # padding VCF 4.5 requires when the variant itself sits at position 1.
        diff=[x for x in plain if len(x)!=len(ref)]
        prefix=any(x.startswith(ref) or ref.startswith(x) for x in diff)
        suffix=any(x.endswith(ref) or ref.endswith(x) for x in diff)
        if symbolic:rule,side,count='SymbolicAllelePadding','PaddingBefore',1
        elif unspecified_only:rule,side,count='UnspecifiedAlleleNoPadding',None,0
        elif prefix:rule,side,count='SimpleIndelPadding','PaddingBefore',1
        elif suffix and int(pos)==1:rule,side,count='PositionOnePadding','PaddingAfter',1
        else:
            # Includes complex substitutions, where every allele already has a base
            # of its own and the specification leaves padding optional, and
            # non-canonical suffix-anchored indels away from position 1.
            rule,side,count='PaddingNotDetermined',None,0
        pad=node(f'record/{ri}/padding','PaddingInterpretation')
        put(r,'hasPaddingInterpretation',pad);put(pad,'paddingRule',V[rule]);put(pad,'paddingBaseCount',count)
        if side:
            put(pad,'paddingSide',V[side])
            put(pad,'paddingAnchorPosition',int(pos) if side=='PaddingBefore' else int(pos)+len(ref)-1)
        infoval={}; infonodes={}
        def field(parent,key,raw,kind,index):
            if (kind,key) not in defs:raise ValueError(f'{path}: missing {kind} definition for {key}')
            definition,decl=defs[kind,key]
            segment='info' if kind=='INFO' else 'fmt'
            n=URIRef(str(parent)+'/'+segment+'/'+quote(key));g.add((n,RDF.type,V.InfoFieldValue if kind=='INFO' else V.FormatFieldValue))
            put(parent,'hasInfoValue' if kind=='INFO' else 'hasFormatValue',n);put(n,'declaredBy',definition);put(n,'fieldIndex',index)
            if decl['Type']=='Flag':put(n,'fieldValueBoolean',True);return n,[]
            put(n,'fieldValue',Literal('.',datatype=V.Null) if raw=='.' else raw)
            vals=[] if raw=='' else raw.split(',');items=[]
            for idx,value in enumerate(vals):
                item=URIRef(str(n)+f'/item/{idx}');g.add((item,RDF.type,V.FieldValueItem));put(n,'hasValueItem',item);put(item,'valueIndex',idx)
                lit=Literal('.',datatype=V.Null) if value=='.' else Literal(int(value)) if decl['Type']=='Integer' else Literal(value,datatype=V.VCFFloat) if decl['Type']=='Float' else Literal(value)
                put(item,'itemValue',lit);items.append(item)
                # VCF 4.5 section 1.2: characters with special meaning are percent-encoded.
                # Keep the source token and its decoded form side by side so a consumer
                # never has to guess which one it is holding.
                if '%' in value:
                    put(item,'rawValue',value);put(item,'decodedValue',unquote(value))
                number=decl['Number']
                if raw!='.' and number in ('A','R'):
                    ai=idx+(1 if number=='A' else 0)
                    if ai<len(alleles):put(item,'forAllele',alleles[ai])
                if number in ('G','LG'):put(item,'forGenotypeIndex',idx)
                if number=='P':put(item,'forGTAlleleIndex',idx)
            if len(vals)==1 and vals[0]!='.':
                if decl['Type']=='Integer':put(n,'fieldValueInteger',int(vals[0]))
                elif decl['Type']=='Float' and re.fullmatch(r'[-+]?[0-9]+(?:\.[0-9]+)?',vals[0]):put(n,'fieldValueDecimal',Literal(vals[0],datatype=XSD.decimal))
            return n,items
        for idx,entry in enumerate([] if info=='.' else info.split(';'),1):
            key,sep,raw=entry.partition('=');infoval[key]=raw;n,items=field(call,key,raw,'INFO',idx);infonodes[key]=(n,items)
            if key in tuple_widths:
                width=tuple_widths[key]
                for j,item in enumerate(items):
                    put(item,'tupleArity',width)
                    if spec['svTupleScope']=='perAlt' and j//width+1<len(alleles):put(item,'forAllele',alleles[j//width+1])
        symbols={'DEL':'SymbolicDeletion','INS':'SymbolicInsertion','DUP':'SymbolicDuplication','INV':'SymbolicInversion','CNV':'SymbolicCopyNumberVariation','CNV:TR':'SymbolicTandemRepeat'}
        for ai,a in enumerate(alleles[1:],1):
            code=seqs[ai][1:-1]
            if code in symbols:put(a,'svType',V[symbols[code]])
            for key,prop in [('SVLEN','svLength'),('CN','copyNumber')]:
                if key in infoval:
                    if key=='CN' and not spec['perAlleleCopyNumber']:
                        put(call,'copyNumber',int(infoval[key]));continue
                    val=infoval[key].split(',')[min(ai-1,len(infoval[key].split(','))-1)]
                    if val!='.':put(a,prop,Literal(val,datatype=XSD.integer if key=='SVLEN' else XSD.decimal))
            if 'SVCLAIM' in infoval:
                val=infoval['SVCLAIM'].split(',')[ai-1];put(a,'svClaim',V[{'D':'AbundanceClaim','J':'AdjacencyClaim','DJ':'AbundanceAndAdjacencyClaim'}[val]])
            if 'IMPRECISE' in infoval:put(a,'isImprecise',True)
            if 'CILEN' in infoval:
                vals=infoval['CILEN'].split(',')[2*(ai-1):2*ai]
                if len(vals)==2 and '.' not in vals:
                    ci=node(f'record/{ri}/allele/{ai}/cilen','ConfidenceInterval');put(a,'lenConfidenceInterval',ci);put(ci,'ciLower',int(vals[0]));put(ci,'ciUpper',int(vals[1]))
            if code=='CNV:TR':
                g.add((a,RDF.type,V.TandemRepeatAllele));rn=int(infoval['RN'].split(',')[ai-1]);put(a,'repeatSequenceCount',rn)
                offset=sum(map(int,infoval['RN'].split(',')[:ai-1]))
                for j in range(rn):
                    repeat=node(f'record/{ri}/allele/{ai}/repeat/{j+1}','RepeatSequence');put(a,'hasRepeatSequence',repeat);put(repeat,'repeatSequenceIndex',j+1)
                    for key,prop in [('RUS','repeatUnitSequence'),('RUL','repeatUnitLength'),('RUC','repeatUnitCount'),('RB','repeatBases')]:
                        if key in infoval:
                            val=infoval[key].split(',')[offset+j];put(repeat,prop,val if key=='RUS' else Literal(val,datatype=XSD.decimal if key=='RUC' else XSD.integer))
        if names:
            fmt=cols[8].split(':');put(call,'formatRaw',cols[8])
            # The declared key list is a resource sequence, so an omitted trailing
            # field is distinguishable from an undeclared key without parsing.
            for ki,key in enumerate(fmt,1):
                fk=node(f'call/{ri}/formatKey/{ki}','FormatKey')
                put(call,'hasFormatKey',fk);put(fk,'fieldIndex',ki)
                if ('FORMAT',key) in defs:put(fk,'declaredBy',defs['FORMAT',key][0])
            if profile=='condensed':
                matrix=node(f'call/{ri}/matrix','CohortCallMatrix');put(call,'hasCallMatrix',matrix);put(matrix,'appliesToSampleSet',node('samples'));put(matrix,'sampleDataRaw','\t'.join(cols[9:]))
                for j,key in enumerate(fmt):
                    vector=node(f'call/{ri}/matrix/fmt/{key}','FormatValueVector');put(matrix,'hasFormatValueVector',vector);put(vector,'declaredBy',defs['FORMAT',key][0]);put(vector,'valueEncoding',V.VCFTextVector)
                    put(vector,'encodedValues','\t'.join(raw.split(':')[j] if j<len(raw.split(':')) else '.' for raw in cols[9:]))
                continue
            for name,raw in zip(names,cols[9:]):
                sn=node(f'sample/{ri}/{quote(name)}','SampleCall');put(call,'hasSampleCall',sn);put(sn,'sampleId',name);put(sn,'forSample',node('samples/'+quote(name)));put(sn,'sampleFieldsRaw',raw)
                values=dict(zip(fmt,raw.split(':')));fnodes={}
                for idx,key in enumerate(fmt,1):
                    if key in values:fnodes[key]=field(sn,key,values[key],'FORMAT',idx)
                if 'LEN' in values and values['LEN']!='.':
                    block=node(f'sample/{ri}/{quote(name)}/block','ReferenceBlock');put(sn,'hasReferenceBlock',block)
                    put(block,'referenceBlockLength',int(values['LEN']));put(block,'endPosition',int(pos)+int(values['LEN'])-1);put(block,'isReferenceBlockStart',True)
                    for ai,seq in enumerate(seqs):
                        if seq in ('<*>','<NON_REF>'):put(block,'blockAllele',alleles[ai])
                if 'FT' in values:put(sn,'sampleFilter',values['FT']);filters(sn,values['FT'])
                if 'GT' in values:
                    gt=node(f'sample/{ri}/{quote(name)}/genotype','Genotype');put(sn,'hasGenotype',gt);put(gt,'genotypeString',Literal(values['GT'],datatype=V.GenotypeString))
                    tokens=re.findall(r'([|/]?)([0-9]+|\.)',values['GT']);put(gt,'ploidy',len(tokens));indicators=[];gtcalls=[]
                    for j,(indicator,token) in enumerate(tokens):
                        indicator=indicator or ('/' if '/' in values['GT'] else '|');indicators.append(indicator)
                        gc=node(f'sample/{ri}/{quote(name)}/genotype/{j}','GenotypeAlleleCall');gtcalls.append(gc);put(gt,'hasAlleleCall',gc);put(gc,'callIndex',j);put(gc,'isNoCall',token=='.');put(gc,'phaseIndicator',indicator)
                        if token!='.':put(gc,'calledAllele',alleles[int(token)])
                    put(gt,'phasingStatus',V.MixedPhasing if len(set(indicators))>1 else V.Phased if indicators[0]=='|' else V.Unphased)
                    if 'PS' in values and values['PS']!='.':
                        phase=node('phase/'+quote(name)+'/'+quote(chrom)+'/'+values['PS'],'PhaseSet');put(gt,'inPhaseSet',phase);put(phase,'phaseSetId',values['PS'])
                    if 'PSL' in values:
                        for j,val in enumerate(values['PSL'].split(',')):
                            if val!='.':
                                phase=node('phase/'+quote(name)+'/'+quote(val),'PhaseSet');put(gtcalls[j],'allelePhaseSet',phase);put(phase,'phaseSetName',val)
                    if 'LAA' in values:
                        ls=node(f'sample/{ri}/{quote(name)}/local','LocalAlleleSet');put(gt,'hasLocalAlleleSet',ls)
                        for j,val in enumerate([] if values['LAA'] in ('','.') else values['LAA'].split(','),1):
                            member=node(f'sample/{ri}/{quote(name)}/local/{j}','LocalAlleleMembership');put(ls,'hasLocalAlleleMembership',member);put(member,'localIndex',j);put(member,'localAllele',alleles[int(val)]);put(ls,'hasLocalAllele',alleles[int(val)])
                        locals_=[alleles[0]]+[alleles[int(x)] for x in ([] if values['LAA'] in ('','.') else values['LAA'].split(','))]
                        for key,(fv,items) in fnodes.items():
                            number=defs['FORMAT',key][1]['Number']
                            if number in ('LA','LR') and values[key]!='.':
                                for j,item in enumerate(items):put(item,'forAllele',locals_[j+(number=='LA')])
                    for key,(fv,items) in fnodes.items():
                        if defs['FORMAT',key][1]['Number']!='M' or values[key]=='.':continue
                        prop,chebi,letter=modification_key(key)
                        sites=[];aggregated=set()
                        for j,(indicator,(_,token)) in enumerate(zip(indicators,tokens)):
                            # Unphased allele values are aggregated and encoded at the
                            # first occurrence; missing and symbolic alleles carry no
                            # modifiable bases and so encode no values at all.
                            if token=='.' or (indicator=='/' and token in aggregated):continue
                            if indicator=='/':aggregated.add(token)
                            seq=seqs[int(token)]
                            if not re.fullmatch('[ACGTNacgtn]+',seq):continue
                            sites.extend((j,k,forward) for k,forward in modification_sites(seq,letter))
                        if len(sites)!=len(items):raise ValueError('Number=M fixture cardinality mismatch')
                        for item,(j,k,forward) in zip(items,sites):
                            # One resource per modification, allele slot and strand, so
                            # fraction, depth and allele depth of the same chemistry meet
                            # and two chemistries on one base stay apart.
                            mod=node(f'sample/{ri}/{quote(name)}/modification/{chebi}/{j}/{k}/{"forward" if forward else "reverse"}','BaseModification')
                            put(item,'forBaseModification',mod);put(item,'forGTAlleleIndex',j);put(mod,'modifiedResidue',C[chebi]);put(mod,'modifiedBaseOffset',k)
                            g.add((mod,RDF.type,F.ForwardStrandPosition if forward else F.ReverseStrandPosition))
                            val=g.value(item,V.itemValue)
                            if str(val)!='.':put(mod,prop,val)
    # Cross-record breakend relationships are resolved only after all IDs exist.
    for ri,cols in enumerate(records,1):
        info=dict(entry.split('=',1) if '=' in entry else (entry,'') for entry in cols[7].split(';') if entry!='.')
        for key,prop in [('MATEID','mateBreakend'),('PARID','partnerBreakend')]:
            for ai,idval in enumerate(info.get(key,'').split(','),1):
                if idval and idval!='.':put(node(f'record/{ri}/allele/{ai}'),prop,node(f'record/{byid[idval]}/allele/1'))
    return g


def outputs():
    yield 'examples/core/example.vcf','examples/core/example.ttl','expanded',None
    yield 'examples/core/example-file1.vcf','examples/core/example-minimal-record.ttl','expanded',None
    yield 'examples/profiles/example-condensed-cohort.vcf','examples/profiles/example-condensed-cohort.ttl','condensed',None
    for src in sorted((ROOT/'examples/vcf-versions').rglob('example-vcf*.vcf')):
        yield str(src.relative_to(ROOT)),str(src.with_suffix('.ttl').relative_to(ROOT)),'expanded',None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--only',action='append',default=[],metavar='SOURCE.vcf',help='Regenerate only this source path; repeat for several sources.')
    args=parser.parse_args()
    if not args.write:parser.error('Use --write; validation is tests/validate_shacl.py')
    selected=list(outputs())
    if args.only:
        wanted={Path(p).resolve() for p in args.only}
        known={(ROOT/item[0]).resolve() for item in selected}
        if wanted-known:parser.error('Unknown fixture source: '+', '.join(map(str,sorted(wanted-known))))
        selected=[item for item in selected if (ROOT/item[0]).resolve() in wanted]
    for source,target,profile,base in selected:
        g=materialize(ROOT/source,profile,base)
        (ROOT/target).write_text(g.serialize(format='turtle').rstrip()+'\n')
        if target=='examples/core/example.ttl':(ROOT/'examples/core/example.nt').write_text(''.join(sorted(g.serialize(format='nt').splitlines(keepends=True))))
        if target=='examples/core/example-minimal-record.ttl':
            # Header-only is a complete zero-record VCF graph; merge is harmless.
            h=Graph();h+=g
            for record in list(h.objects(None,V.hasRecord)):h.remove((None,V.hasRecord,record))
            # Retain only the file, header, declarations and sample column resources.
            reachable={next(h.subjects(RDF.type,V.VCFFile))}
            while True:
                file_iri=str(next(h.subjects(RDF.type,V.VCFFile)))
                expanded=reachable|{o for s,p,o in h if s in reachable and isinstance(o,URIRef) and str(o).startswith(file_iri)}
                if expanded==reachable:break
                reachable=expanded
            for s,p,o in list(h):
                if s not in reachable:h.remove((s,p,o))
            (ROOT/'examples/core/example-headers.ttl').write_text(h.serialize(format='turtle').rstrip()+'\n')
        print(target,len(g),'triples')

if __name__=='__main__':main()
