#!/usr/bin/env python3
"""Assert that every statistic quoted in the SWAT4HCLS 2027 manuscript still
matches ``coverage/curated/generated/report.json``.

The manuscript quotes concrete counts. This check fails if the artifacts move
and the prose does not, so a published figure cannot go stale unnoticed.
Run ``npm run coverage:report`` first; ``npm run validate`` does both.
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT = ROOT / "coverage/curated/generated/report.json"
PAPER = ROOT / "SWAT4HCLS_2027" / "main.tex"


def main() -> int:
    if not REPORT.exists():
        print("coverage-report.json missing; run: npm run coverage:report", file=sys.stderr)
        return 1
    report = json.loads(REPORT.read_text())
    tex = PAPER.read_text()

    cov = report["coverage"]["logicalModel"]
    ser = report["coverage"]["serialization"]
    voc = report["vocabulary"]["byKind"]
    ext = report["externalVocabularies"]
    keys = report["reservedKeys"]
    shapes = report["shaclProfiles"]
    portable = shapes["vcf-core-vocabulary.shacl.ttl"]

    expected: list[tuple[str, str]] = [
        ("construct total", str(cov["constructs"])),
        ("constructs fully covered", str(cov["full"])),
        # The manuscript may state the ratio or "all N entries"; accept either.
        ("full coverage claim", [f"{cov['fullPercent']}\\%", f"all {cov['full']} logical-model entries"]),
        ("declared terms", str(report["vocabulary"]["declaredTerms"])),
        ("classes", f"{voc['class']} classes"),
        ("object properties", f"{voc['objectProperty']} object properties"),
        ("datatype properties", f"{voc['datatypeProperty']} datatype properties"),
        ("named individuals", f"{voc['namedIndividual']} named individuals"),
        ("reserved declarations", f"{keys['current']['total']} reserved key declarations"),
        ("reserved split", f"{keys['current']['info']} INFO and {keys['current']['format']} FORMAT"),
        ("portable node shapes", f"{portable['nodeShapes']} node shapes"),
        ("portable property shapes", f"{portable['propertyShapes']} property shapes"),
        ("sparql rules", f"{shapes['vcf-core-vocabulary-sparql.shacl.ttl']['sparqlConstraints']} cross-resource"),
        ("consistency rules", f"{shapes['vcf-core-consistency.shacl.ttl']['sparqlConstraints']} rules relating raw tokens"),
        ("validated fixtures", f"accepts {report['validation']['fixtures']} fixtures"),
        ("serialization fixtures", f"{ser['fixturesPassed']} of {ser['fixturesChecked']} satisfy"),
        ("enforced constructs", f"{cov['axesHeld']['enforced']} of {cov['constructs']} are enforced"),
    ]
    for prefix, count in (("SO", "so"), ("ChEBI", "chebi"), ("VRS", "vrs"),
                          ("HERO-Genomics", "hero"), ("FALDO", "faldo"), ("GENO", "geno")):
        expected.append((f"{prefix} alignment count",
                         f"{prefix}~({ext['alignmentTargets']['byVocabulary'][count]})"))

    for area in cov["byArea"]:
        expected.append((f"table row: {area['area']}",
                         f"{area['constructs']} & {area['full']} & "))

    def present(value):
        options = value if isinstance(value, list) else [value]
        return any(option in tex for option in options)

    missing = [(label, text) for label, text in expected if not present(text)]
    if missing:
        print("Manuscript figures no longer match the generated report:", file=sys.stderr)
        for label, text in missing:
            print(f"  {label}: expected to find {text!r} in main.tex", file=sys.stderr)
        return 1
    print(f"Manuscript figures: {len(expected)} checked, all match coverage/curated/generated/report.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
