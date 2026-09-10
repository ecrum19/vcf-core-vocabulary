"""Regression tests for errors that could inflate or silently change the measure."""
import json
import contextlib
import io
from pathlib import Path
import sys
import unittest
import tempfile
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "scripts"))
import assess
from source import sections, declarations
from source_review import make_audit, resolved, save_annotations, unsaved
from rdflib import Graph, Literal, URIRef


class MeasurementTests(unittest.TestCase):
    def assertion_fixture(self):
        sources, requirements = self.source_review_fixture()
        baseline = make_audit(sources, requirements, {})
        inventory = {r["id"]: dict(sourceFingerprint=r["sourceFingerprint"], assertions=[],
                     exclusions=["Heading or excluded layout."], reviewQuestions=[],
                     disposition="context-only", note="Checked source scope.") for r in baseline}
        example = next(r for r in baseline if r["title"] == "An example")
        inventory[example["id"]].update(disposition="mapped", exclusions=[], assertions=[
            dict(id="A1", statement="Illustrative information belongs to R1.",
                 start=example["start"], end=example["end"], requirements=["R1"],
                 caseIds=[], testGap="No targeted example case.")])
        return sources, requirements, inventory, example["id"]

    def test_explicit_assertion_links_are_independent_of_anchor_overlap(self):
        sources, requirements, inventory, sid = self.assertion_fixture()
        row = next(r for r in make_audit(sources, requirements, {}, inventory) if r["id"] == sid)
        self.assertEqual(row["anchorRequirements"], [])
        self.assertEqual(row["requirements"], ["R1"])
        self.assertEqual(row["assertions"][0]["testStatus"], "no-targeted-test")
        self.assertEqual(row["requirementTests"], [{"requirement": "R1", "caseIds": []}])

    def test_same_requirement_case_does_not_automatically_cover_an_assertion(self):
        sources, requirements, inventory, sid = self.assertion_fixture()
        test = {"query": "example.rq", "expected": [["value"]]}
        cases = [dict(id="C1", version="4.5", requirement="R1", preservation={"both": test}, structure={"both": test})]
        row = next(r for r in make_audit(sources, requirements, {}, inventory, cases) if r["id"] == sid)
        self.assertEqual(row["requirementTests"][0]["caseIds"], ["C1"])
        self.assertEqual(row["assertions"][0]["testStatus"], "no-targeted-test")
        inventory[sid]["assertions"][0]["caseIds"] = ["C1"]
        row = next(r for r in make_audit(sources, requirements, {}, inventory, cases) if r["id"] == sid)
        self.assertEqual(row["assertions"][0]["testStatus"], "partial-tests")
        inventory[sid]["assertions"][0]["testGap"] = ""
        row = next(r for r in make_audit(sources, requirements, {}, inventory, cases) if r["id"] == sid)
        self.assertEqual(row["assertions"][0]["testStatus"], "targeted-tests")

    def test_unrelated_missing_and_empty_answer_cases_cannot_support_assertions(self):
        sources, requirements, inventory, sid = self.assertion_fixture()
        inventory[sid]["assertions"][0]["caseIds"] = ["C1"]
        with self.assertRaisesRegex(AssertionError, "Unknown assertion case"):
            make_audit(sources, requirements, {}, inventory)
        cases = [dict(id="C1", version="4.4", requirement="R1")]
        with self.assertRaisesRegex(AssertionError, "Unrelated assertion case"):
            make_audit(sources, requirements, {}, inventory, cases)
        cases[0]["version"] = "4.5"
        with self.assertRaisesRegex(AssertionError, "no answer test"):
            make_audit(sources, requirements, {}, inventory, cases)

    def test_review_question_prevents_acceptance_even_if_disposition_is_changed(self):
        sources, requirements, inventory, sid = self.assertion_fixture()
        inventory[sid]["reviewQuestions"] = ["Which conflicting source value governs?"]
        decision = dict(disposition="mapped", note="A note alone does not resolve the oracle.",
                        sourceFingerprint=inventory[sid]["sourceFingerprint"])
        row = next(r for r in make_audit(sources, requirements, {sid: decision}, inventory) if r["id"] == sid)
        self.assertEqual(row["disposition"], "needs-review")
        self.assertIn("reviewQuestions", row["reviewIssue"])
        self.assertFalse(resolved([row]))

    def test_incomplete_or_stale_assertion_inventory_fails(self):
        sources, requirements, inventory, sid = self.assertion_fixture()
        inventory[sid]["sourceFingerprint"] = "stale"
        with self.assertRaisesRegex(AssertionError, "Stale assertion inventory"):
            make_audit(sources, requirements, {}, inventory)
        del inventory[sid]
        with self.assertRaises(KeyError):
            make_audit(sources, requirements, {}, inventory)

    def test_original_annotations_remain_visible_without_becoming_acceptance(self):
        sources, requirements, inventory, sid = self.assertion_fixture()
        prior = {sid: dict(disposition="needs-requirement", note="User's earlier finding.", relatedRequirements=[])}
        rows = make_audit(sources, requirements, {}, inventory, previous=prior)
        row = next(r for r in rows if r["id"] == sid)
        self.assertEqual(row["priorAnnotation"], prior[sid])
        self.assertEqual(row["disposition"], "mapped")
        self.assertFalse(unsaved(rows))
        worksheet = json.loads(json.dumps(rows))
        next(r for r in worksheet if r["id"] == sid)["assertions"][0]["testGap"] = "tampered"
        with self.assertRaisesRegex(AssertionError, "authored source-assertions"):
            save_annotations(worksheet, rows, {})

    def source_review_fixture(self):
        text = '\n'.join([r'\section{The VCF specification}', 'Information to represent.',
                          r'\subsection{An example}', 'Illustrative information.', r'\section{BCF}'])
        requirements = [{"id": "R1", "versions": ["4.5"], "anchors": {"4.5": {"start": 1, "end": 2}}}]
        return {"4.5": text}, requirements

    def test_source_annotations_survive_rebuild_without_accepting_audit(self):
        sources, requirements = self.source_review_fixture()
        current = make_audit(sources, requirements, {})
        worksheet = json.loads(json.dumps(current))
        row = next(r for r in worksheet if r["title"] == "An example")
        row.update(disposition="duplicate", note="Same information as R1.", relatedRequirements=["R1"])
        self.assertEqual(len(unsaved(worksheet)), 1)
        review = save_annotations(worksheet, current, {"sourceAudit": None})
        rebuilt = make_audit(sources, requirements, review["sourceSections"])
        saved = next(r for r in rebuilt if r["title"] == "An example")
        self.assertEqual(saved["disposition"], "duplicate")
        self.assertEqual(saved["note"], "Same information as R1.")
        self.assertEqual(saved["relatedRequirements"], ["R1"])
        self.assertEqual(saved["reviewIssue"], "")
        self.assertFalse(unsaved(rebuilt))
        self.assertFalse(resolved(rebuilt))
        self.assertIsNone(review["sourceAudit"])

    def test_legacy_user_wording_is_preserved_but_not_treated_as_resolved(self):
        sources, requirements = self.source_review_fixture()
        current = make_audit(sources, requirements, {})
        worksheet = json.loads(json.dumps(current))
        row = next(r for r in worksheet if r["title"] == "An example")
        row.pop("savedAnnotationFingerprint")
        row["disposition"] = "excluded: only an example"
        review = save_annotations(worksheet, current, {})
        saved = next(r for r in make_audit(sources, requirements, review["sourceSections"]) if r["title"] == "An example")
        self.assertEqual(saved["disposition"], "excluded: only an example")
        self.assertIn("Choose a documented disposition", saved["reviewIssue"])
        self.assertFalse(resolved([saved]))

    def test_mapped_and_duplicate_require_links_and_a_rationale(self):
        sources, requirements = self.source_review_fixture()
        row = next(r for r in make_audit(sources, requirements, {}) if r["title"] == "An example")
        for disposition in ("mapped", "duplicate"):
            decision = dict(sourceFingerprint=row["sourceFingerprint"], disposition=disposition, note="Checked.")
            reviewed_rows = make_audit(sources, requirements, {row["id"]: decision})
            self.assertIn("Link the requirements", next(r for r in reviewed_rows if r["id"] == row["id"])["reviewIssue"])
            decision.update(relatedRequirements=["R1"], note="")
            reviewed_rows = make_audit(sources, requirements, {row["id"]: decision})
            self.assertIn("rationale", next(r for r in reviewed_rows if r["id"] == row["id"])["reviewIssue"])

    def test_source_changes_invalidate_section_decision(self):
        sources, requirements = self.source_review_fixture()
        row = next(r for r in make_audit(sources, requirements, {}) if r["title"] == "An example")
        decision = dict(sourceFingerprint=row["sourceFingerprint"], disposition="duplicate", note="R1", relatedRequirements=["R1"])
        sources["4.5"] = sources["4.5"].replace("Illustrative information.", "New information.")
        changed = next(r for r in make_audit(sources, requirements, {row["id"]: decision}) if r["id"] == row["id"])
        self.assertIn("Source changed", changed["reviewIssue"])
        self.assertFalse(resolved([changed]))

    def test_save_refuses_deleted_sections_or_modified_generated_links(self):
        sources, requirements = self.source_review_fixture()
        current = make_audit(sources, requirements, {})
        with self.assertRaisesRegex(AssertionError, "sections were removed"):
            save_annotations(current[:-1], current, {})
        worksheet = json.loads(json.dumps(current))
        worksheet[1]["requirements"] = ["invented"]
        with self.assertRaisesRegex(AssertionError, "relatedRequirements"):
            save_annotations(worksheet, current, {})

    def test_build_refuses_to_overwrite_unsaved_annotations(self):
        sources, requirements = self.source_review_fixture()
        worksheet = make_audit(sources, requirements, {})
        worksheet[1]["note"] = "Work in progress."
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "generated").mkdir()
            path = folder / "generated/source-audit.json"
            text = json.dumps(worksheet)
            path.write_text(text)
            with patch.object(assess, "HERE", folder), patch.object(assess, "evaluate") as evaluate, patch.object(sys, "argv", ["assess.py", "build"]), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(assess.main(), 1)
                evaluate.assert_not_called()
                self.assertEqual(path.read_text(), text)

    def test_unassessed_components_never_become_full_credit(self):
        self.assertEqual(assess.status([]), "unassessed")
        self.assertEqual(assess.status(["unassessed"]), "unassessed")
        self.assertEqual(assess.status(["pass", "unassessed"]), "partial")
        self.assertEqual(assess.status(["pass", "fail"]), "partial")
        self.assertEqual(assess.status(["fail"]), "not-demonstrated")
        self.assertEqual(assess.status(["pass", "pass"]), "demonstrated")

    def test_review_requires_matching_evidence_and_named_decision(self):
        decision = dict(fingerprint="a", reviewer="reviewer", date="2026-09-10", rationale="checked")
        self.assertTrue(assess.reviewed(decision, "a"))
        self.assertFalse(assess.reviewed(decision, "changed"))
        self.assertFalse(assess.reviewed({"fingerprint": "a"}, "a"))
        self.assertFalse(assess.reviewed(None, "a"))

    def test_empty_graph_and_constant_answers_do_not_earn_credit(self):
        with self.assertRaisesRegex(ValueError, "without data"):
            assess.run_query(Graph(), 'SELECT ("42" AS ?x) WHERE {}', [["42"]], "preservation")
        with self.assertRaisesRegex(ValueError, "nonempty"):
            assess.run_query(Graph(), "SELECT ?x WHERE {?s ?p ?x}", [], "preservation")

    def test_wrong_and_duplicate_answers_fail(self):
        g = Graph()
        g.add((URIRef("urn:a"), assess.V.pos, Literal(42)))
        g.add((URIRef("urn:b"), assess.V.pos, Literal(42)))
        query = "PREFIX vcfc: <https://w3id.org/vcf-core/vocab#> SELECT ?x WHERE {?s vcfc:pos ?x}"
        self.assertEqual(assess.run_query(g, query, [["42"]], "structure")["status"], "fail")
        self.assertEqual(assess.run_query(g, query, [["43"], ["43"]], "structure")["status"], "fail")
        good = assess.run_query(g, query, [["42"], ["42"]], "structure")
        self.assertEqual(good["status"], "pass")
        self.assertTrue(good["predicateDeletionRejected"])

    def test_literal_decoding_cannot_be_called_structural(self):
        with self.assertRaisesRegex(ValueError, "cannot decode"):
            assess.run_query(Graph(), 'SELECT (STRBEFORE(?x, ":") AS ?y) WHERE {?s ?p ?x}', [["x"]], "structure")

    def test_section_audit_partitions_entire_sources_without_gaps(self):
        for path in (HERE / "sources").glob("*.tex"):
            text = path.read_text()
            ranges = sections(text)
            positions = [n for s in ranges for n in range(s["start"], s["end"]+1)]
            self.assertEqual(positions, list(range(1, len(text.splitlines())+1)), path.name)
            self.assertTrue(any(s["zone"] == "bcf" for s in ranges))
            if path.name in {"VCFv4.3.tex", "VCFv4.4.tex", "VCFv4.5.tex"}:
                self.assertTrue(any(s["zone"] == "changes" for s in ranges))

    def test_extractor_excludes_example_declarations_and_keeps_source_lines(self):
        text = '\n'.join([
            r'\section{The VCF specification}', r'\subsection{An example}',
            '##INFO=<ID=EXAMPLE,Number=1,Type=String,Description="Not normative">',
            r'\section{INFO keys used for structural variants}',
            '##INFO=<ID=SVLEN,Number=A,Type=Integer,Description="Length">',
            r'\section{BCF}',
            '##INFO=<ID=BCF,Number=1,Type=String,Description="Excluded">'])
        rows = declarations(text)
        self.assertEqual([(d["key"], d["line"]) for d in rows], [("SVLEN", 5)])

    def test_version_mismatch_fails_before_evaluation(self):
        original = json.loads((HERE / "inputs/cases.json").read_text())
        bad = [dict(original[0], version="4.0")]
        read = Path.read_text
        def substituted(path, *args, **kwargs):
            return json.dumps(bad) if path == HERE / "inputs/cases.json" else read(path, *args, **kwargs)
        with patch.object(Path, "read_text", substituted), self.assertRaisesRegex(AssertionError, "Wrong-version"):
            assess.evaluate()

    def test_source_pin_failure_stops_before_assessment(self):
        read = Path.read_bytes
        def substituted(path):
            value = read(path)
            return value+b"changed" if path.name == "VCFv4.1.tex" else value
        with patch.object(Path, "read_bytes", substituted), self.assertRaisesRegex(AssertionError, "Source pin mismatch"):
            assess.evaluate()

    def test_stale_output_check_does_not_rewrite_or_accept_it(self):
        summary = json.loads((HERE / "generated/summary.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "generated").mkdir()
            path = folder / "generated/summary.json"
            path.write_text(assess.encoded(summary))
            (folder / "README.md").write_text(assess.result_block(summary))
            with patch.object(assess, "HERE", folder), patch.object(assess, "ROOT", folder), patch.object(assess, "evaluate", return_value={"summary.json": summary}), patch.object(sys, "argv", ["assess.py", "check"]), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(assess.main(), 0)
                path.write_text('{"tampered": true}\n')
                self.assertEqual(assess.main(), 1)
                self.assertEqual(path.read_text(), '{"tampered": true}\n')

    def test_review_gate_is_separate_from_reproducibility(self):
        summary = json.loads((HERE / "generated/summary.json").read_text())
        summary["pendingReviews"] = 1
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "generated").mkdir()
            (folder / "generated/summary.json").write_text(assess.encoded(summary))
            (folder / "README.md").write_text(assess.result_block(summary))
            with patch.object(assess, "HERE", folder), patch.object(assess, "ROOT", folder), patch.object(assess, "evaluate", return_value={"summary.json": summary}), patch.object(sys, "argv", ["assess.py", "check", "--require-reviewed"]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(assess.main(), 2)

    def test_current_summary_keeps_untested_requirements_in_denominator(self):
        summary = json.loads((HERE / "generated/summary.json").read_text())
        register = json.loads((HERE / "inputs/requirements.json").read_text())
        for row in summary["byVersion"]:
            expected = sum(row["version"] in r["versions"] for r in register)
            self.assertEqual(row["denominator"], expected)
            for axis in assess.AXES:
                self.assertEqual(sum(row[axis][s] for s in ("demonstrated", "partial", "not-demonstrated", "unassessed")), expected)
        self.assertEqual(summary["requirements"], len(register))


if __name__ == "__main__":
    unittest.main()
