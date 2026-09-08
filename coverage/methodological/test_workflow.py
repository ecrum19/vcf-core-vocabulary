"""Failure-oriented tests for the measurement, independent of vocabulary validation."""
import json
import tempfile
import unittest
from pathlib import Path

from rdflib import Graph

import workflow as w
from evidence import catalogue, compare_reserved_definitions, graph_fingerprint, rule_scope
from extract import extract


class ExtractionTests(unittest.TestCase):
    def test_scope_literals_context_and_changelog(self):
        tex = r'''\section{The VCF specification}
\subsection{Fixed fields}
\begin{enumerate}
\item CHROM --- chromosome: Values must be strings with \verb|%| permitted.
(String, Required).
\item REF --- reference: Values must be strings with \verb|%| permitted.
(String, Required).
\end{enumerate}
\begin{verbatim}
This example must not become an obligation.
\end{verbatim}
Positions are sorted numerically, in increasing order.
% This comment must not be extracted.
\section{BCF specification}
BCF must be binary.
\section{List of changes}
\subsection{Changes between VCFv4.5 and VCFv4.4}
\begin{itemize}
\item Added a requirement.
A continuation paragraph must stay in the changelog.
\end{itemize}
'''
        result = extract('4.5', tex, 'test')
        statements = result['candidates']
        self.assertEqual(len(result['changes']), 1)
        self.assertNotIn('binary', ' '.join(c['text'] for c in statements))
        self.assertNotIn('example must', ' '.join(c['text'] for c in statements))
        self.assertNotIn('comment must', ' '.join(c['text'] for c in statements))
        strings = [c for c in statements if 'Values must' in c['text']]
        self.assertEqual(len(strings), 2)
        self.assertNotEqual(strings[0]['requirementId'], strings[1]['requirementId'])
        self.assertIn('%', strings[0]['text'])
        sorted_position = next(c for c in statements if 'Positions are sorted' in c['text'])
        self.assertEqual(sorted_position['discovery'], ['declarative'])
        for candidate in statements:
            self.assertLess(candidate['lineEnd'], result['statistics']['vcfBoundaryLine'])

    def test_missing_bcf_boundary_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'missing BCF boundary'):
            extract('4.5', '\\section{VCF}\nIt must hold.', 'test')

    def test_number_changes_never_exact_align(self):
        one = extract('4.1', '\\section{VCF}\nThere must be 1 value.\n\\section{BCF specification}', 'x')
        two = extract('4.2', '\\section{VCF}\nThere must be 2 values.\n\\section{BCF specification}', 'y')
        corpus = w.initial_corpus([one, two])
        self.assertEqual(len(corpus), 2)

    def test_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'source.tex'
            path.write_text('tampered')
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                w.verified_source({'file': 'source.tex', 'sha256': '0'*64}, Path(tmp))


