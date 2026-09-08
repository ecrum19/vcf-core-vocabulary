"""Include the independent measurement's regression tests in the repository suite."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'coverage/methodological'))
import test_workflow


def load_tests(loader, tests, pattern):
    return loader.loadTestsFromModule(test_workflow)
