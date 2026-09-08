#!/usr/bin/env python3
"""Offline VCF requirement traceability. See README.md and DECISIONS.md."""
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import version_registry
from extract import digest, extract, normalize
from evidence import catalogue, compare_reserved_definitions, fingerprint

KINDS = {"representational", "validity", "serialization", "processing", "bcf"}
STATUSES = {"requirement", "not-a-requirement", "duplicate-of", "split-into", "excluded"}
ALL_VERSIONS = ["4.1", "4.2", "4.3", "4.4", "4.5"]
PRIMARY_OUTPUTS = {
    'report.md', 'summary.json', 'corpus.json', 'traceability.json',
    'evidence-catalogue.json', 'reserved-definition-comparison.json',
    'changelog-reconciliation.json', 'provenance.json',
}
LIMITS = [
    "Candidates are mechanically selected statements, not yet reviewed atomic requirements.",
    "Modal/declarative sweeps are incomplete; unselected prose and skipped regions remain auditable.",
    "Earlier specifications use less normative wording. Counts cannot rank versions by coverage.",
    "Exact text/context grouping is mechanical; fuzzy alignment and semantic applicability require decisions.",
    "Text absence is not withdrawal, and deprecation is not removal.",
    "Evidence suggestions are not discharges. Reviewed mappings establish traceability, not rule correctness or conformance.",
    "This workflow does not execute the vocabulary validators. Run the repository validation suite separately.",
]


def read_json(path):
    # Duplicate keys in a decision ledger would otherwise silently discard a review.
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key {key!r} in {path}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reviewed(record, label):
    require(isinstance(record, dict), f"{label}: expected an object")
    for key in ("reviewer", "reason"):
        require(isinstance(record.get(key), str) and record[key].strip(), f"{label}: nonempty {key} required")


def checked_versions(values, label, allowed=ALL_VERSIONS):
    require(isinstance(values, list) and bool(values) and len(values) == len(set(values))
            and set(values) <= set(allowed), f"{label}: nonempty distinct versions must be in {allowed}")
    return sorted(values)


def source_lock(root=ROOT, here=HERE):
    registry = version_registry.load(root / "ontology/versions/registry.json")
    entries = version_registry.versions(registry)
    require([v['id'] for v in entries] == ALL_VERSIONS, "workflow scope is VCF 4.1–4.5; review extractor before changing it")
    lock = read_json(here / "sources.lock.json")
    require(lock.get("schemaVersion") == 1, "unsupported source lock schema")
    require(set(lock['versions']) == set(ALL_VERSIONS), "source lock must contain all five versions")
    for version in entries:
        item = lock['versions'][version['id']]
        require(item['source'] == version['source'] and item['file'] == f"sources/{version['specFile']}",
                f"source registry drift for {version['id']}")
        reserved = version['reservedKeys']
        if reserved['mode'] == 'snapshot':
            expected = read_json(root / reserved['snapshot'])['sha256']
        else:
            match = re.search(r"^# SHA-256: ([a-f0-9]{64})$", (root / reserved['graph']).read_text(), re.M)
            require(match is not None, "current reserved registry has no source SHA-256")
            expected = match[1]
        require(item['sha256'] == expected, f"source pin disagrees with reserved-key artifact for {version['id']}")
    return lock


def verified_source(item, here=HERE):
    path = here / item['file']
    require(path.is_file(), f"missing {path}; run workflow.py fetch")
    raw = path.read_bytes()
    require(fingerprint(raw) == item['sha256'], f"source SHA-256 mismatch: {path}")
    return raw.decode('utf-8')


def fetch_sources(root=ROOT, here=HERE):
    lock = source_lock(root, here)
    # Validate the complete download before replacing any local snapshot.
    downloads = []
    for item in lock['versions'].values():
        raw = subprocess.check_output(['curl', '--fail', '--silent', '--show-error', '--location',
                                       '--max-time', '60', item.get('downloadUrl', item['source'])])
        require(fingerprint(raw) == item['sha256'], f"download hash mismatch for {item['file']}; existing files preserved")
        downloads.append((here / item['file'], raw))
    for path, raw in downloads:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    print("Downloaded and verified all five pinned sources.")


def guess_kind(text):
    if re.search(r"\b(?:implementations?|tools processing|parsers?)\b", text, re.I):
        return 'processing'
    if re.search(r"\b(?:byte order|UTF-8|line separator|tab.delimited|non-printable)\b", text, re.I):
        return 'serialization'
    return 'validity'


def initial_corpus(extractions):
    groups = {}
    for extraction in extractions:
        for candidate in extraction['candidates']:
            rid = candidate['requirementId']
            row = groups.setdefault(rid, {"id": rid, "text": candidate['text'], "members": [],
                                          "alignment": "exact-text-and-context", "status": "pending"})
            require(normalize(row['text']) == normalize(candidate['text']), f"identity collision for {rid}")
            row['members'].append(candidate)
    for row in groups.values():
        row['versions'] = sorted({c['version'] for c in row['members']})
        row['suggestedKind'] = guess_kind(row['text'])
    return groups