class TraceTests(unittest.TestCase):
    def setUp(self):
        self.groups = {'REQ-test': {'id': 'REQ-test', 'text': 'A value must be valid.',
                                   'members': [], 'versions': ['4.3', '4.5']}}
        self.target = {'id': 'rule:test', 'type': 'rule', 'text': 'A value must be valid.',
                       'versions': ['4.5'], 'fingerprint': 'pinned-rule'}
        self.review = {'status': 'requirement', 'kind': 'validity', 'reviewer': 'Test reviewer',
                       'reason': 'Synthetic assessment for failure testing.', 'mappingComplete': True,
                       'evidence': [{'target': 'rule:test', 'fingerprint': 'pinned-rule',
                                     'role': 'enforcement', 'assessment': 'full', 'versions': ['4.5'],
                                     'reason': 'Synthetic full mapping for 4.5 only.'}]}

    def trace(self):
        return w.trace(self.groups, {'REQ-test': self.review}, [self.target])

    def test_unreviewed_suggestion_is_never_credit(self):
        rows, errors = w.trace(self.groups, {}, [self.target])
        self.assertFalse(errors)
        self.assertTrue(rows[0]['suggestions'])
        self.assertEqual(rows[0]['finding'], 'unassessed')
        self.assertEqual(rows[0]['coveredVersions'], [])

    def test_partial_version_mapping_cannot_claim_union(self):
        rows, errors = self.trace()
        self.assertFalse(errors)
        self.assertEqual(rows[0]['coveredVersions'], ['4.5'])
        self.assertEqual(rows[0]['unmappedVersions'], ['4.3'])
        self.assertEqual(rows[0]['dischargeStatus'], 'partial')

    def test_multiple_overlays_can_cover_union(self):
        second = dict(self.target, id='rule:43', versions=['4.3'])
        self.review['evidence'].append(dict(self.review['evidence'][0], target='rule:43', versions=['4.3']))
        rows, errors = w.trace(self.groups, {'REQ-test': self.review}, [self.target, second])
        self.assertFalse(errors)
        self.assertEqual(rows[0]['dischargeStatus'], 'full')

    def test_wrong_version_is_a_build_error(self):
        self.review['evidence'][0]['versions'] = ['4.3', '4.5']
        rows, errors = self.trace()
        self.assertIn('version-mismatched', errors[0])
        self.assertEqual(rows[0]['finding'], 'version-mismatched')
        self.assertNotIn('4.3', rows[0]['coveredVersions'])

    def test_dangling_or_changed_rule_fails(self):
        with self.assertRaisesRegex(ValueError, 'dangling evidence'):
            w.trace(self.groups, {'REQ-test': self.review}, [])
        self.target['fingerprint'] = 'changed-query-with-same-name'
        with self.assertRaisesRegex(ValueError, 'evidence changed'):
            self.trace()

    def test_incomplete_mapping_and_partial_evidence_do_not_discharge(self):
        self.review['mappingComplete'] = False
        rows, _ = self.trace()
        self.assertEqual(rows[0]['coveredVersions'], [])
        self.review['mappingComplete'] = True
        self.review['evidence'][0]['assessment'] = 'partial'
        rows, _ = self.trace()
        self.assertEqual(rows[0]['coveredVersions'], [])

    def test_unknown_python_scope_requires_reason(self):
        self.target.update(type='decoded', versions=[])
        with self.assertRaisesRegex(ValueError, 'unknown target scope'):
            self.trace()
        self.review['evidence'][0]['scopeReason'] = 'Reviewed control flow supports VCF 4.5.'
        rows, errors = self.trace()
        self.assertFalse(errors)
        self.assertEqual(rows[0]['coveredVersions'], ['4.5'])

    def test_exclusions_need_recorded_scope(self):
        self.review = {k:v for k,v in self.review.items() if k not in {'evidence', 'mappingComplete'}}
        self.review.update(status='excluded', kind='processing')
        with self.assertRaisesRegex(ValueError, 'scopeReason'):
            self.trace()
        self.review['scopeReason'] = 'Requirements on implementations are outside vocabulary scope.'
        rows, _ = self.trace()
        self.assertEqual(rows[0]['finding'], 'out of scope')
        self.assertEqual(rows[0]['coveredVersions'], [])

    def test_duplicate_cannot_discard_an_earlier_version(self):
        self.groups['REQ-target'] = dict(self.groups['REQ-test'], id='REQ-target', versions=['4.5'])
        duplicate = {'status': 'duplicate-of', 'target': 'REQ-target', 'reviewer': 'Tester', 'reason': 'test'}
        with self.assertRaisesRegex(ValueError, 'lose version applicability'):
            w.trace(self.groups, {'REQ-test': duplicate, 'REQ-target': self.review}, [self.target])

    def test_split_preserves_source_versions(self):
        children = ['MAN-a', 'MAN-b']
        for child in children:
            self.groups[child] = dict(self.groups['REQ-test'], id=child, manual={'parent': 'REQ-test'})
        reviews = {'REQ-test': {'status': 'split-into', 'reviewer': 'Tester', 'reason': 'Two obligations', 'children': children},
                   **{child: self.review for child in children}}
        rows, _ = w.trace(self.groups, reviews, [self.target])
        self.assertEqual(next(r for r in rows if r['id'] == 'REQ-test')['finding'], 'split')
        for child in children:
            self.groups[child]['versions'] = ['4.5']
        with self.assertRaisesRegex(ValueError, 'split loses version'):
            w.trace(self.groups, reviews, [self.target])


