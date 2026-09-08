"""Independent regression probes for the assessment findings and version boundaries."""
from pathlib import Path
import importlib.util
import sys
import unittest
from rdflib import Graph,Namespace,Literal,URIRef
from rdflib.namespace import RDF,XSD
from pyshacl import validate
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tests'))
spec=importlib.util.spec_from_file_location('validator',ROOT/'tests/validate_shacl.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
V=Namespace('https://w3id.org/vcf-core/vocab#')

class ValidationRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.shapes,cls.ontology=module.load_schema()
    def setUp(self):
        self.g=Graph().parse(ROOT/'examples/vcf-versions/vcf-4.5/example-vcf45-features.ttl')
        self.file=next(self.g.subjects(RDF.type,V.VCFFile));self.header=self.g.value(self.file,V.hasHeader)
        self.record=min(self.g.objects(self.file,V.hasRecord),key=lambda r:int(self.g.value(r,V.recordIndex)))
        self.call=self.g.value(self.record,V.hasCall);self.sample=self.g.value(self.call,V.hasSampleCall);self.gt=self.g.value(self.sample,V.hasGenotype)
        self.ff=next(self.g.subjects(RDF.type,V.FileFormatHeaderLine));self.allele=self.g.value(self.record,V.hasAltAllele)
        self.af=next(f for f in self.g.objects(self.call,V.hasInfoValue) if str(self.g.value(self.g.value(f,V.declaredBy),V.fieldId))=='AF')
        self.afdef=self.g.value(self.af,V.declaredBy)
    def assert_shape(self,name,conforms=False):
        actual,report,details=validate(self.g,shacl_graph=self.shapes,ont_graph=self.ontology,inference='rdfs',advanced=True,use_shapes=[str(V[name]),str(V.IntegerLiteralShape),str(V.NumericLiteralShape)])
        self.assertEqual(actual,conforms,details)
    def test_end_deprecation_version(self):
        self.assertEqual(str(self.ontology.value(V.ReservedInfo_END,V.deprecatedInVersion)), 'VCFv4.5')
        self.assertEqual(str(self.ontology.value(V.ReservedInfo_SVTYPE,V.deprecatedInVersion)), 'VCFv4.4')
    def test_reference_disagreement(self):
        self.g.set((self.record,V.ref,Literal('A')));self.assert_shape('AlleleRawAgreementShape')
    def test_header_attribute_disagreement(self):
        attr=next(a for a in self.g.objects(self.afdef,V.hasAttribute) if str(self.g.value(a,V.attributeKey))=='Number')
        self.g.set((attr,V.attributeValue,Literal('1')));self.assert_shape('HeaderDeclarationAgreementShape')
    def test_special_float_is_accepted(self):
        self.g.set((self.call,V.qual,Literal('+Infinity',datatype=V.VCFFloat)));self.assert_shape('VariantCallShape',True)
    def test_missing_ps_does_not_conflict_with_psl(self):
        sample=next(s for s in self.g.subjects(RDF.type,V.SampleCall) if any(str(self.g.value(self.g.value(f,V.declaredBy),V.fieldId))=='PSL' for f in self.g.objects(s,V.hasFormatValue)))
        fv=URIRef('urn:test:PS');self.g.add((sample,V.hasFormatValue,fv));self.g.add((fv,RDF.type,V.FormatFieldValue));self.g.add((fv,V.declaredBy,V.ReservedFormat_PS));self.g.add((fv,V.fieldValue,Literal('.',datatype=V.Null)))
        self.assert_shape('SampleCallLocalAlleleSparqlShape',True)
        self.g.set((fv,V.fieldValue,Literal('100')));self.assert_shape('SampleCallLocalAlleleSparqlShape')
    def test_missing_fileformat(self):
        self.g.remove((self.header,V.hasHeaderLine,self.ff));self.assert_shape('VCFHeaderShape')
    def test_missing_column_header(self):
        self.g.remove((self.header,V.hasColumnHeader,None));self.assert_shape('VCFHeaderShape')
    def test_header_version_disagreement(self):
        self.g.set((self.ff,V.headerValue,Literal('VCFv4.4')));self.assert_shape('HeaderVersionAgreementShape')
    def test_negative_position(self):
        self.g.set((self.record,V.pos,Literal(-1)));self.assert_shape('VCFRecordShape')
    def test_invalid_custom_float(self):
        self.g.set((self.call,V.qual,Literal('banana',datatype=V.VCFFloat)));self.assert_shape('VariantCallShape')
    def test_invalid_custom_genotype(self):
        self.g.set((self.gt,V.genotypeString,Literal('banana',datatype=V.GenotypeString)));self.assert_shape('GenotypeShape')
    def test_invalid_number(self):
        self.g.set((self.afdef,V.fieldNumber,Literal('Q')));self.g.remove((self.afdef,V.fieldArity,None));self.assert_shape('InfoFieldDefinitionShape')
    def test_wrong_reserved_definition(self):
        self.g.set((self.afdef,V.fieldNumber,Literal('1')));self.g.set((self.afdef,V.fieldType,V.StringType));self.g.remove((self.afdef,V.fieldArity,None));self.assert_shape('VCF45INFOReservedShape')
    def test_wrong_value_type(self):
        self.g.set((self.af,V.fieldValue,Literal('banana')));self.assert_shape('InfoFieldValueLexicalShape')
    def test_number_a_raw_count(self):
        self.g.set((self.af,V.fieldValue,Literal('0.25,0.5')));self.assert_shape('InfoFieldValueCardinalityShape')
    def test_extra_parsed_item(self):
        n=URIRef('urn:test:extra');self.g.add((self.af,V.hasValueItem,n));self.g.add((n,RDF.type,V.FieldValueItem));self.g.add((n,V.valueIndex,Literal(1)));self.g.add((n,V.itemValue,Literal('0.5')));self.assert_shape('ValueItemCountShape')
    def test_ploidy_disagreement(self):
        self.g.set((self.gt,V.ploidy,Literal(7)));self.assert_shape('GenotypeCallAgreementShape')
    def test_alt_disagreement(self):
        self.g.set((self.record,V.alt,Literal('G')));self.assert_shape('AlleleRawAgreementShape')
    def test_all_tuple_items_removed(self):
        fv=next(f for f in self.g.subjects(RDF.type,V.InfoFieldValue) if str(self.g.value(self.g.value(f,V.declaredBy),V.fieldId))=='CILEN');self.g.remove((fv,V.hasValueItem,None));self.assert_shape('VCF45Tuple2ItemsShape')
    def test_interval_order(self):
        n=next(self.g.subjects(RDF.type,V.ConfidenceInterval));self.g.set((n,V.ciLower,Literal(30)));self.assert_shape('ConfidenceIntervalShape')
    def test_derived_integer_is_accepted(self):
        self.g.set((self.allele,V.alleleIndex,Literal(1,datatype=XSD.positiveInteger)));self.assert_shape('AlleleShape',True)
    def test_reference_derived_zero_is_accepted(self):
        ref=self.g.value(self.record,V.hasReferenceAllele);self.g.set((ref,V.alleleIndex,Literal(0,datatype=XSD.nonNegativeInteger)));self.assert_shape('ReferenceAlleleShape',True)
    def test_decimal_index_is_rejected(self):
        self.g.set((self.allele,V.alleleIndex,Literal('1.0',datatype=XSD.decimal)));self.assert_shape('AlleleShape')
    def test_nonsense_version(self):
        self.g.set((self.file,V.fileFormat,Literal('garbage')));self.assert_shape('VCFFileShape')
    def test_old_cipos_is_valid(self):
        self.g=Graph().parse(ROOT/'examples/vcf-versions/vcf-4.3/example-vcf43.ttl');self.assert_shape('VCF43Tuple2Shape',True)
    def test_old_cipos_fails_modern_rule(self):
        self.g=Graph().parse(ROOT/'examples/vcf-versions/vcf-4.3/example-vcf43.ttl');file=next(self.g.subjects(RDF.type,V.VCFFile));self.g.set((file,V.fileFormat,Literal('VCFv4.5')));self.assert_shape('VCF45Tuple2Shape')
    def test_unsupported_old_number_m(self):
        self.g.set((self.file,V.fileFormat,Literal('VCFv4.4')));self.assert_shape('VCF44NumberShape')
    def test_vcf41_disallows_number_r(self):
        self.g.set((self.file,V.fileFormat,Literal('VCFv4.1')));self.assert_shape('VCF41NumberShape')
    def test_short_vector(self):
        self.g=Graph().parse(ROOT/'examples/profiles/example-condensed-cohort.ttl');vec=next(self.g.subjects(RDF.type,V.FormatValueVector));self.g.set((vec,V.encodedValues,Literal('0/1')));self.assert_shape('MatrixDimensionShape')
    def test_mixed_indicator_disagreement(self):
        gc=next(self.g.objects(self.gt,V.hasAlleleCall));self.g.set((gc,V.phaseIndicator,Literal('/')));self.assert_shape('GenotypeAlleleAgreementShape')
    def test_null_token(self):
        self.g.set((self.call,V.qual,Literal('not-missing',datatype=V.Null)));self.assert_shape('NullLiteralShape')
    def test_decoded_integer_range(self):
        fv=next(f for f in self.g.objects(self.sample,V.hasFormatValue) if str(self.g.value(self.g.value(f,V.declaredBy),V.fieldId))=='DP');self.g.set((fv,V.fieldValue,Literal('-2147483648')))
        self.assertTrue(any(e.startswith('integer-range:') for e in module.validate_semantics(self.g,self.ontology)))
    def test_malformed_structure_reports_errors_without_crashing(self):
        self.g.set((self.record,V.pos,Literal('not-an-integer')))
        sample=next(self.g.subjects(RDF.type,V.VCFSample))
        self.g.remove((sample,V.sampleIndex,None))
        laa=next(f for f in self.g.subjects(RDF.type,V.FormatFieldValue) if str(self.g.value(self.g.value(f,V.declaredBy),V.fieldId))=='LAA')
        self.g.set((laa,V.fieldValue,Literal('bad-index')))
        errors=module.validate_semantics(self.g,self.ontology)
        self.assertTrue(any(e.startswith('structural-integer:') for e in errors))
        self.assertTrue(any(e.startswith('LAA-indices:') for e in errors))
    def test_decoded_modification_cardinality(self):
        fv=next(f for f in self.g.objects(self.sample,V.hasFormatValue) if str(self.g.value(self.g.value(f,V.declaredBy),V.fieldId))=='M5mC');self.g.set((fv,V.fieldValue,Literal('0.9,0.1')))
        self.assertTrue(any(e.startswith('modification-cardinality:') for e in module.validate_semantics(self.g,self.ontology)))
    def test_arbitrary_ploidy_g_cardinality(self):
        gtfv=next(f for f in self.g.objects(self.sample,V.hasFormatValue) if str(self.g.value(self.g.value(f,V.declaredBy),V.fieldId))=='GT');pl=next(f for f in self.g.objects(self.sample,V.hasFormatValue) if str(self.g.value(self.g.value(f,V.declaredBy),V.fieldId))=='PL')
        self.g.set((gtfv,V.fieldValue,Literal('/'.join(['0']*9))));self.g.set((pl,V.fieldValue,Literal(','.join(['0']*10))))
        self.assertFalse(any(e.startswith('number-cardinality:') and str(pl) in e for e in module.validate_semantics(self.g,self.ontology)))
        self.g.set((pl,V.fieldValue,Literal(','.join(['0']*9))))
        self.assertTrue(any(e.startswith('number-cardinality:') and str(pl) in e for e in module.validate_semantics(self.g,self.ontology)))

if __name__=='__main__':unittest.main()


class BoundaryRegression(unittest.TestCase):
    """Probes for the boundary constructs: telomeres, assembly contigs, padding.

    Each new rule is exercised in the negative as well as the positive, so a rule
    that silently never fires cannot be mistaken for evidence.
    """

    @classmethod
    def setUpClass(cls):cls.shapes,cls.ontology=module.load_schema()

    def setUp(self):
        self.g=Graph().parse(ROOT/'examples/vcf-versions/vcf-4.5/example-vcf45-boundaries.ttl')
        self.byPos={int(self.g.value(r,V.pos)):r for r in self.g.subjects(RDF.type,V.VCFRecord)}
        self.asmRecord=next(iter(self.g.subjects(V.chromAssemblyContig,None)))
        self.asmContig=self.g.value(self.asmRecord,V.chromAssemblyContig)

    def assert_shape(self,name,conforms=False):
        actual,report,details=validate(self.g,shacl_graph=self.shapes,ont_graph=self.ontology,inference='rdfs',advanced=True,use_shapes=[str(V[name]),str(V.IntegerLiteralShape),str(V.NumericLiteralShape)])
        self.assertEqual(actual,conforms,details)

    # --- telomeric positions (inventory entry 55) ---
    def test_telomere_boundaries_are_accepted(self):
        self.assertIn(0,self.byPos);self.assertIn(101,self.byPos)
        self.assert_shape('RecordContigBoundSparqlShape',True)

    def test_position_beyond_contig_end_is_rejected(self):
        self.g.set((self.byPos[101],V.pos,Literal(102)))
        self.assert_shape('RecordContigBoundSparqlShape')

    # --- assembly-contig CHROM (inventory entry 53) ---
    def test_assembly_contig_agreement_is_accepted(self):
        self.assert_shape('AssemblyContigAgreementShape',True)

    def test_parsed_assembly_contig_must_match_the_token(self):
        self.g.set((self.asmContig,V.assemblyContigId,Literal('other')))
        self.assert_shape('AssemblyContigAgreementShape')

    def test_bracketed_chrom_must_not_also_name_a_declared_contig(self):
        contig=next(iter(self.g.subjects(RDF.type,V.ContigHeaderLine)))
        self.g.add((self.asmRecord,V.chromosome,contig))
        self.assert_shape('AssemblyContigAgreementShape')

    def test_bracketed_chrom_requires_a_parsed_contig(self):
        self.g.remove((self.asmRecord,V.chromAssemblyContig,None))
        self.assert_shape('AssemblyContigAgreementShape')

    # --- REF padding interpretation (inventory entry 59) ---
    def test_padding_interpretations_are_accepted(self):
        self.assert_shape('PaddingInterpretationAgreementShape',True)

    def test_padding_anchor_must_follow_from_pos_and_side(self):
        pad=self.g.value(self.byPos[50],V.hasPaddingInterpretation)
        self.g.set((pad,V.paddingAnchorPosition,Literal(51)))
        self.assert_shape('PaddingInterpretationAgreementShape')

    def test_undetermined_padding_may_not_claim_a_side(self):
        pad=self.g.value(self.byPos[90],V.hasPaddingInterpretation)
        self.assertEqual(self.g.value(pad,V.paddingRule),V.PaddingNotDetermined)
        self.g.add((pad,V.paddingSide,V.PaddingBefore))
        self.assert_shape('PaddingInterpretationAgreementShape')

    def test_position_one_rule_requires_trailing_padding_at_position_one(self):
        pad=self.g.value(self.byPos[1],V.hasPaddingInterpretation)
        self.assertEqual(self.g.value(pad,V.paddingRule),V.PositionOnePadding)
        self.g.set((pad,V.paddingSide,V.PaddingBefore))
        self.assert_shape('PaddingInterpretationAgreementShape')

    def test_all_five_padding_rules_occur_in_the_fixture(self):
        seen={self.g.value(p,V.paddingRule) for p in self.g.subjects(RDF.type,V.PaddingInterpretation)}
        self.assertEqual(seen,{V.SimpleIndelPadding,V.SymbolicAllelePadding,V.PositionOnePadding,
                               V.UnspecifiedAlleleNoPadding,V.PaddingNotDetermined})

    # --- whole-field versus itemwise missingness (inventory entry 90) ---
    def test_three_missingness_shapes_are_distinguishable(self):
        shapes={}
        for value in self.g.subjects(RDF.type,V.InfoFieldValue):
            if str(self.g.value(self.g.value(value,V.declaredBy),V.fieldId))!='AF':continue
            record=next(iter(self.g.subjects(V.hasInfoValue,value)),None)
            record=next(iter(self.g.subjects(V.hasCall,record)),None) if record is None else record
            items=[self.g.value(i,V.itemValue) for i in self.g.objects(value,V.hasValueItem)]
            missing=[i for i in items if i is not None and i.datatype==V.Null]
            present=[i for i in items if i is not None and i.datatype!=V.Null]
            raw=self.g.value(value,V.fieldValue)
            if raw is not None and raw.datatype==V.Null:shapes['whole-field']=True
            elif missing and not present:shapes['all-items']=True
            elif missing and present:shapes['partial']=True
        self.assertEqual(set(shapes),{'whole-field','all-items','partial'})

    # --- percent encoding (inventory entry 48) ---
    def test_percent_encoded_value_keeps_both_forms(self):
        item=next(iter(self.g.subjects(V.rawValue,None)))
        self.assertEqual(str(self.g.value(item,V.rawValue)),'left%3Bright%3Aend%25')
        self.assertEqual(str(self.g.value(item,V.decodedValue)),'left;right:end%')

    def test_percent_decoded_disagreement_is_detected(self):
        item=next(iter(self.g.subjects(V.rawValue,None)))
        self.g.set((item,V.decodedValue,Literal('wrong')))
        errors=module.validate_semantics(self.g,self.ontology)
        self.assertTrue(any('percent-decoded-disagreement' in e for e in errors),errors)