def apply_alignments(groups, decisions):
    groups = {k: dict(v, members=list(v['members'])) for k,v in groups.items()}
    aliases = {}
    rejected = set()
    for index, decision in enumerate(decisions):
        reviewed(decision, f"alignment {index}")
        source, target = decision.get('source'), decision.get('target')
        require(source != target and source in groups and target in groups, f"alignment {index}: missing/reused endpoint")
        require(decision.get('relation') in {'same', 'different'}, f"alignment {index}: relation must be same or different")
        if decision['relation'] == 'different':
            pair = tuple(sorted((source, target)))
            require(pair not in rejected, f"duplicate alignment decision: {pair}")
            rejected.add(pair)
            continue
        require(tuple(sorted((source, target))) not in rejected, f"contradictory alignment: {source}, {target}")
        groups[target]['members'] += groups[source]['members']
        groups[target]['versions'] = sorted({c['version'] for c in groups[target]['members']})
        groups[target]['alignment'] = 'reviewed-merge'
        aliases[source] = target
        del groups[source]
    def canonical(rid):
        while rid in aliases:
            rid = aliases[rid]
        return rid
    for left, right in rejected:
        require(canonical(left) != canonical(right), f"different alignment collapsed by later merge: {left}, {right}")
    rejected = {tuple(sorted((canonical(a), canonical(b)))) for a,b in rejected}
    return groups, aliases, rejected


STOPWORDS = set('the a an of and or to in is are be must shall should for with by as from this that it on not may can values value field fields'.split())


def tokens(text):
    return set(re.findall(r'[a-z0-9_]+', text.lower())) - STOPWORDS


def similarity(a, b):
    aa, bb = tokens(a), tokens(b)
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa | bb)


def propose_alignments(groups, rejected):
    rows = list(groups.values())
    suggestions = []
    for i, left in enumerate(rows):
        if not left['members']:
            continue
        for right in rows[i+1:]:
            if (not right['members'] or set(left['versions']) == set(right['versions'])
                    or tuple(sorted((left['id'], right['id']))) in rejected):
                continue
            l, r = left['members'][0], right['members'][0]
            if l['headings'] != r['headings'] or l['context'] != r['context']:
                continue
            fields = l.get('reservedField'), r.get('reservedField')
            same_key = all(fields) and (fields[0]['kind'], fields[0]['key']) == (fields[1]['kind'], fields[1]['key'])
            score = difflib.SequenceMatcher(None, normalize(left['text']), normalize(right['text']), autojunk=False).ratio()
            if same_key or (score >= 0.72 and similarity(left['text'], right['text']) >= 0.4):
                suggestions.append({'source': left['id'], 'target': right['id'], 'score': round(score, 4),
                                    'basis': 'same reserved key' if same_key else 'text similarity within section and context',
                                    'confidence': 'high' if score >= 0.92 else 'ambiguous', 'status': 'pending'})
    return sorted(suggestions, key=lambda s: (-s['score'], s['source'], s['target']))


def add_manual(groups, manual, lock, here=HERE):
    for row in manual:
        reviewed(row, 'manual requirement')
        rid = row.get('id', '')
        require(re.fullmatch(r'MAN-[A-Za-z0-9_-]+', rid) and rid not in groups, f"invalid/duplicate manual id {rid}")
        versions = checked_versions(row.get('versions'), rid)
        require(isinstance(row.get('text'), str) and row['text'].strip(), f"{rid}: text required")
        require(row.get('anchors'), f"{rid}: source anchors required")
        require({a['version'] for a in row['anchors']} == set(versions), f"{rid}: every version needs an anchor")
        for anchor in row['anchors']:
            item = lock['versions'][anchor['version']]
            require(anchor['sha256'] == item['sha256'], f"{rid}: stale manual source anchor")
            line_count = len(verified_source(item, here).splitlines())
            require(1 <= anchor['lineStart'] <= anchor['lineEnd'] <= line_count, f"{rid}: invalid source line range")
        groups[rid] = {'id': rid, 'text': row['text'], 'versions': versions, 'members': [],
                       'manual': row, 'alignment': 'manual', 'status': 'pending', 'suggestedKind': guess_kind(row['text'])}


def proposals(row, targets):
    ranked = []
    for target in targets:
        if target['versions'] and not set(row['versions']) & set(target['versions']):
            continue
        score = similarity(row['text'], target['text'])
        if score >= .12:
            ranked.append({'target': target['id'], 'score': round(score, 4), 'basis': 'token overlap, not a verdict'})
    # Deterministic shortlist, with separate representation and enforcement pools.
    by_id = {t['id']: t for t in targets}
    ranked.sort(key=lambda p: (-p['score'], p['target']))
    out = []
    for kinds in ({'inventory', 'term'}, {'shape', 'rule', 'decoded', 'serialization'}):
        out.extend([p for p in ranked if by_id[p['target']]['type'] in kinds][:3])
    for candidate in row['members']:
        if 'reservedField' in candidate:
            field = candidate['reservedField']
            local = f"VCF{candidate['version'].replace('.', '')}{field['kind']}ReservedShape"
            target = f"shape:shacl/vcf-{candidate['version']}.shacl.ttl#{local}"
            if target in by_id and not any(p['target'] == target for p in out):
                out.append({'target': target, 'score': None, 'basis': 'reserved field family and version; check actual Number/Type rule'})
    return out