class EvidenceTests(unittest.TestCase):
    def test_literal_definition_comparison_exposes_missing_and_wrong_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'snapshot.json').write_text(json.dumps({'definitions': [
                {'kind': 'INFO', 'id': 'AC', 'number': 'R', 'type': 'Integer'},
                {'kind': 'INFO', 'id': 'AF', 'number': 'A', 'type': 'Float'}]}))
            extraction = {'version': '4.3', 'candidates': [
                {'id': key, 'reservedField': {'kind': 'INFO', 'key': key, 'number': 'A', 'type': typ}}
                for key, typ in [('AC', 'Integer'), ('AF', 'Float'), ('MISSING', 'String')]]}
            entry = {'reservedKeys': {'mode': 'snapshot', 'snapshot': 'snapshot.json'}}
            result = compare_reserved_definitions([extraction], [entry], root)['versions'][0]
            self.assertEqual((result['exact'], result['different'], result['missing']), (1, 1, 1))
            self.assertEqual(result['rows'][0]['artifactDefinitions'][0]['number'], 'R')

    def test_real_shape_deletion_invalidates_reviewed_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'shacl').mkdir()
            (root / 'tests').mkdir()
            (root / 'tests/semantic_validation.py').write_text('def validate(): pass\n')
            (root / 'coverage/curated').mkdir(parents=True)
            (root / 'coverage/curated/check_serialization.py').write_text('def inspect(): pass\n')
            shape_file = root / 'shacl/test.ttl'
            shape_file.write_text('''@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix vcfc: <https://w3id.org/vcf-core/vocab#> .
vcfc:VersionRule a sh:NodeShape ; sh:targetClass vcfc:VCFFile ; sh:sparql [
 sh:message "A value must be valid." ;
 sh:select 'SELECT $this WHERE { $this vcfc:fileFormat "VCFv4.3" ; vcfc:p ?v . }' ] .
''')
            targets = catalogue(root, w.ALL_VERSIONS, {'areas': []})
            target = next(t for t in targets if t['type'] == 'rule')
            groups = {'REQ-test': {'id': 'REQ-test', 'text': 'A value must be valid.', 'members': [], 'versions': ['4.3']}}
            reviews = {'REQ-test': {'status': 'requirement', 'kind': 'validity', 'reviewer': 'Tester',
                                   'reason': 'Synthetic test', 'mappingComplete': True, 'evidence': [
                                       {'target': target['id'], 'fingerprint': target['fingerprint'],
                                        'versions': ['4.3'], 'role': 'enforcement', 'assessment': 'full', 'reason': 'Synthetic rule'}]}}
            self.assertEqual(w.trace(groups, reviews, targets)[0][0]['dischargeStatus'], 'full')
            shape_file.unlink()
            with self.assertRaisesRegex(ValueError, 'dangling evidence'):
                w.trace(groups, reviews, catalogue(root, w.ALL_VERSIONS, {'areas': []}))

    def test_blank_node_ids_do_not_affect_fingerprints(self):
        a = Graph().parse(data='@prefix x: <https://test/> . x:s x:p [ x:q "value" ].', format='turtle')
        b = Graph().parse(data='@prefix x: <https://test/> . x:s x:p _:other . _:other x:q "value" .', format='turtle')
        self.assertEqual(graph_fingerprint(a), graph_fingerprint(b))

    def test_earlier_reserved_terms_keep_scope_and_semantic_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'ontology/versions').mkdir(parents=True)
            (root / 'tests').mkdir()
            (root / 'tests/semantic_validation.py').write_text('def validate(): pass\n')
            (root / 'coverage/curated').mkdir(parents=True)
            (root / 'coverage/curated/check_serialization.py').write_text('def inspect(): pass\n')
            source = root / 'ontology/versions/early.ttl'
            source.write_text('''@prefix v: <https://w3id.org/vcf-core/vocab#> .
v:Early a v:FormatFieldDefinition; v:fieldId "CN";
 v:reservedIn "VCFv4.1"; v:fieldDescription "Reserved FORMAT CN declaration." .
''')
            targets = catalogue(root, w.ALL_VERSIONS, {'areas': []})
            term = next(t for t in targets if t['type'] == 'term')
            self.assertEqual(term['versions'], ['4.1'])
            self.assertEqual(term['reservedField']['key'], 'CN')
            source.write_text(source.read_text().replace('declaration.', 'changed meaning.'))
            changed = next(t for t in catalogue(root, w.ALL_VERSIONS, {'areas': []}) if t['id'] == term['id'])
            self.assertNotEqual(term['fingerprint'], changed['fingerprint'])
            byte_checker = next(t for t in targets if t['id'] == 'serialization:inspect')
            self.assertEqual(byte_checker['versions'], w.ALL_VERSIONS)

    def test_policy_confirmation_does_not_award_requirement_credit(self):
        groups = {'REQ-test': {'id': 'REQ-test', 'text': 'A value must be valid.',
                              'members': [], 'versions': ['4.5']}}
        decisions = {'assessmentPolicy': [{'id': 'coverage-credit', 'status': 'agreed',
                     'reviewer': 'Owner', 'reason': 'Separate meaning from declarations.',
                     'scope': 'Method only', 'qualification': 'Complex meaning requires judgment.'}],
                     'changelog': {}}
        rows, errors = w.trace(groups, {}, [])
        self.assertFalse(errors)
        self.assertEqual(rows[0]['coveredVersions'], [])
        register = w.review_register(groups, rows, decisions)
        self.assertIn('Complex meaning requires judgment.', register)
        self.assertIn('does not constitute approval of every mapping', register)

    def test_unknown_scope_not_guessed_from_filename_or_message(self):
        self.assertEqual(rule_scope('SELECT $this WHERE { FILTER(?version < "VCFv4.5") }', w.ALL_VERSIONS)[0], [])
        self.assertEqual(rule_scope('SELECT $this WHERE { $this vcfc:fileFormat "VCFv4.3" ; vcfc:p ?v . }', w.ALL_VERSIONS)[0], ['4.3'])
        # A gate on only one UNION arm is not a common version gate.
        self.assertEqual(rule_scope('SELECT $this WHERE { { $this vcfc:fileFormat "VCFv4.3" . } UNION { $this vcfc:p ?v . } }', w.ALL_VERSIONS)[0], [])


