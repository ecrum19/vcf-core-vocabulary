"""The cleanup command must preserve authored inputs and required reports."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('repository_clean', Path(__file__).resolve().parents[1] / 'scripts/clean.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RepositoryCleanupTests(unittest.TestCase):
    def test_cleaning_desktop_metadata_does_not_invalidate_validation(self):
        gate_spec = importlib.util.spec_from_file_location('validation_gate',
                    Path(__file__).resolve().parents[1] / 'scripts/validation-gate.py')
        gate = importlib.util.module_from_spec(gate_spec)
        gate_spec.loader.exec_module(gate)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'examples').mkdir()
            source = root / 'examples/source.vcf'
            source.write_text('source fixture')
            with patch.object(gate, 'ROOT', root):
                before = gate.fingerprint()
                (root / 'examples/.DS_Store').write_text('desktop metadata')
                (root / 'examples/__pycache__').mkdir()
                (root / 'examples/__pycache__/cached.pyc').write_bytes(b'cache')
                self.assertEqual(gate.fingerprint(), before)
                module.clean(root)
                self.assertEqual(gate.fingerprint(), before)
                source.write_text('changed source fixture')
                self.assertNotEqual(gate.fingerprint(), before)

    def test_cleanup_preserves_sources_reports_exports_and_dependencies(self):
        retained = [
            'coverage/methodological/decisions.json', 'coverage/methodological/sources/VCFv4.5.tex',
            'coverage/methodological/probes/rules.json', 'coverage/methodological/generated/report.md',
            'coverage/curated/inventory.json', 'coverage/curated/generated/report.json',
            'tests/generated/validation.json', 'SWAT4HCLS_2027/main.tex',
            'SWAT4HCLS_2027/template/ceurart.cls', 'SWAT4HCLS_2027/paper-draft.pdf',
            '.venv/lib/__pycache__/keep.pyc', 'node_modules/.DS_Store', '.git/config',
        ]
        disposable = ['site/index.html', 'SWAT4HCLS_2027/.build/main.log',
                      'SWAT4HCLS_2027/main.aux', 'coverage/methodological/generated/audit/extracted.json',
                      'coverage/methodological/__pycache__/workflow.pyc', '.DS_Store']
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in retained + disposable:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('retained input or disposable fixture')
            module.clean(root)
            for name in retained:
                self.assertTrue((root / name).is_file(), name)
            for name in disposable:
                self.assertFalse((root / name).exists(), name)
            self.assertEqual(module.clean(root), [])