def trace(groups, reviews, targets):
    require(set(reviews) <= set(groups), 'triage contains unknown or merged-away IDs: ' + ', '.join(sorted(set(reviews)-set(groups))))
    by_target = {t['id']: t for t in targets}
    results, errors = [], []
    roles = {'representation': {'inventory', 'term'}, 'enforcement': {'shape', 'rule', 'decoded'},
             'serialization': {'serialization'}}
    for rid, group in sorted(groups.items()):
        decision = reviews.get(rid)
        row = {'id': rid, 'versions': group['versions'], 'status': 'pending', 'kind': None,
               'mappingComplete': False, 'coveredVersions': [], 'unmappedVersions': [],
               'dischargeStatus': 'pending', 'finding': 'unassessed', 'owner': 'maintainer',
               'evidence': [], 'suggestions': proposals(group, targets)}
        if decision is None:
            results.append(row)
            continue
        reviewed(decision, rid)
        status = decision.get('status')
        require(status in STATUSES, f"{rid}: invalid triage status")
        row.update(status=status, owner=decision.get('owner', decision['reviewer']), decision=decision)
        if status in {'requirement', 'excluded'}:
            kind = decision.get('kind')
            require(kind in KINDS, f"{rid}: choose one requirement kind")
            row['kind'] = kind
        if status == 'excluded':
            require(isinstance(decision.get('scopeReason'), str) and decision['scopeReason'].strip(), f"{rid}: exclusion requires scopeReason")
            row['finding'] = 'out of scope'
        elif status == 'not-a-requirement':
            row['finding'] = 'not a requirement'
        elif status == 'duplicate-of':
            target = decision.get('target')
            require(target in groups and target != rid, f"{rid}: invalid duplicate target")
            require(reviews.get(target, {}).get('status') in {'requirement', 'excluded'}, f"{rid}: duplicate must point to a retained terminal requirement")
            require(set(group['versions']) <= set(groups[target]['versions']), f"{rid}: duplicate would lose version applicability; align instead")
            row['finding'] = 'duplicate'
        elif status == 'split-into':
            children = decision.get('children', [])
            require(len(children) >= 2 and len(children) == len(set(children)), f"{rid}: split needs at least two distinct manual children")
            for child in children:
                require(child in groups and groups[child].get('manual', {}).get('parent') == rid, f"{rid}: missing child or parent link {child}")
                require(reviews.get(child, {}).get('status') in {'requirement', 'excluded'}, f"{rid}: child {child} needs triage")
                require(set(groups[child]['versions']) <= set(group['versions']), f"{rid}: child applicability exceeds parent")
            require(set().union(*(set(groups[c]['versions']) for c in children)) == set(group['versions']), f"{rid}: split loses version applicability")
            row['finding'] = 'split'
        else:
            complete = decision.get('mappingComplete', False)
            require(isinstance(complete, bool), f"{rid}: mappingComplete must be boolean")
            row['mappingComplete'] = complete
            covered = defaultdict(set)
            mismatch = set()
            for evidence in decision.get('evidence', []):
                target_id = evidence.get('target')
                require(target_id in by_target, f"{rid}: dangling evidence target {target_id}")
                target = by_target[target_id]
                require(evidence.get('fingerprint') == target['fingerprint'], f"{rid}: evidence changed; re-review {target_id}")
                require(evidence.get('role') in roles and target['type'] in roles[evidence['role']], f"{rid}: wrong evidence role for {target_id}")
                require(evidence.get('assessment') in {'full', 'partial'}, f"{rid}: evidence assessment must be full or partial")
                require(isinstance(evidence.get('reason'), str) and evidence['reason'].strip(), f"{rid}: evidence reason required")
                versions = checked_versions(evidence.get('versions'), f"{rid} evidence", group['versions'])
                if target['versions']:
                    allowed = set(target['versions'])
                else:
                    require(isinstance(evidence.get('scopeReason'), str) and evidence['scopeReason'].strip(), f"{rid}: unknown target scope requires scopeReason")
                    allowed = set(versions)
                bad = set(versions) - allowed
                mismatch.update(bad)
                if bad:
                    errors.append(f"{rid}: version-mismatched {target_id}: {', '.join(sorted(bad))}")
                if evidence['assessment'] == 'full':
                    covered[evidence['role']].update(set(versions) & allowed)
                row['evidence'].append(evidence)
            needed = {'representational': 'representation', 'validity': 'enforcement', 'serialization': 'serialization'}.get(row['kind'])
            require(row['kind'] not in {'processing', 'bcf'} or not complete,
                    f"{rid}: processing/BCF must be explicitly excluded or left pending, never credited as vocabulary coverage")
            if complete:
                row['coveredVersions'] = sorted(covered[needed]) if needed else []
                row['unmappedVersions'] = sorted(set(row['versions']) - set(row['coveredVersions']))
                row['dischargeStatus'] = ('full' if not row['unmappedVersions'] else
                                          'partial' if row['coveredVersions'] else 'unmapped')
                inventory = any(by_target[e['target']]['type'] == 'inventory' for e in row['evidence'])
                enforced = bool(covered['enforcement'] or covered['serialization'])
                row['finding'] = ('version-mismatched' if mismatch else
                                  'enforced, not inventoried' if enforced and not inventory else
                                  'inventoried, not enforced' if inventory and not enforced else
                                  'inventoried and enforced' if inventory and enforced else 'neither')
            elif mismatch:
                row['finding'] = 'version-mismatched'
        # Lifecycle claims are human decisions; their absence does not imply withdrawal.
        for life in decision.get('lifecycle', []):
            require(life.get('version') in ALL_VERSIONS and life.get('state') in {'deprecated', 'withdrawn'}
                    and isinstance(life.get('reason'), str) and life['reason'].strip(), f"{rid}: invalid lifecycle decision")
        results.append(row)
    for rid, group in groups.items():
        parent = group.get('manual', {}).get('parent')
        if parent:
            require(reviews.get(parent, {}).get('status') == 'split-into' and rid in reviews[parent]['children'], f"{rid}: orphan split child")
    return results, errors


