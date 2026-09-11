"""The mapping sets must stay valid, and the alignment module must stay honest."""
import importlib.util
import json
from pathlib import Path
import unittest

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, SKOS

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_mapping_sets', ROOT / 'scripts/build-mapping-sets.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

ALIGNMENTS = URIRef('https://w3id.org/vcf-core/alignments')
CORE = URIRef('https://w3id.org/vcf-core/vocab')


class MappingSetTests(unittest.TestCase):
    def test_every_set_validates(self):
        for path in builder.mapping_sets():
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertEqual(builder.validate(path), [])

    def test_module_matches_the_curated_set(self):
        prefixes, metadata, rows = builder.read_set(builder.CURATED)
        self.assertEqual(builder.MODULE.read_text(encoding='utf-8'),
                         builder.render_module(prefixes, metadata, rows),
                         'alignment module is stale; run npm run mappings:build')

    def test_module_is_a_superset_of_the_ontology(self):
        self.assertEqual(builder.check_superset(), [])

    def test_bh25_sets_name_their_source_sheet(self):
        """Third-party transcriptions must stay traceable to the workbook they came from."""
        registry = json.loads((ROOT / 'mappings/registry.json').read_text(encoding='utf-8'))
        known = set(registry['provenance']['sourceSheets'].values())
        self.assertTrue(known, 'registry records no source sheets')
        for path in sorted((ROOT / 'mappings/bh25').glob('*.sssom.tsv')):
            with self.subTest(path=path.name):
                source = builder.read_set(path)[1].get('mapping_set_source')
                self.assertTrue(source, f'{path.name} does not record mapping_set_source')
                self.assertTrue(set(source) <= known,
                                f'{path.name} cites a sheet the registry does not list')

    def test_registry_lists_every_set_on_disk(self):
        registry = json.loads((ROOT / 'mappings/registry.json').read_text(encoding='utf-8'))
        declared = {entry['file'] for entry in registry['mappingSets']}
        found = {str(p.relative_to(ROOT / 'mappings')) for p in builder.mapping_sets()}
        self.assertEqual(declared, found)


class AlignmentModuleTests(unittest.TestCase):
    """The module must import the core, and the core must not import it back."""

    @classmethod
    def setUpClass(cls):
        cls.module = Graph().parse(builder.MODULE, format='turtle')
        cls.core = Graph()
        for path in sorted((ROOT / 'ontology').glob('*.ttl')):
            if path.name != builder.BUNDLE:
                cls.core.parse(path, format='turtle')

    def test_module_declares_itself_and_imports_the_core(self):
        self.assertIn((ALIGNMENTS, None, OWL.Ontology), self.module)
        self.assertIn((ALIGNMENTS, OWL.imports, CORE), self.module)

    def test_core_does_not_import_the_alignment_module(self):
        """Loading vcf-core must not drag in outward alignments."""
        self.assertNotIn((None, OWL.imports, ALIGNMENTS), self.core)

    def test_every_subject_is_a_vcf_core_term(self):
        for predicate in (SKOS.exactMatch, SKOS.closeMatch, SKOS.broadMatch,
                          SKOS.narrowMatch, SKOS.relatedMatch):
            for subject, _, _ in self.module.triples((None, predicate, None)):
                self.assertTrue(str(subject).startswith('https://w3id.org/vcf-core/vocab#'),
                                f'{subject} is not a vcf-core term')

    def test_bh25_assertions_are_not_in_the_module(self):
        """Third-party subjects stay in bh25/; the module speaks only for vcf-core."""
        for path in sorted((ROOT / 'mappings/bh25').glob('*.sssom.tsv')):
            for row in builder.read_set(path)[2]:
                self.assertFalse(row['subject_id'].startswith('vcfc:'),
                                 f'{path.name} asserts about a vcf-core term')

    def test_no_owl_equivalence_between_vocabularies(self):
        """SKOS mapping properties only: owl:equivalentClass would merge models."""
        for predicate in (OWL.equivalentClass, OWL.equivalentProperty, OWL.sameAs):
            self.assertEqual(list(self.module.triples((None, predicate, None))), [],
                             f'{predicate} must not be used for cross-vocabulary alignment')

    def test_reified_provenance_resolves_to_a_real_mapping(self):
        axioms = list(self.module.subjects(None, OWL.Axiom))
        self.assertTrue(axioms, 'no per-mapping provenance emitted')
        for axiom in axioms:
            source = self.module.value(axiom, OWL.annotatedSource)
            predicate = self.module.value(axiom, OWL.annotatedProperty)
            target = self.module.value(axiom, OWL.annotatedTarget)
            self.assertIn((source, predicate, target), self.module,
                          f'provenance for {source} {predicate} {target} has no mapping')


if __name__ == '__main__':
    unittest.main()
