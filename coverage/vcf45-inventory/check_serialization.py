#!/usr/bin/env python3
"""Check the source-byte requirements VCF 4.5 places on a file's serialization.

These are requirements on bytes, not on the logical model, so the vocabulary
deliberately mints no term for them: adding an RDF property would record a
claim about the source without demonstrating that the source was ever read.
This checker reads the actual bytes of every fixture instead, and the coverage
report presents its result as a separate axis alongside logical-model coverage.

VCF 4.5 sections 1-1.2 require:
  * UTF-8 encoding
  * no byte order mark
  * lines separated by LF or CR+LF, used only as line separators

Writes coverage/vcf45-inventory/generated/serialization.json. Exit status is non-zero if any fixture
violates a requirement.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BOM = b"\xef\xbb\xbf"


def inspect(path: pathlib.Path) -> dict:
    raw = path.read_bytes()
    result: dict[str, object] = {"file": path.relative_to(ROOT).as_posix(), "bytes": len(raw)}
    problems: list[str] = []

    result["byteOrderMark"] = raw.startswith(BOM)
    if result["byteOrderMark"]:
        problems.append("starts with a byte order mark, which VCF 4.5 forbids")

    try:
        text = raw.decode("utf-8")
        result["encoding"] = "UTF-8"
    except UnicodeDecodeError as exc:
        result["encoding"] = "not UTF-8"
        problems.append(f"is not valid UTF-8 ({exc.reason} at byte {exc.start})")
        text = ""

    crlf = raw.count(b"\r\n")
    bare_lf = raw.count(b"\n") - crlf
    stray_cr = raw.count(b"\r") - crlf
    result["crlfLines"] = crlf
    result["lfLines"] = bare_lf
    if crlf and bare_lf:
        result["lineTerminator"] = "mixed"
        problems.append(f"mixes CR+LF ({crlf}) and bare LF ({bare_lf}) terminators")
    elif crlf:
        result["lineTerminator"] = "CRLF"
    elif bare_lf:
        result["lineTerminator"] = "LF"
    else:
        result["lineTerminator"] = "none"
        problems.append("contains no line terminator")
    if stray_cr:
        problems.append(f"contains {stray_cr} CR byte(s) outside a CR+LF terminator")

    if text and not text.endswith("\n"):
        problems.append("last data line is not terminated, which VCF 4.5 requires")

    # Non-printable characters the specification disallows.
    disallowed = {c for c in text if ord(c) in set(range(0x00, 0x09)) | {0x0B, 0x0C} | set(range(0x0E, 0x20))}
    if disallowed:
        problems.append("contains disallowed non-printable characters "
                        + ", ".join(f"U+{ord(c):04X}" for c in sorted(disallowed)))

    result["problems"] = problems
    result["passed"] = not problems
    return result


def main() -> int:
    fixtures = sorted(ROOT.glob("examples/**/*.vcf"))
    if not fixtures:
        print("No VCF fixtures found.", file=sys.stderr)
        return 1
    results = [inspect(path) for path in fixtures]
    terminators = sorted({r["lineTerminator"] for r in results})
    report = {
        "$comment": "Source-byte serialization checks (VCF 4.5 sections 1-1.2). Reported as an axis "
                    "separate from logical-model coverage; the vocabulary mints no term for these "
                    "properties by design. Regenerate with: npm run validate:serialization",
        "requirements": ["UTF-8 encoding", "no byte order mark",
                         "LF or CR+LF line separators", "terminated final line",
                         "no disallowed non-printable characters"],
        "fixtures": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "terminatorsExercised": terminators,
        "results": results,
    }
    (HERE / "generated").mkdir(exist_ok=True)
    (HERE / "generated/serialization.json").write_text(json.dumps(report, indent=1) + "\n")

    failures = [r for r in results if not r["passed"]]
    for r in failures:
        for problem in r["problems"]:
            print(f"  {r['file']}: {problem}", file=sys.stderr)
    print(f"Source serialization: {report['passed']}/{report['fixtures']} fixtures satisfy the "
          f"VCF 4.5 byte requirements; terminators exercised: {', '.join(terminators)}.")
    if len(terminators) < 2:
        print("  note: only one line terminator is exercised; add a CR+LF fixture to cover both.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