def transitions(groups):
    out = []
    for before, after in zip(ALL_VERSIONS, ALL_VERSIONS[1:]):
        added, absent, reworded = [], [], []
        for rid, row in sorted(groups.items()):
            applies = row['versions']
            if before not in applies and after in applies:
                added.append(rid)
            elif before in applies and after not in applies:
                absent.append(rid)
            elif before in applies and after in applies:
                texts = {v: sorted({m['text'] for m in row['members'] if m['version'] == v}) for v in (before, after)}
                if texts[before] != texts[after]:
                    reworded.append(rid)
        out.append({'from': before, 'to': after, 'newlyObserved': added, 'noLongerObserved': absent, 'reviewedRewordings': reworded})
    return out


def reconcile(extractions, groups, decisions, diffs, transition_notes=None):
    transition_notes = transition_notes or {}
    changes = [c for x in extractions for c in x['changes']]
    require(set(decisions) <= {c['id'] for c in changes}, 'unknown changelog decision id')
    rows = []
    for change in changes:
        heading = change['headings'][-1]
        mentioned = re.findall(r'VCFv(4\.[1-5])', heading)
        transition = sorted(set(mentioned)) if len(set(mentioned)) == 2 else None
        candidates = []
        for rid, row in groups.items():
            score = similarity(change['text'], row['text'])
            if score >= .12:
                candidates.append({'requirement': rid, 'score': round(score, 4)})
        candidates.sort(key=lambda r: (-r['score'], r['requirement']))
        result = {**change, 'transition': transition, 'status': 'pending', 'suggestions': candidates[:5]}
        decision = decisions.get(change['id'])
        if decision:
            reviewed(decision, change['id'])
            require(decision.get('status') in {'linked', 'out-of-scope', 'editorial', 'unresolved'}, f"{change['id']}: invalid reconciliation status")
            links = decision.get('requirements', [])
            require(set(links) <= set(groups), f"{change['id']}: dangling reconciliation link")
            if decision['status'] == 'linked':
                require(links, f"{change['id']}: linked change needs requirements")
                if transition:
                    diff = next(d for d in diffs if [d['from'], d['to']] == transition)
                    changed = set(diff['newlyObserved'] + diff['noLongerObserved'] + diff['reviewedRewordings'])
                    if not set(links) & changed:
                        require(isinstance(decision.get('disagreementReason'), str) and decision['disagreementReason'].strip(),
                                f"{change['id']}: linked requirements absent from transition diff; explain disagreementReason")
            result.update(status=decision['status'], decision=decision)
        rows.append(result)
    unreconciled, explained, known = [], [], set()
    for diff in diffs:
        transition = [diff['from'], diff['to']]
        linked = {r for c in rows if c['transition'] == transition and c['status'] == 'linked'
                  for r in c.get('decision', {}).get('requirements', [])}
        missing = []
        for rid in sorted(set(diff['newlyObserved'] + diff['noLongerObserved'] + diff['reviewedRewordings'])):
            key = f"{diff['from']}->{diff['to']}:{rid}"
            known.add(key)
            if key in transition_notes:
                note = transition_notes[key]
                reviewed(note, key)
                require(note.get('status') in {'specification-omission', 'editorial', 'alignment-artifact', 'extraction-limit', 'out-of-scope'}, f"{key}: invalid transition note status")
                explained.append({'id': key, 'decision': note})
            elif rid not in linked:
                missing.append(rid)
        unreconciled.append({'from': diff['from'], 'to': diff['to'], 'requirements': missing})
    require(set(transition_notes) <= known, 'unknown/stale transition note IDs')
    return {'changes': rows, 'derivedChangesWithoutReviewedChangelogLink': unreconciled,
            'explainedTransitionObservations': explained,
            'note': 'Independent extraction of changelog items; links and disagreements require review. Errata are retained separately.'}


