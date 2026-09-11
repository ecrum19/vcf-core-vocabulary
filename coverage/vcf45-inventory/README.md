# Curated VCF 4.5 inventory

**Result: 104/104 curated logical-model constructs are classified as fully
represented; 87 of them additionally have a validation rule that tests a stated
requirement.**

## In plain terms

This is a **hand-written list** of the things VCF 4.5 can express — a file, a
header line, an allele, a genotype, a breakend, and 99 others — where each entry
names the vocabulary term that represents it and points at a file proving it.
Think of it as a map from "this part of the VCF spec" to "this part of the
vocabulary", with evidence attached to every row.

Because the list is authored, the 100% figure means **"everything on this list is
represented"**, not "everything in VCF is represented". A list cannot reveal
something nobody thought to put on it. That limit is the reason the repository
also runs a second, stricter assessment whose checklist is derived from the
specification text instead of authored:
[`methodology/`](../methodology/README.md). The two count different things and
their percentages must never be combined —
[why we keep both](../README.md#why-there-are-two-assessments).

What this does not claim: that every VCF requirement is represented, that
arbitrary VCF validates, or that source bytes reconstruct exactly.

## Inputs, outputs and execution

| File | Role |
| --- | --- |
| [inventory.json](inventory.json) | Authored inventory, rubric, per-entry axes, evidence, source-byte scope and exclusions. |
| [report.py](report.py) | Recomputes verdicts/statistics; checks declared terms and query paths; includes the separate representation summary. |
| [check_serialization.py](check_serialization.py) | Executes byte predicates on the source VCF fixtures. |
| [generated/report.json](generated/report.json) | Reproducible counts, recomputed from the inventory. |
| [generated/serialization.json](generated/serialization.json) | Executed byte-check results, separate from model coverage. |

Run from the repository root:

```sh
npm run coverage:report          # byte checks, then regenerate this report
npm run validate:serialization   # byte checks only
npm run validate:force           # the complete repository suite
```

`coverage:report` runs the byte checks and regenerates this report. `report.py`
first verifies that the specification-derived assessment's outputs are current,
so if its inputs changed, run `npm run methodology:build` before this.
The fixture summary in the report comes from
[the complete SHACL run](../../tests/generated/validation.json); reporting that
summary does not re-execute the SHACL suite. Use `validate:force` for a full run.

## Rubric

Each construct has three independently reviewed axes:

| Axis | Question |
| --- | --- |
| `preserved` | Does the source information survive in the graph? |
| `structured` | Can a graph pattern reach the construct without parsing a literal? |
| `enforced` | Does a validation rule test a stated requirement? |

The script derives the verdict from the first two axes:

```text
full    = preserved AND structured
partial = preserved AND NOT structured
absent  = NOT preserved
```

Enforcement does not increase representation credit. The script rejects verdicts
that contradict their axes and references to undeclared terms or missing queries.
It does not independently establish that a reviewer's axes are justified or that
the inventory is complete. The assessment's 104 constructs are also distinct from
122 current reserved-key resources; key declarations are counted separately.

## Evidence and modeling boundaries

The inventory is the sole per-construct checklist. Its references include the
paired fixtures and queries in [examples/](../../examples/README.md), the shared
and versioned [SHACL profiles](../../shacl/README.md), and the independent
[validation regressions](../../tests/README.md).

Several distinctions matter when interpreting its full scores:

- **Bracketed CHROM:** `AssemblyContig`, its parsed identifier and assembly source
  distinguish an assembly-contig reference from a reference-contig declaration.
- **Telomeric POS:** numeric positions and linked contig length expose 0 and N+1;
  a dedicated telomere flag is not necessary for that query.
- **Padding:** `PaddingInterpretation` records a selected rule and anchor. Internal
  consistency does not establish that an arbitrary variant was interpreted correctly.
- **Missingness:** a field-level `Null` and indexed missing items distinguish source
  spellings and positions. An all-dot list can express wholly missing information.
- **Trailing FORMAT fields:** the ordered `FormatKey` sequence makes omitted
  declared fields distinguishable from undeclared fields.
- **Percent encoding:** raw and decoded values expose both forms; preservation
  alone does not prove complete lexical or capitalization enforcement.
- **Expanded/condensed samples:** ordered vectors preserve cells, but querying
  their contents may require decoding or materialization.

The [specification-derived assessment](../methodology/README.md) tests expected query answers and reports the two representation profiles separately. Its registered denominator is distinct from this inventory.

## Source bytes and limits

Encoding, BOM state, allowed control characters and line terminators are checked
on bytes. They do not earn logical-model representation credit. Current byte
fixtures exercise LF and CRLF. A passing fixture set does not prove arbitrary-input acceptance.

No VCF 4.0 overlay is supplied. BCF encoding, exact byte preservation, unrestricted
conversion fidelity, exhaustive complex-event reconstruction, all repeat-list
combinations and external-reference biological truth are not established here.
A missing construct, unsupported structured axis, or counterexample to an asserted
rule can falsify or narrow the corresponding claim. Review the inventory, amend
its evidence and regenerate; do not fix the percentage directly.
