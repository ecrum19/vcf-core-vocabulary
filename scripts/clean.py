#!/usr/bin/env python3
"""Remove disposable repository output; preserve inputs and primary reports."""
from pathlib import Path
import os
import shutil

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git', '.venv', 'node_modules'}


def clean(root=ROOT):
    candidates = {root / name for name in (
        'site', 'SWAT4HCLS_2027/.build', 'coverage/methodological/generated/audit',
    )}
    paper = root / 'SWAT4HCLS_2027'
    candidates.update(paper / ('main.' + suffix) for suffix in (
        'abs', 'aux', 'bbl', 'blg', 'fdb_latexmk', 'fls', 'log', 'out',
        'synctex.gz', 'xmpdata', 'toc',
    ))
    candidates.add(paper / 'pdfa.xmpi')
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