def summary(extractions, groups, traceability, alignments, reconciliation):
    counts = Counter(r['status'] for r in traceability)
    per_version = []
    for extraction in extractions:
        version = extraction['version']
        rows = [r for r in traceability if version in r['versions']]
        per_version.append({'version': version, **extraction['statistics'],
                            'corpusEntries': len(rows), 'reviewedRequirements': sum(r['status'] == 'requirement' for r in rows),
                            'discharged': sum(version in r['coveredVersions'] for r in rows),
                            'pendingTriage': sum(r['status'] == 'pending' for r in rows),
                            'pendingMapping': sum(r['status'] == 'requirement' and not r['mappingComplete'] for r in rows),
                            'excluded': sum(r['status'] == 'excluded' for r in rows)})
    pending_mapping = sum(r['status'] == 'requirement' and not r['mappingComplete'] for r in traceability)
    pending_changes = sum(c['status'] in {'pending', 'unresolved'} for c in reconciliation['changes'])
    missing_change_links = sum(len(t['requirements']) for t in reconciliation['derivedChangesWithoutReviewedChangelogLink'])
    return {'assessmentStatus': 'review-required' if (counts['pending'] or pending_mapping or alignments or pending_changes or missing_change_links) else 'reviewed',
            'candidateOccurrences': sum(len(e['candidates']) for e in extractions), 'corpusEntries': len(groups),
            'manuallyAdded': sum(bool(r.get('manual')) for r in groups.values()),
            'reviewedRequirements': counts['requirement'], 'pendingTriage': counts['pending'], 'pendingMapping': pending_mapping,
            'dischargedAllApplicableVersions': sum(r['status'] == 'requirement' and set(r['coveredVersions']) == set(r['versions']) for r in traceability),
            'dischargedByKind': {kind: sum(r['kind'] == kind and r['status'] == 'requirement' and set(r['coveredVersions']) == set(r['versions']) for r in traceability) for kind in sorted(KINDS)},
            'pendingAlignmentPairs': len(alignments), 'pendingChangelogItems': pending_changes,
            'derivedChangesWithoutReviewedChangelogLink': missing_change_links,
            'findings': dict(sorted(Counter(r['finding'] for r in traceability).items())), 'byVersion': per_version,
            'limitations': LIMITS}


