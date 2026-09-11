"""Read pinned VCF sources; expose every section and explicit reserved declaration.

This bounded LaTeX reader does not infer requirements from keywords. The authored
register supplies those judgments. Section intervals partition the entire file,
so tables, examples, changelogs, and unlinked passages remain available for audit.
"""
import hashlib
import re


def sha(data):
    return hashlib.sha256(data).hexdigest()


def plain(text):
    """Normalize table typography only; retain field names and Number/Type values."""
    text = re.sub(r"\\(?:texttt|textbf|emph)\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\([_%&#])", r"\1", text)
    return " ".join(text.replace("$", "").replace("{", "").replace("}", "").split())


def sections(text):
    lines = text.splitlines()
    starts = [(1, "Preamble", "preamble")]
    zone = "vcf"
    for n, line in enumerate(lines, 1):
        # A trailing cross-reference label is markup, not part of the heading.
        m = re.match(r"\s*\\(section|subsection|subsubsection)\*?\{(.+)\}",
                     re.sub(r"\s*\\label\{[^{}]*\}\s*$", "", line))
        if not m:
            continue
        title = plain(m[2])
        if m[1] == "section":
            zone = "bcf" if "BCF" in title else "changes" if "changes" in title.lower() else "vcf"
        starts.append((n, title, zone))
    assert any(s[2] == "bcf" for s in starts), "Missing BCF scope boundary"
    return [{"start": n, "end": starts[i+1][0]-1 if i+1 < len(starts) else len(lines),
             "title": title, "zone": z} for i, (n, title, z) in enumerate(starts)]


def declarations(text):
    """Extract only explicit Number/Type rows, independently of registry generators.

    A declaration inside an illustrative VCF is not a reserved definition. Only
    labeled reserved tables and the two structural-variant key sections count.
    Prose-only definitions and parameter-family expansion require separate review.
    """
    lines = text.splitlines()
    found = []
    for sec in sections(text):
        if sec["zone"] != "vcf":
            continue
        chunk = "\n".join(lines[sec["start"]-1:sec["end"]])
        for table in re.finditer(r"\\begin\{longtable\}.*?\\end\{longtable\}", chunk, re.S):
            kind = "INFO" if r"\label{table:reserved-info}" in table[0] else "FORMAT" if r"\label{table:reserved-genotypes}" in table[0] else None
            if not kind:
                continue
            first = sec["start"] + chunk[:table.start()].count("\n")
            for offset, line in enumerate(table[0].splitlines()):
                cells = [plain(x) for x in re.sub(r"\\\\\s*$", "", line).split("&")]
                if len(cells) == 4 and cells[2] in {"Integer", "Float", "String", "Character", "Flag"}:
                    found.append(dict(kind=kind, key=cells[0], number=cells[1], type=cells[2], line=first+offset))
        if sec["title"] in {"INFO keys used for structural variants", "FORMAT keys used for structural variants"}:
            pattern = r'##(INFO|FORMAT)=<ID=([^,>]+),Number=([^,>]+),Type=([^,>]+),Description="'
            for m in re.finditer(pattern, chunk):
                found.append(dict(zip(("kind", "key", "number", "type"), map(plain, m.groups())),
                                  line=sec["start"]+chunk[:m.start()].count("\n")))
    return sorted(found, key=lambda x: x["line"])