class AlignmentTests(unittest.TestCase):
    def setUp(self):
        self.groups = {rid: {'id': rid, 'text': rid, 'versions': [v], 'members': [{'id': rid, 'version': v}]}
                       for rid, v in [('A', '4.3'), ('B', '4.4'), ('C', '4.5')]}

    def decision(self, source, target, relation='same'):
        return dict(source=source, target=target, relation=relation, reviewer='Tester', reason='Synthetic alignment')

    def test_reviewer_selected_id_survives_and_no_occurrence_is_lost(self):
        groups, aliases, _ = w.apply_alignments(self.groups, [self.decision('A', 'B'), self.decision('C', 'B')])
        self.assertEqual(list(groups), ['B'])
        self.assertEqual(aliases, {'A': 'B', 'C': 'B'})
        self.assertEqual(groups['B']['versions'], ['4.3', '4.4', '4.5'])
        self.assertEqual({m['id'] for m in groups['B']['members']}, {'A', 'B', 'C'})

    def test_transitive_merge_cannot_contradict_rejected_pair(self):
        decisions = [self.decision('A', 'C', 'different'), self.decision('A', 'B'), self.decision('B', 'C')]
        with self.assertRaisesRegex(ValueError, 'different alignment collapsed'):
            w.apply_alignments(self.groups, decisions)

    def test_missing_reviewer_does_not_accept_fuzzy_alignment(self):
        decision = self.decision('A', 'B')
        del decision['reviewer']
        with self.assertRaisesRegex(ValueError, 'reviewer required'):
            w.apply_alignments(self.groups, [decision])


class FullCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts, cls.stats, cls.errors = w.build()

    def test_all_five_pins_and_known_obligation_counts(self):
        expected = {'4.1': 27, '4.2': 27, '4.3': 64, '4.4': 105, '4.5': 115}
        for row in self.stats['byVersion']:
            strength = row['byStrength']
            self.assertEqual(strength.get('obligation', 0) + strength.get('prohibition', 0), expected[row['version']])

    def test_every_occurrence_belongs_to_exactly_one_corpus_entry(self):
        extracted = json.loads(self.artifacts['extracted.json'])
        corpus = json.loads(self.artifacts['corpus.json'])
        raw_ids = [c['id'] for v in extracted['versions'] for c in v['candidates']]
        grouped_ids = [c['id'] for r in corpus['requirements'] for c in r['members']]
        self.assertEqual(sorted(raw_ids), sorted(grouped_ids))
        self.assertEqual(len(grouped_ids), len(set(grouped_ids)))

    def test_seven_seeds_are_found_without_automatic_credit(self):
        seeds = json.loads(self.artifacts['seed-checks.json'])
        self.assertEqual(len(seeds), 7)
        for seed in seeds:
            self.assertTrue(seed['candidates'])
            self.assertTrue(seed['targets'])
        decisions = w.read_json(w.HERE / 'decisions.json')
        if not decisions['triage']:
            self.assertEqual(self.stats['dischargedAllApplicableVersions'], 0)
            self.assertEqual(self.stats['findings'], {'unassessed': self.stats['corpusEntries']})

    def test_generation_is_byte_reproducible(self):
        second, _, _ = w.build()
        self.assertEqual(self.artifacts, second)

    def test_check_detects_missing_and_modified_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            here = Path(tmp)
            (here / 'generated').mkdir()
            (here / 'generated/x.json').write_bytes(b'old')
            self.assertEqual(w.check_outputs({'x.json': b'new', 'missing.json': b'new'}, here), ['x.json', 'missing.json'])

    def test_optional_audit_is_separate_and_checked_when_requested(self):
        primary = w.selected_outputs(self.artifacts)
        expanded = w.selected_outputs(self.artifacts, audit=True)
        self.assertEqual(set(primary), w.PRIMARY_OUTPUTS)
        self.assertIn('audit/extracted.json', expanded)
        self.assertNotIn('extracted.json', expanded)
        with tempfile.TemporaryDirectory() as tmp:
            here = Path(tmp)
            for name, raw in expanded.items():
                path = here / 'generated' / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            (here / 'generated/audit/extracted.json').unlink()
            self.assertEqual(w.check_outputs(primary, here), [])
            self.assertEqual(w.check_outputs(expanded, here), ['audit/extracted.json'])

    def test_duplicate_json_keys_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'decision.json'
            path.write_text('{"triage": {}, "triage": {}}')
            with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
                w.read_json(path)

    def test_reconciliation_requires_explanation_for_unchanged_requirement(self):
        change = {'id': 'C1', 'text': 'Updated Number=P', 'headings': ['Changes between VCFv4.5 and VCFv4.4']}
        groups = {'REQ-one': {'text': 'Number=P', 'members': [], 'versions': ['4.4', '4.5']}}
        decision = {'status': 'linked', 'requirements': ['REQ-one'], 'reviewer': 'Tester', 'reason': 'Test link'}
        diffs = w.transitions(groups)
        with self.assertRaisesRegex(ValueError, 'explain disagreementReason'):
            w.reconcile([{'changes': [change]}], groups, {'C1': decision}, diffs)
        decision['disagreementReason'] = 'The feature is already in the pinned 4.4 source; the changelog also contains errata.'
        report = w.reconcile([{'changes': [change]}], groups, {'C1': decision}, diffs)
        self.assertEqual(report['changes'][0]['status'], 'linked')

    def test_unlisted_transition_can_be_explained_without_inventing_changelog(self):
        groups = {'REQ-one': {'text': 'New wording', 'members': [], 'versions': ['4.5']}}
        diffs = w.transitions(groups)
        notes = {'4.4->4.5:REQ-one': {'status': 'specification-omission', 'reviewer': 'Tester', 'reason': 'No matching changelog entry.'}}
        report = w.reconcile([], groups, {}, diffs, notes)
        self.assertFalse(report['derivedChangesWithoutReviewedChangelogLink'][-1]['requirements'])
        self.assertEqual(len(report['explainedTransitionObservations']), 1)


if __name__ == '__main__':
    unittest.main()
