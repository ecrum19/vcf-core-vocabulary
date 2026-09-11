"""Persist section dispositions separately from generated source structure.

Dispositions classify source material, never vocabulary support. Free-text labels
are retained for migration, but cannot close the source audit until categorized.
"""
import json

from source import sections, sha

DISPOSITIONS = {
    "pending", "mapped", "needs-requirement", "duplicate", "context-only",
    "out-of-scope", "needs-clarification", "needs-review",
}
RESOLVED = {"mapped", "duplicate", "context-only", "out-of-scope"}
ANNOTATIONS = ("disposition", "note", "relatedRequirements")
LEGACY_DEFAULTS = {
    "pending source review": ("pending", ""),
    "excluded: binary layout": ("out-of-scope", "Binary layout is outside this assessment."),
    "excluded: document setup": ("out-of-scope", "Document setup is outside this assessment."),
}


def digest(value):
    return sha(json.dumps(value, sort_keys=True, ensure_ascii=False).encode())


def annotation(row):
    return {"disposition": row["disposition"], "note": row.get("note", ""),
            "relatedRequirements": row.get("relatedRequirements", [])}


def unsaved(rows):
    """A saved hash detects worksheet edits without confusing changed inputs with edits."""
    return [r for r in rows if
            (digest(annotation(r)) != r["savedAnnotationFingerprint"]
             if "savedAnnotationFingerprint" in r
             else r["disposition"] not in LEGACY_DEFAULTS or r.get("note") or r.get("relatedRequirements"))]


def make_audit(source_text, requirements, decisions, coverage=None, cases=(), previous=None):
    """Join authored source assertions to actual case IDs without inferring coverage.

    Anchor overlap remains available as a diagnostic. When an assertion inventory
    is supplied, only its explicit semantic links populate ``requirements``.
    A case's existence is not a passing result or proof of source completeness.
    Optional arguments keep the small source-review fixtures independent of the
    full assessment. Production supplies an inventory for every source section.
    """
    rows = []
    indexed_cases = {c["id"]: c for c in cases}
    for version, text in source_text.items():
        for section in sections(text):
            section_id = f"{version}:{section['start']}-{section['end']}"
            excerpt = "\n".join(text.splitlines()[section["start"]-1:section["end"]])
            source_fingerprint = digest({"version": version, "section": section, "text": excerpt})
            linked = [r["id"] for r in requirements if version in r["versions"] and
                      r["anchors"][version]["start"] <= section["end"] and
                      r["anchors"][version]["end"] >= section["start"]]
            excluded = section["zone"] in {"bcf", "preamble"}
            default = {"disposition": "out-of-scope" if excluded else "pending",
                       "note": "Binary layout is outside this assessment." if section["zone"] == "bcf" else
                               "Document setup is outside this assessment." if excluded else "",
                       "relatedRequirements": []}
            authored = coverage[section_id] if coverage is not None else None
            if authored is not None:
                assert authored["sourceFingerprint"] == source_fingerprint, f"Stale assertion inventory: {section_id}"
                default.update(disposition=authored["disposition"], note=authored["note"])
            anchors = linked
            if authored is not None:
                linked = sorted({rid for a in authored["assertions"] for rid in a["requirements"]})
            decision = decisions.get(section_id)
            row = dict(id=section_id, version=version, **section, requirements=linked,
                       sourceFingerprint=source_fingerprint, **(annotation(decision) if decision else default))
            refs = row["relatedRequirements"]
            assert isinstance(refs, list) and len(refs) == len(set(refs)), section_id
            valid_ids = {r["id"] for r in requirements if version in r["versions"]}
            assert set(refs) <= valid_ids, f"Unknown or wrong-version requirement link: {section_id}"
            if authored is not None:
                assert set(linked) <= valid_ids, f"Unknown or wrong-version assertion requirement: {section_id}"
                assertions = []
                for assertion in authored["assertions"]:
                    assert section["start"] <= assertion["start"] <= assertion["end"] <= section["end"], assertion["id"]
                    assert assertion["statement"].strip() and assertion["requirements"], assertion["id"]
                    for cid in assertion["caseIds"]:
                        assert cid in indexed_cases, f"Unknown assertion case: {cid}"
                        case = indexed_cases[cid]
                        assert case["version"] == version and case["requirement"] in assertion["requirements"], f"Unrelated assertion case: {cid}"
                        assert any(t.get("query") and t.get("expected")
                                   for axis in ("preservation", "structure")
                                   for t in case.get(axis, {}).values()), f"Assertion case has no answer test: {cid}"
                    # Even a same-version requirement case can leave part of an
                    # assertion untested; the authored testGap keeps that visible.
                    status = ("no-targeted-test" if not assertion["caseIds"] else
                              "partial-tests" if assertion["testGap"] else "targeted-tests")
                    assertions.append(dict(assertion, testStatus=status))
                assert len({a["id"] for a in assertions}) == len(assertions), section_id
                assert assertions or authored["exclusions"] or authored["reviewQuestions"], section_id
                row.update(anchorRequirements=anchors, assertions=assertions,
                           exclusions=authored["exclusions"], reviewQuestions=authored["reviewQuestions"],
                           assessmentOrigin="Codex source audit; human acceptance remains separate",
                           testCoverage={s: sum(a["testStatus"] == s for a in assertions)
                                         for s in ("targeted-tests", "partial-tests", "no-targeted-test")})
                row["requirementTests"] = [
                    {"requirement": rid, "caseIds": sorted(c["id"] for c in cases
                     if c["requirement"] == rid and c["version"] == version)}
                    for rid in linked]
                if previous and section_id in previous:
                    row["priorAnnotation"] = annotation(previous[section_id])
            # Keep a stale decision visible for correction; never silently renew it.
            issue = ""
            if decision and decision.get("sourceFingerprint") != source_fingerprint:
                issue = "Source changed; reread before saving this decision."
            elif authored and authored["reviewQuestions"]:
                issue = "Resolve the listed reviewQuestions in the assertion inventory before accepting this section."
                row["disposition"] = "needs-review"
            elif row["disposition"] not in DISPOSITIONS:
                issue = "Choose a documented disposition; previous wording has been retained."
            elif row["disposition"] in {"mapped", "duplicate"} and not (linked or refs):
                issue = "Link the requirements that account for this passage."
            elif row["disposition"] in RESOLVED and not row["note"].strip():
                issue = "Add a short rationale for this disposition."
            row["reviewIssue"] = issue
            row["savedAnnotationFingerprint"] = digest(annotation(row))
            rows.append(row)
    assert set(decisions) <= {r["id"] for r in rows}, "A saved section no longer exists; reconcile it before rebuilding"
    if coverage is not None:
        assert set(coverage) == {r["id"] for r in rows}, "Assertion inventory must include every source section exactly once"
    return rows


