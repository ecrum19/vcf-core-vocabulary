"""Conservative, line-addressable candidate extraction, independent of the inventory.

This is a bounded LaTeX reader, not a general TeX interpreter. Every prose block
is retained in the audit output, including blocks selected by neither sweep.
"""
from __future__ import annotations

import hashlib
import re
from collections import Counter


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


def clean_tex(text: str) -> str:
    # Protect inline literal syntax (including %, braces and sentence-like dots).
    literals = []

    def literal(match):
        literals.append(match[2])
        return f"ZZLITERAL{len(literals)-1}ZZ"

    text = re.sub(r"\\verb\*?([^A-Za-z\s])(.*?)\1", literal, text)
    text = re.sub(r"(?<!\\)%[^\n]*", "", text)
    text = re.sub(r"\\(?:label|index)\{[^}]*\}", "", text)
    text = re.sub(r"\\(?:ref|pageref)\{([^}]*)\}", r"[ref:\1]", text)
    text = re.sub(r"\\(?:begin|end)\{[^}]*\}(?:\[[^]]*\])?", " ", text)
    text = re.sub(r"\\(?:item)(?:\[([^]]*)\])?", r" \1 ", text)
    for _ in range(4):
        text = re.sub(r"\\(?:texttt|textbf|textsc|textit|textrm|emph|mbox|underline|footnote)\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\([_%&#${}])", r"\1", text)
    text = text.replace(r"\backslash", "\\").replace(r"\ldots", "…")
    text = re.sub(r"\\(?:tt|bf|it|small|footnotesize|scriptsize|normalsize)\b", "", text)
    text = re.sub(r"\\[,;! ]", " ", text)
    text = text.replace("~", " ").replace("$", "").replace("{", "").replace("}", "")
    text = text.replace("``", '"').replace("''", '"')
    for i, value in enumerate(literals):
        text = text.replace(f"ZZLITERAL{i}ZZ", value)
    return " ".join(text.split())


def normalize(text: str) -> str:
    # Only typography/whitespace, never numbers, identifiers, negation or versions.
    return " ".join(text.replace("—", "---").replace("–", "--").split())


MODAL = re.compile(r"\b(?:must(?: not)?|shall(?: not)?|required|may not|cannot|not allowed|not permitted|disallowed|should(?: not)?|recommended|reserved)\b", re.I)
PROHIBITION = re.compile(r"\b(?:must not|shall not|may not|cannot|not allowed|not permitted|disallowed)\b", re.I)
OBLIGATION = re.compile(r"\b(?:must|shall|required)\b", re.I)
DECLARATIVE = re.compile(
    r"\b(?:are sorted|are not|is indicated by|are indicated by|is reserved|"
    r"follow the same rules as|no (?:whitespace|duplicate)|"
    r"(?:character )?encoding .*? is|data types supported|possible types|"
    r"there are \d+ fixed fields|are tab.delimited|missing values are specified|"
    r"(?:field|fields|line|lines) (?:has|have|contains?|consists?|starts?)|"
    r"the order of|is a colon.separated|is mandatory|is optional)\b|"
    r"\((?:String|Integer|Float|Character)[,;)]", re.I)
HEADING = re.compile(r"\\(section|subsection|subsubsection)\*?\{([^}]+)\}")
DECLARATION = re.compile(r'##(INFO|FORMAT)=<ID=([^,>]+),Number=([^,>]+),Type=([^,>]+),Description="([^"]*)"')


def split_sentences(text: str) -> list[str]:
    # Keep decimal points, e.g./i.e., single-character quoted tokens and regexes.
    protected = re.sub(r"\b(?:e\.g|i\.e|cf)\.", lambda m: m[0].replace(".", "ZZDOTZZ"), text)
    chunks = re.split(r'(?<=[.!?])\s+(?=[A-Z(])', protected)
    return [s.replace("ZZDOTZZ", ".").strip() for s in chunks if s.strip()]


def discover(text: str) -> tuple[list[str], list[str], str]:
    matches = sorted({m[0].lower() for m in MODAL.finditer(text)})
    methods = (["modal"] if matches else []) + (["declarative"] if DECLARATIVE.search(text) else [])
    strength = ("prohibition" if PROHIBITION.search(text) else
                "obligation" if OBLIGATION.search(text) else
                "advisory" if matches else "declarative")
    return methods, matches, strength


