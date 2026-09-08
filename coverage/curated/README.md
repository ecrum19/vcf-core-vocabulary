# Original VCF 4.5 curated assessment

**Result: 104/104 curated logical-model constructs are classified as fully
represented; 87 additionally have enforcement evidence.** This is the original
assessment used by the manuscript. It is not a claim to represent every VCF
requirement, to validate arbitrary VCF, or to reconstruct source bytes exactly.
The separate [4.1–4.5 assessment](../methodological/README.md) uses a different,
more demanding specification-derived requirement register.

## Inputs, outputs and execution

| File | Role |
| --- | --- |
| [inventory.json](inventory.json) | Authored inventory, rubric, per-entry axes, evidence, source-byte scope and exclusions. |
| [report.py](report.py) | Recomputes verdicts/statistics; checks declared terms and query paths; includes the separate requirements summary. |
| [check_serialization.py](check_serialization.py) | Executes byte predicates on the source VCF fixtures. |
| [generated/report.json](generated/report.json) | Reproducible counts consumed by the manuscript figure checker. |
| [generated/serialization.json](generated/serialization.json) | Executed byte-check results, separate from model coverage. |

Run from the repository root:

```sh
npm run coverage:report
npm run validate:serialization
npm run validate:force
```

`coverage:report` checks that the specification-derived outputs are current,
regenerates the curated and byte reports, and runs
[the manuscript checker](../paper/check_figures.py). If decisions or workflow
inputs changed, first run `npm run methodological:build`.
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

The inventory contains stronger representation judgments than the later
specification-derived review. Its full scores do not override the later findings
about extension-header IDs, numeric modification declarations or PS/PSL lists.

## Source bytes and limits

Encoding, BOM state, allowed control characters and line terminators are checked
on bytes. They do not earn logical-model representation credit. Current byte
fixtures exercise LF and CRLF. The separate review also records rejection of mixed
LF/CRLF as an interpretation-dependent finding; a passing fixture set does not
prove arbitrary-input acceptance.

No VCF 4.0 overlay is supplied. BCF encoding, exact byte preservation, unrestricted
conversion fidelity, exhaustive complex-event reconstruction, all repeat-list
combinations and external-reference biological truth are not established here.
A missing construct, unsupported structured axis, or counterexample to an asserted
rule can falsify or narrow the corresponding claim. Review the inventory, amend
its evidence and regenerate; do not fix the percentage directly.
