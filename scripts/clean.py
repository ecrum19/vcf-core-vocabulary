#!/usr/bin/env python3
"""Remove disposable repository output; preserve inputs and primary reports.

Disposable means regenerable from committed inputs: the generated documentation
site, Python bytecode caches and desktop metadata. Authored inputs, the coverage
assessments' generated reports and installed dependencies are always kept.
"""
from pathlib import Path
import os
import shutil

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git', '.venv', 'node_modules'}

# Regenerable output removed wholesale. Everything else is discovered by walking.
DISPOSABLE_DIRS = ('site',)


def clean(root=ROOT):
    candidates = {root / name for name in DISPOSABLE_DIRS}
    for directory, dirs, files in os.walk(root, followlinks=False):
        base = Path(directory)
        dirs[:] = [d for d in dirs if d not in SKIP and base / d not in candidates]
        if '__pycache__' in dirs:
            candidates.add(base / '__pycache__')
            dirs.remove('__pycache__')
        if '.DS_Store' in files:
            candidates.add(base / '.DS_Store')
    removed = []
    for path in sorted(candidates):
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        else:
            continue
        removed.append(path.relative_to(root).as_posix())
    return removed


if __name__ == '__main__':
    for name in clean():
        print('Removed ' + name)
