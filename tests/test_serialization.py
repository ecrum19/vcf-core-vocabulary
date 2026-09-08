"""Source-byte serialization checks, and proof that line endings do not leak into the model.

VCF 4.5 sections 1-1.2 constrain the source stream, not the logical model, so the
vocabulary carries no term for encoding, byte-order-mark state or line terminator.
These tests supply the evidence in the only place it can exist: the bytes.
"""
from pathlib import Path
import importlib.util
import sys
import unittest

from rdflib.compare import isomorphic

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


serialization = _load('serialization', ROOT / 'coverage/curated/check_serialization.py')
examples = _load('vcf_examples', ROOT / 'scripts/vcf_examples.py')

LF = ROOT / 'examples/serialization/lf-line-endings.vcf'
CRLF = ROOT / 'examples/serialization/crlf-line-endings.vcf'


class SourceSerialization(unittest.TestCase):
    def test_every_fixture_satisfies_the_byte_requirements(self):
        for path in sorted(ROOT.glob('examples/**/*.vcf')):
            with self.subTest(fixture=path.relative_to(ROOT).as_posix()):
                self.assertEqual(serialization.inspect(path)['problems'], [])

    def test_both_permitted_line_terminators_are_exercised(self):
        self.assertEqual(serialization.inspect(LF)['lineTerminator'], 'LF')
        self.assertEqual(serialization.inspect(CRLF)['lineTerminator'], 'CRLF')

    def test_no_fixture_carries_a_byte_order_mark(self):
        for path in sorted(ROOT.glob('examples/**/*.vcf')):
            with self.subTest(fixture=path.relative_to(ROOT).as_posix()):
                self.assertFalse(serialization.inspect(path)['byteOrderMark'])

    def test_line_terminator_does_not_change_the_logical_graph(self):
        # Same base IRI for both, so any difference is content rather than naming.
        base = 'file://line-endings.vcf'
        self.assertTrue(isomorphic(examples.materialize(LF, base=base),
                                   examples.materialize(CRLF, base=base)))

    def test_a_byte_order_mark_is_detected(self):
        # Negative probe: the checker must actually fail a non-conforming stream.
        tmp = ROOT / 'tests/.bom-probe.vcf'
        try:
            tmp.write_bytes(b'\xef\xbb\xbf' + LF.read_bytes())
            result = serialization.inspect(tmp)
            self.assertTrue(result['byteOrderMark'])
            self.assertFalse(result['passed'])
        finally:
            tmp.unlink(missing_ok=True)

    def test_mixed_line_terminators_are_detected(self):
        tmp = ROOT / 'tests/.mixed-probe.vcf'
        try:
            tmp.write_bytes(CRLF.read_bytes() + b'chr1\t20\t.\tA\tG\t.\tPASS\tAF=0.5\tGT\t0/1\n')
            result = serialization.inspect(tmp)
            self.assertEqual(result['lineTerminator'], 'mixed')
            self.assertFalse(result['passed'])
        finally:
            tmp.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
