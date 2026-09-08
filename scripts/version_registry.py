#!/usr/bin/env python3
"""Shared loader for ontology/versions/registry.json.

The registry is the single source of truth for which VCF specification versions
this vocabulary covers and how each one differs. Every version-scoped artifact is
derived from it, so adding a version is an edit to the table rather than to the
generators. See scripts/README.md.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / 'ontology/versions/registry.json'
MODES = {'snapshot', 'registry'}
SCOPES = {'fixed', 'perAlt'}


class RegistryError(ValueError):
    """The registry table is internally inconsistent."""


def load(path=REGISTRY_PATH):
    """Return the validated registry payload."""
    data = json.loads(Path(path).read_text())
    versions = data.get('versions')
    if not versions:
        raise RegistryError('registry.json declares no versions')
    seen = set()
    for entry in versions:
        for field in ('id', 'code', 'className', 'source', 'reservedKeys', 'numberCodes',
                      'leadingPhaseIndicator', 'perAlleleCopyNumber', 'svTupleScope', 'svTuples'):
            if field not in entry:
                raise RegistryError(f'version {entry.get("id", "?")} is missing "{field}"')
        if entry['id'] in seen:
            raise RegistryError(f'duplicate version id {entry["id"]}')
        seen.add(entry['id'])
        if entry['code'] != f'VCFv{entry["id"]}':
            raise RegistryError(f'version {entry["id"]} code must be VCFv{entry["id"]}')
        if entry['className'] != class_name(entry['id']):
            raise RegistryError(f'version {entry["id"]} className must be {class_name(entry["id"])}')
        if entry['reservedKeys'].get('mode') not in MODES:
            raise RegistryError(f'version {entry["id"]} reservedKeys.mode must be one of {sorted(MODES)}')
        if entry['svTupleScope'] not in SCOPES:
            raise RegistryError(f'version {entry["id"]} svTupleScope must be one of {sorted(SCOPES)}')
        for kind in ('info', 'format'):
            if not entry['numberCodes'].get(kind):
                raise RegistryError(f'version {entry["id"]} declares no {kind} Number codes')
    if data.get('current') not in seen:
        raise RegistryError(f'current version {data.get("current")!r} is not in the table')
    if [v['id'] for v in versions] != sorted(seen, key=sort_key):
        raise RegistryError('versions must be listed in ascending specification order')
    return data


def sort_key(version_id):
    return tuple(int(part) for part in version_id.split('.'))


def class_name(version_id):
    """VCF4xFile class local name for a version id, e.g. 4.1 -> VCF41File."""
    return 'VCF' + version_id.replace('.', '') + 'File'


def slug(version_id):
    """Shape-name infix for a version id, e.g. 4.1 -> 41."""
    return version_id.replace('.', '')


def versions(data=None):
    return (data or load())['versions']


def current(data=None):
    data = data or load()
    return next(v for v in data['versions'] if v['id'] == data['current'])


def by_mode(mode, data=None):
    return [v for v in versions(data) if v['reservedKeys']['mode'] == mode]


def number_pattern(entry, kind):
    """The alternation body for a version's permitted Number codes."""
    return '|'.join(entry['numberCodes'][kind])


def sv_tuple_expected(entry, width):
    """The expected item count for an SV tuple of the given per-ALT width."""
    return str(width) if entry['svTupleScope'] == 'fixed' else f'{width} * ?altCount'


def first_with(capability, data=None):
    """The earliest version in the table that has a boolean capability, or None."""
    return next((entry for entry in versions(data) if entry.get(capability)), None)


def sv_tuple_widths(entry):
    """Map each SV tuple key this version defines to its per-ALT item width."""
    return {key: spec['width'] for spec in entry['svTuples'] for key in spec['keys']}


def by_code(data=None):
    """Index the table by fileformat code, e.g. 'VCFv4.5'."""
    return {entry['code']: entry for entry in versions(data)}
