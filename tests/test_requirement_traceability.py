"""Include the representation assessment's measurement tests in the repository suite."""
import importlib.util
from pathlib import Path


def load_tests(loader, tests, pattern):
    path = Path(__file__).resolve().parents[1] / "coverage/methodology/tests/test_assessment.py"
    spec = importlib.util.spec_from_file_location("coverage_measurement_tests", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return loader.loadTestsFromModule(module)