def extract(version: str, source: str, sha256: str) -> dict:
    lines = source.splitlines()
    headings, numbers = [], [0, 0, 0]
    context = ""
    block = []
    blocks, candidates, changes, skips = [], [], [], []
    zone = "preamble"
    environment = None
    bcf_start = change_start = None
    longtable_kind = None
    occurrence_counts = Counter()

    def anchor(start, end):
        return {"version": version, "source": f"sources/VCFv{version}.tex", "sha256": sha256,
                "lineStart": start, "lineEnd": end, "section": ".".join(str(n) for n in numbers if n),
                "headings": list(headings), "context": context}

    def emit(text, start, end, methods=None, fields=None):
        methods0, matches, strength = discover(text)
        methods = methods if methods is not None else methods0
        identity = normalize(" / ".join(headings) + " | " + context + " | " + text)
        rid = "REQ-" + digest(identity)
        occurrence_counts[rid] += 1
        item = {"id": f"{version}:{rid}:{occurrence_counts[rid]}", "requirementId": rid,
                "text": text, "discovery": methods, "matchedModals": matches,
                "strength": "declarative" if fields else strength, **anchor(start, end)}
        if fields:
            item["reservedField"] = fields
        candidates.append(item)
        return item["id"]

    def flush():
        if not block:
            return
        raw = "\n".join(line for _, line in block)
        text = clean_tex(raw)
        start, end = block[0][0], block[-1][0]
        block.clear()
        if not text:
            return
        if zone == "changes":
            if context == "change-item":
                changes.append({"id": "CHANGE-" + digest(version + " / ".join(headings) + text),
                                "text": text, **anchor(start, end)})
            return
        if zone != "vcf":
            return
        ids = []
        for sentence in split_sentences(text):
            if discover(sentence)[0]:
                ids.append(emit(sentence, start, end))
        blocks.append({"id": "BLOCK-" + digest(version + str(start) + raw),
                       "text": text, "rawTex": raw, "candidateIds": ids, **anchor(start, end)})

    for index, line in enumerate(lines, 1):
        # Comments cannot introduce headings, examples or requirements.
        if line.lstrip().startswith("%"):
            skips.append({"lineStart": index, "lineEnd": index, "reason": "comment"})
            continue
        match = HEADING.search(line) if environment not in {"verbatim", "lstlisting"} else None
        if match:
            flush()
            level = {"section": 0, "subsection": 1, "subsubsection": 2}[match[1]]
            numbers[level] += 1
            numbers[level+1:] = [0] * (2-level)
            headings[level:] = [clean_tex(match[2])]
            context = ""
            if level == 0:
                if "BCF" in match[2]:
                    zone, bcf_start = "bcf", index
                elif "changes" in match[2].lower():
                    zone, change_start = "changes", index
                else:
                    zone = "vcf"
            continue
        if zone in {"bcf", "preamble"}:
            continue
        start_env = re.search(r"\\begin\{(verbatim|lstlisting|longtable|tabular)\}", line)
        if start_env:
            flush()
            environment = start_env[1]
            longtable_kind = None
            if environment == "longtable":
                # Labels appear after the repeated headers, before the data rows.
                ahead = "\n".join(lines[index-1:])
                ahead = ahead.split(r"\end{longtable}", 1)[0]
                if re.search(r"\\label\{table:reserved-info\}", ahead):
                    longtable_kind = "INFO"
                elif re.search(r"\\label\{table:reserved-genotypes\}", ahead):
                    longtable_kind = "FORMAT"
        if environment:
            declaration = DECLARATION.search(line)
            fields = None
            if declaration and headings[0] in {"INFO keys used for structural variants", "FORMAT keys used for structural variants"}:
                kind, key, number, typ, description = (clean_tex(s) for s in declaration.groups())
                fields = {"kind": kind, "key": key, "number": number, "type": typ, "description": description}
            elif longtable_kind and "&" in line and re.search(r"\\\\\s*$", line):
                cells = [clean_tex(s) for s in re.sub(r"\\\\\s*$", "", line).split("&")]
                if len(cells) == 4 and cells[2] in {"Integer", "Float", "String", "Character", "Flag"}:
                    key, number, typ, description = cells
                    fields = {"kind": longtable_kind, "key": key, "number": number, "type": typ, "description": description}
            if fields:
                emit(f"{fields['kind']} {fields['key']}: Number={fields['number']}; Type={fields['type']}. {fields['description']}",
                     index, index, ["reserved-table" if longtable_kind else "reserved-declaration"], fields)
            skips.append({"lineStart": index, "lineEnd": index,
                          "reason": f"{environment}: structured row extracted" if fields else f"{environment}: not prose"})
            if re.search(r"\\end\{" + environment + r"\}", line):
                environment = None
                longtable_kind = None
            continue
        if r"\item" in line:
            flush()
            item_text = clean_tex(line)
            if zone == "changes":
                context = "change-item"
            else:
                # Retain a field/list label without using its whole version-specific prose.
                label = re.match(r"([A-Za-z0-9_.<>+-]+)\s*(?::|---|--)", item_text)
                context = label[1] if label else ""
        if re.search(r"\\end\{(?:enumerate|itemize|description)\}", line):
            flush()
            context = ""
        elif not line.strip():
            # Changelog items can span paragraphs; keep them together.
            if zone != "changes":
                flush()
        elif not re.fullmatch(r"\s*\\(?:label\{[^}]*\}|(?:begin|end)\{[^}]*\}|[a-z]+)\s*", line):
            block.append((index, line))
    flush()
    if bcf_start is None:
        raise ValueError(f"VCF {version}: missing BCF boundary; refusing to change scope silently")
    return {"version": version, "sourceSha256": sha256,
            "statistics": {"sourceLines": len(lines), "vcfBoundaryLine": bcf_start,
                           "changeBoundaryLine": change_start, "proseBlocks": len(blocks),
                           "unselectedBlocks": sum(not b['candidateIds'] for b in blocks),
                           "candidates": len(candidates),
                           "byDiscovery": dict(sorted(Counter(d for c in candidates for d in c['discovery']).items())),
                           "byStrength": dict(sorted(Counter(c['strength'] for c in candidates).items()))},
            "excludedRegions": [{"lineStart": 1, "lineEnd": next(i for i,l in enumerate(lines,1) if HEADING.search(l))-1,
                                 "reason": "preamble"},
                                {"lineStart": bcf_start, "lineEnd": (change_start or len(lines)+1)-1,
                                 "reason": "BCF section; standing workflow scope"}],
            "candidates": candidates, "proseAudit": blocks, "skippedLines": skips, "changes": changes}