def resolved(rows):
    return all(r["disposition"] in RESOLVED and not r["reviewIssue"] for r in rows)


def save_annotations(worksheet, current, review):
    """Copy only edited reviewer fields; source identity and scores remain generated."""
    indexed = {r["id"]: r for r in current}
    decisions = review.setdefault("sourceSections", {})
    seen = set()
    for row in worksheet:
        key = f"{row['version']}:{row['start']}-{row['end']}"
        assert key in indexed and key not in seen, f"Unknown or duplicate source section: {key}"
        seen.add(key)
        actual = indexed[key]
        assert row.get("id", key) == key, f"Source section ID edited: {key}"
        for field in ("title", "zone"):
            assert row[field] == actual[field], f"Source metadata edited: {key} {field}"
        assert row["requirements"] == actual["requirements"], f"Use relatedRequirements for extra links; requirements is generated: {key}"
        for field in ("assertions", "anchorRequirements", "requirementTests", "testCoverage", "reviewQuestions", "exclusions", "priorAnnotation"):
            assert row.get(field) == actual.get(field), f"Edit the authored source-assertions input, not generated {field}: {key}"
        assert row.get("sourceFingerprint", actual["sourceFingerprint"]) == actual["sourceFingerprint"], f"Stale source section: {key}"
        if unsaved([row]):
            decisions[key] = dict(sourceFingerprint=actual["sourceFingerprint"], **annotation(row))
    assert seen == set(indexed), "Source sections were removed; use a disposition instead of deleting rows"
    return review