def markdown_report(stats, seeds):
    lines = ['# VCF 4.1–4.5 requirement traceability', '',
             '**Assessment status: ' + stats['assessmentStatus'] + '.** Generated offline; do not edit.', '',
             f"{stats['candidateOccurrences']} candidate occurrences form {stats['corpusEntries']} corpus entries. "
             f"{stats['reviewedRequirements']} are retained requirements (including unfinished mappings); {stats['dischargedAllApplicableVersions']} "
             'have reviewed discharge evidence for every applicable version.', '',
             'An unreviewed entry is **unassessed**, not a demonstrated vocabulary gap. No coverage percentages are calculated.', '',
             '| VCF | Candidates | Obligation / prohibition candidates | Corpus entries | Reviewed requirements | Discharged | Pending triage |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for row in stats['byVersion']:
        strong = row['byStrength'].get('obligation', 0) + row['byStrength'].get('prohibition', 0)
        lines.append(f"| {row['version']} | {row['candidates']} | {strong} | {row['corpusEntries']} | {row['reviewedRequirements']} | {row['discharged']} | {row['pendingTriage']} |")
    lines += ['', 'Obligation density is sensitive to wording: 4.1/4.2 are more descriptive. The column above is a candidate count, not a comparable denominator.', '',
              '## Automatically checked reserved-field facts', '',
              'Literal Number/Type comparisons against the versioned vocabulary artifacts, using independently extracted source rows. '
              'Counts include repeated definitions; this checks metadata agreement, not semantic discharge or enforcement.', '',
              '| VCF | Source rows | Distinct field keys | Exact matches | Missing | Different |',
              '| --- | ---: | ---: | ---: | ---: | ---: |']
    for row in stats['reservedDefinitionComparison']:
        lines.append(f"| {row['version']} | {row['sourceRows']} | {row['sourceKeys']} | {row['exact']} | {row['missing']} | {row['different']} |")
    lines += ['', 'Details: [reserved-definition-comparison.json](reserved-definition-comparison.json).', '',
              '## Decisions awaiting review', '',
              f"- Triage/classification: {stats['pendingTriage']} entries.",
              f"- Mapping: {stats['pendingMapping']} reviewed requirements.",
              f"- Alignment: {stats['pendingAlignmentPairs']} proposed pairs (not accepted automatically).",
              f"- Changelog: {stats['pendingChangelogItems']} items; {stats['derivedChangesWithoutReviewedChangelogLink']} transition observations lack reviewed links.", '',
              'Read the [assessment and method](../README.md) and [review instructions](../DECISIONS.md). '
              'The active judgments are in [decisions.json](../decisions.json). '
              'Run `npm run methodological:audit` for optional worksheets, extraction diagnostics and a readable decision register.', '',
              '## Seed checks from the plans', '',
              'These are extraction acceptance checks and evidence suggestions. They carry no reviewed coverage credit.', '',
              '| Seed | VCF 4.5 candidates found | Evidence targets found |', '| --- | ---: | ---: |']
    lines += [f"| {s['name']} | {len(s['candidates'])} | {len(s['targets'])} |" for s in seeds]
    lines += ['', '## Limits', ''] + ['- ' + limit for limit in LIMITS]
    lines += ['', '## Reproduce', '', '```sh', 'npm run methodological:build', 'npm run methodological:check',
              'npm run methodological:test', '```', '',
              'The exact inputs and their SHA-256 hashes are in [provenance.json](provenance.json). '
              'Source line anchors refer to [the pinned LaTeX copies](../sources/).', '']
    return '\n'.join(lines)


SEEDS = [
    ('CHROM blocks', r'entries for a specific CHROM must form a contiguous block', 'Records for one CHROM must form a contiguous record-index block.'),
    ('Sorted positions (declarative)', r'Positions are sorted numerically', 'Record positions must be nondecreasing within a CHROM block.'),
    ('Record ID uniqueness (advisory wording)', r'No identifier should be present in more than one data record', 'Individual record identifiers must be unique across records.'),
    ('Structured header IDs', r'All structured lines require an ID which must be unique', 'Structured header-line ID attributes must be unique within their header type.'),
    ('Sample names', r'Duplicate sample IDs are not allowed', "Sample names and sample indices must be unique within a VCF file's SampleSet."),
    ('GT first', r'The first key must always be the genotype \(GT\) if it is present', 'GT must be the first FORMAT key when it is present.'),
    ('PS / PSL exclusion', r'A given sample-genotype must not have values for both PS and PSL', 'PS and PSL must not both be populated for the same sample call.'),
]


def seed_checks(extractions, targets):
    candidates = next(e['candidates'] for e in extractions if e['version'] == '4.5')
    seeds = []
    for name, pattern, message in SEEDS:
        matched = [c['id'] for c in candidates if re.search(pattern, c['text'], re.I)]
        evidence = [t['id'] for t in targets if t['type'] == 'rule' and t['text'] == message]
        require(matched, f"extraction acceptance seed not found: {name}")
        require(evidence, f"evidence acceptance seed not found: {name}")
        seeds.append({'name': name, 'candidates': matched, 'targets': evidence, 'status': 'suggested-only'})
    return seeds


def seed_review(seeds, groups, targets):
    by_target = {t['id']: t for t in targets}
    by_occurrence = {m['id']: row for row in groups.values() for m in row['members']}
    prompts = [
        'Assess whether recordIndex and the materialized CHROM sequence faithfully capture the source record order.',
        'The neighbouring source sentence permits equal POS values. Assess the nondecreasing check against that context.',
        'The source uses should. Decide whether to retain this advisory requirement; do not silently promote its strength.',
        'The suggested rule enumerates specific header types. Assess arbitrary extension structured lines and ID presence separately before calling the whole statement discharged.',
        'The source requires unique sample IDs; the rule also checks sample indices. Keep the source requirement distinct from additional model constraints.',
        'Check the rule when GT is present, when it is absent, and against the FORMAT representation actually materialized.',
        'The source observations apply to 4.4 and 4.5; an ungated shared rule is not evidence that the requirement existed earlier.',
    ]
    lines = ['# First assessment batch: seven seed examples', '',
             'Generated review worksheet. These are **suggestions**, not accepted findings. '
             'Write decisions in [decisions.json](../../decisions.json); see [DECISIONS.md](../../DECISIONS.md).', '']
    for seed, prompt in zip(seeds, prompts):
        row = by_occurrence[seed['candidates'][0]]
        member = next(m for m in row['members'] if m['id'] == seed['candidates'][0])
        lines += ['## ' + seed['name'], '', f"**ID:** `{row['id']}`. **Observed versions:** {', '.join(row['versions'])}. "
                  f"**VCF 4.5 discovery strength:** {member['strength']}. **Triage:** {row['status']}.", '',
                  '> ' + member['text'], '',
                  f"Source: [VCF 4.5](../../{member['source']}), lines {member['lineStart']}–{member['lineEnd']}; "
                  + ' / '.join(member['headings']) + '.', '', '**Decision to assess:** ' + prompt, '']
        for tid in seed['targets']:
            target = by_target[tid]
            lines += [f"Suggested rule: [{target['iri'].split('#')[-1]}](../../../../{target['file']}).", '',
                      '> ' + target['text'], '', f"Target: `{tid}`", '',
                      f"Fingerprint: `{target['fingerprint']}`", '',
                      'Recognised scope: ' + ', '.join(target['versions']) + '. ' + target['scopeBasis'] + '.', '']
    return '\n'.join(lines)


def input_hashes(root=ROOT, here=HERE):
    patterns = ['ontology/*.ttl', 'ontology/versions/*', 'shacl/*.ttl',
                'coverage/curated/inventory.json', 'tests/semantic_validation.py', 'coverage/curated/check_serialization.py',
                'scripts/version_registry.py', 'coverage/methodological/*.py', 'coverage/methodological/*.json',
                'coverage/methodological/probes/*.json',
                'coverage/methodological/requirements.txt', 'coverage/methodological/sources/*.tex']
    paths = {p for pattern in patterns for p in root.glob(pattern) if p.is_file() and '.bundle.' not in p.name}
    return {p.relative_to(root).as_posix(): fingerprint(p.read_bytes()) for p in sorted(paths)}


def review_register(groups, rows, decisions):
    """Readable view of recorded judgments; it never assigns a new verdict."""
    lines = ['# Recorded reviewer decisions', '',
             'Generated from [decisions.json](../../decisions.json). Reviewer identities are recorded authors, '
             'not independent approval. A scope decision with pending mapping earns no credit.', '',
             'See [README.md](../../README.md) for the interpretation and limits.', '']
    policies = decisions.get('assessmentPolicy', [])
    if policies:
        lines += ['## Agreed assessment policies', '']
        for policy in policies:
            lines += [f"- **{policy['id']}** — {policy['status']}, {policy['reviewer']}: {policy['reason']} "
                      + policy.get('qualification', '')]
        lines += ['', 'Policy agreement does not constitute approval of every mapping or of corpus completeness.', '']
    for row in rows:
        decision = row.get('decision')
        if decision is None:
            continue
        lines += ['## ' + row['id'], '', groups[row['id']]['text'], '',
                  f"**Reviewer:** {decision['reviewer']}. **Status:** {row['status']}. "
                  f"**Kind:** {row['kind'] or '—'}. **Versions:** {', '.join(row['versions'])}.", '',
                  '**Rationale:** ' + decision['reason'], '']
        if row['status'] == 'requirement':
            lines += [f"**Mapping complete:** {str(row['mappingComplete']).lower()}. "
                      f"**Fully credited versions:** {', '.join(row['coveredVersions']) or 'none'}.", '']
        if decision.get('strengthAssessment'):
            lines += ['**Strength assessment:** ' + decision['strengthAssessment'], '']
        if decision.get('reviewBasis'):
            lines += ['**Assessment basis:** ' + decision['reviewBasis'], '']
        if decision.get('secondReview'):
            second = decision['secondReview']
            lines += [f"**Second review:** {second['reviewer']} — {second['scope']}. {second['reason']}", '']
        if decision.get('children'):
            lines += ['**Split children:** ' + ', '.join('`' + c + '`' for c in decision['children']), '']
        for item in row['evidence']:
            lines += [f"- {item['assessment']} {item['role']} ({', '.join(item['versions'])}): "
                      f"`{item['target']}`. {item['reason']}"]
        if row['evidence']:
            lines.append('')
    lines += ['## Changelog judgments', '',
              'All source occurrences and anchors are retained in [changelog-reconciliation.json](../changelog-reconciliation.json).', '']
    for key, decision in sorted(decisions['changelog'].items()):
        lines += [f"- `{key}` — **{decision['status']}**, {decision['reviewer']}: {decision['reason']} "
                  + decision.get('disagreementReason', '')]
    return '\n'.join(lines) + '\n'


def build(root=ROOT, here=HERE):
    lock = source_lock(root, here)
    decisions = read_json(here / 'decisions.json')
    require(decisions.get('schemaVersion') == 1, 'unsupported decision schema')
    require(set(decisions) <= {'schemaVersion', 'comment', 'alignments', 'manualRequirements', 'triage', 'changelog', 'transitions', 'assessmentPolicy'}, 'unknown decision ledger section')
    policies = decisions.get('assessmentPolicy', [])
    require(isinstance(policies, list), 'assessmentPolicy must be a list')
    policy_ids = set()
    for policy in policies:
        reviewed(policy, 'assessment policy')
        require(policy.get('id') and policy['id'] not in policy_ids, 'assessment policy IDs must be distinct')
        require(policy.get('status') in {'agreed', 'disagreed', 'unresolved'} and policy.get('scope'), 'assessment policy needs status and scope')
        policy_ids.add(policy['id'])
    extractions = [extract(v, verified_source(lock['versions'][v], here), lock['versions'][v]['sha256']) for v in ALL_VERSIONS]
    groups, aliases, rejected = apply_alignments(initial_corpus(extractions), decisions['alignments'])
    add_manual(groups, decisions['manualRequirements'], lock, here)
    alignments = propose_alignments(groups, rejected)
    targets = catalogue(root, ALL_VERSIONS, read_json(root / 'coverage/curated/inventory.json'))
    rows, errors = trace(groups, decisions['triage'], targets)
    # Propagate reviewed state into the readable register, retaining all occurrences.
    for row in rows:
        groups[row['id']]['status'] = row['status']
        groups[row['id']]['kind'] = row['kind']
    diffs = transitions(groups)
    reconciliation = reconcile(extractions, groups, decisions['changelog'], diffs, decisions.get('transitions', {}))
    seeds = seed_checks(extractions, targets)
    stats = summary(extractions, groups, rows, alignments, reconciliation)
    reserved = compare_reserved_definitions(extractions, version_registry.versions(
        version_registry.load(root / 'ontology/versions/registry.json')), root)
    stats['reservedDefinitionComparison'] = [{k:v for k,v in row.items() if k != 'rows'} for row in reserved['versions']]
    provenance = {'schemaVersion': 1, 'methodVersion': 1, 'sources': lock,
                  'inputs': input_hashes(root, here), 'reproduction': 'Python >=3.10; pinned rdflib; UTF-8; no network/timestamps/random IDs',
                  'limitations': LIMITS}
    queue = {'triage': [{'id': r['id'], 'text': groups[r['id']]['text'], 'versions': r['versions'],
                         'suggestedKind': groups[r['id']]['suggestedKind'], 'evidenceSuggestions': r['suggestions']}
                        for r in rows if r['status'] == 'pending' or (r['status'] == 'requirement' and not r['mappingComplete'])],
             'alignment': alignments, 'changelog': [c for c in reconciliation['changes'] if c['status'] in {'pending', 'unresolved'}],
             'owner': 'maintainer', 'note': 'Suggestions are unreviewed. Decisions belong in ../decisions.json, never this generated file.'}
    artifacts = {'extracted.json': {'schemaVersion': 1, 'versions': extractions},
                 'corpus.json': {'schemaVersion': 1, 'aliases': aliases, 'requirements': [groups[k] for k in sorted(groups)]},
                 'alignment-suggestions.json': alignments, 'evidence-catalogue.json': targets,
                 'version-diff.json': diffs, 'changelog-reconciliation.json': reconciliation,
                 'traceability.json': {'schemaVersion': 1, 'summary': stats, 'requirements': rows, 'errors': errors},
                 'review-queue.json': queue, 'seed-checks.json': seeds, 'summary.json': stats,
                 'provenance.json': provenance}
    artifacts['reserved-definition-comparison.json'] = reserved
    rendered = {name: encoded(data) for name, data in artifacts.items()}
    rendered['report.md'] = markdown_report(stats, seeds).encode('utf-8')
    rendered['seed-review.md'] = seed_review(seeds, groups, targets).encode('utf-8')
    rendered['reviewed-decisions.md'] = review_register(groups, rows, decisions).encode('utf-8')
    return rendered, stats, errors


def selected_outputs(artifacts, audit=False):
    """Publish the necessary results; detailed reviewer workspaces are opt-in."""
    return {(name if name in PRIMARY_OUTPUTS else 'audit/' + name): raw
            for name, raw in artifacts.items() if name in PRIMARY_OUTPUTS or audit}


def check_outputs(artifacts, here=HERE):
    stale = []
    for name, raw in artifacts.items():
        path = here / 'generated' / name
        if not path.exists() or path.read_bytes() != raw:
            stale.append(name)
    return stale


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['fetch', 'build', 'check', 'review-template'])
    parser.add_argument('--require-reviewed', action='store_true', help='exit 2 while triage/alignment/reconciliation remains incomplete')
    parser.add_argument('--id', help='corpus ID for review-template')
    parser.add_argument('--audit', action='store_true', help='also generate/check optional diagnostics in generated/audit/')
    args = parser.parse_args(argv)
    try:
        if args.command == 'fetch':
            fetch_sources()
            return 0
        artifacts, stats, errors = build()
        if args.command == 'review-template':
            corpus = json.loads(artifacts['corpus.json'])['requirements']
            row = next((r for r in corpus if r['id'] == args.id), None)
            require(row is not None, 'pass --id with an ID from generated/corpus.json')
            print(json.dumps({row['id']: {'status': 'requirement', 'kind': row['suggestedKind'], 'reviewer': '',
                                         'reason': '', 'mappingComplete': False, 'evidence': []}}, indent=2))
            return 0
        if args.command == 'check':
            stale = check_outputs(selected_outputs(artifacts, args.audit))
            if stale:
                print('STALE: ' + ', '.join(stale) + '; run npm run methodological:build', file=sys.stderr)
                return 1
        else:
            (HERE / 'generated').mkdir(exist_ok=True)
            for name, raw in selected_outputs(artifacts, args.audit).items():
                destination = HERE / 'generated' / name
                destination.parent.mkdir(exist_ok=True, parents=True)
                destination.write_bytes(raw)
            # Remove only known legacy locations for outputs now generated on demand.
            for name in set(artifacts) - PRIMARY_OUTPUTS:
                (HERE / 'generated' / name).unlink(missing_ok=True)
        print(f"VCF methodological assessment: {stats['candidateOccurrences']} occurrences; {stats['corpusEntries']} corpus entries; "
              f"{stats['reviewedRequirements']} reviewed; {stats['dischargedAllApplicableVersions']} discharged; "
              f"{stats['pendingTriage']} pending triage ({stats['assessmentStatus']}).")
        if errors:
            print('\n'.join(errors), file=sys.stderr)
            return 1
        if args.require_reviewed and stats['assessmentStatus'] != 'reviewed':
            return 2
        return 0
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
