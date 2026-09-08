"""The version-scoped artifacts must stay in step with ontology/versions/registry.json.

These checks fail when a version is added to the table without rerunning the
generators, and when an artifact is hand-edited away from what the table implies.
"""
import json
import sys
import unittest
from pathlib import Path

from rdflib import Graph, Namespace, RDF
from rdflib.namespace import OWL, RDFS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import version_registry  # noqa: E402  (path set above)

V = Namespace('https://w3id.org/vcf-core/vocab#')
SH = Namespace('http://www.w3.org/ns/shacl#')


class VersionRegistryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = version_registry.load()
        cls.versions = version_registry.versions(cls.registry)
        cls.vocabulary = Graph().parse(ROOT / 'ontology/vcf-core-vocabulary.ttl')
        cls.ocg = (ROOT / 'ocg.config.json').read_text()

    def test_table_validates(self):
        self.assertTrue(self.versions)
        self.assertIn(self.registry['current'], [v['id'] for v in self.versions])

    def test_exactly_one_registry_mode_version(self):
        # The full reserved-key generator writes one graph at a time; a second
        # registry-mode version would silently overwrite the first.
        full = version_registry.by_mode('registry', self.registry)
        self.assertEqual([v['id'] for v in full], [self.registry['current']])

    def test_file_classes_are_declared(self):
        for entry in self.versions:
            term = V[entry['className']]
            with self.subTest(version=entry['id']):
                self.assertIn((term, RDF.type, OWL.Class), self.vocabulary)
                self.assertIn((term, RDFS.subClassOf, V.VCFFile), self.vocabulary)

    def test_no_stray_file_classes(self):
        declared = {str(s)[len(str(V)):] for s in self.vocabulary.subjects(RDFS.subClassOf, V.VCFFile)}
        self.assertEqual(declared, {v['className'] for v in self.versions})

    def test_generated_class_block_is_delimited(self):
        text = (ROOT / 'ontology/vcf-core-vocabulary.ttl').read_text()
        begin = text.find('# BEGIN GENERATED VERSION CLASSES')
        end = text.find('# END GENERATED VERSION CLASSES')
        self.assertGreater(begin, 0, 'generated-block markers are missing')
        self.assertGreater(end, begin)
        block = text[begin:end]
        for entry in self.versions:
            self.assertIn(f'vcfc:{entry["className"]} a owl:Class', block)

    def test_overlays_exist_and_gate_their_class(self):
        for entry in self.versions:
            path = ROOT / f'shacl/vcf-{entry["id"]}.shacl.ttl'
            with self.subTest(version=entry['id']):
                self.assertTrue(path.exists(), f'{path.name} was never generated')
                shapes = Graph().parse(path)
                gate = V[entry['className'] + 'Gate']
                self.assertIn((gate, RDF.type, SH.NodeShape), shapes)
                self.assertIn((gate, SH.targetClass, V[entry['className']]), shapes)

    def test_reserved_key_artifacts_exist(self):
        for entry in self.versions:
            reserved = entry['reservedKeys']
            with self.subTest(version=entry['id']):
                self.assertTrue((ROOT / reserved['graph']).exists())
                if reserved['mode'] == 'snapshot':
                    snapshot = json.loads((ROOT / reserved['snapshot']).read_text())
                    self.assertEqual(snapshot['version'], entry['id'])
                    self.assertEqual(snapshot['source'], entry['source'])
                    self.assertTrue(snapshot['definitions'])

    def test_ocg_config_lists_every_version(self):
        # Imported here so the test does not depend on the generator's filename
        # being importable as a module name.
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'build_shacl_profiles', ROOT / 'scripts/build-shacl-profiles.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for key, label, artifact, description in module.ocg_entries(self.registry):
            with self.subTest(key=key):
                self.assertIn(f'"key": "{key}"', self.ocg)
                self.assertIn(f'"path": "{artifact}"', self.ocg)
                self.assertIn(f'"description": "{description}"', self.ocg)


if __name__ == '__main__':
    unittest.main()
