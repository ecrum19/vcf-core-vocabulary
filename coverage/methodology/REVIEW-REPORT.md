# Coverage assessment: review record

**Reviewed and accepted by Elias Crum, 11 September 2026.** All 94 requirements and the source
audit carry a recorded decision in [inputs/review.json](inputs/review.json), each with the
rationale given at the time; `npm run methodology:check -- --require-reviewed` exits 0.

Two agent passes prepared the material — a VCF-expert reading of the five pinned specifications
on 10 September, then the tests it asked for on 11 September — and every decision below was
taken by the reviewer, one item at a time, against the evidence.

Reviewed artefact: `coverage/methodology/` at the pinned sources in
[sources.lock.json](sources.lock.json); all five SHA-256 pins re-verified.
Current scores are in the [assessment README](README.md#scoring-and-outcome) and are regenerated,
so they are not repeated here.

## What the assessment claims

The two axes, the exclusions and the equal weighting of requirements are appropriate, and the
intended claim — **demonstrated coverage of registered information requirements** — is the one
the evidence supports. Complete specification coverage is not supported and the README says so.

Three qualifications came out of the review:

1. **Structured-header attribute order is not information.** VCF 4.4 and 4.5 state that
   implementations "must not rely on the order of the fields within structured lines and are not
   required to preserve field ordering", and present the recommended ID/Number/Type/Description
   sequence as a readability aid; 4.1–4.3 nowhere give the order meaning. R34 covers identity,
   value and escaping only. This is distinct from R02, the order of meta-information *lines*,
   which is legitimately scored.
2. **The condensed structure column measures a profile choice**, not the vocabulary — see
   [below](#the-condensed-structure-failures).
3. **"333/333 declarations match" covers a version-biased subset** — see
   [below](#32-reserved-declarations-333-rows).

---

# Source interpretations resolved

Twenty-one passages were flagged as ambiguous or defective and each was resolved against the
pinned text. The full decision for each lives in the corresponding row of
[source-audit.json](generated/source-audit.json); this is the summary. The section numbers are
referenced elsewhere in this document and from the assertion inventory, so they are stable.

### 2.1 Legacy GLE — `4.1:193-222`, `4.2:210-239` → accepted unassessed limitation

No valid sample-column serialization can be derived from the text: the reserved example value
`0:-75.22,1:-223.42,…` uses `:` internally, which is the FORMAT sub-field separator, no escaping
rule or complete sample column is given, and the printed `GLE=` prefix is INFO syntax. VCF 4.3
removes the key as "unused and ill-defined". GLE stays in scope only as an opaque declared String
value; R80 stays unassessed for 4.1/4.2.

### 2.2 Deletion length — `4.1:468-523` → 205 bp

`POS=321682`, `END=321887` and `SVLEN=-205` all agree on 205 deleted bases, with `REF=T` at POS as
the padding base. The prose "105 bp" is a typo, and the pinned 4.2 (line 534) and 4.3 (line 874)
both print "205 bp".

### 2.3 Complete assembly insertion `C<ctg1>` — `4.1:586-638`, `4.2:603-655`, `4.3:1000-1052`

The shorthand row `13 321682 INS0 T C<ctg1>` copies its POS and REF from the unrelated chr2
breakend row. The flanking pair places the insertion between 13:123456 (`REF=C`) and 13:123457, so
the consistent record is **`13 123456 INS0 C C<ctg1> 6 PASS SVTYPE=INS`**; VCF 4.4 independently
corrects the same row. Any oracle must come from the flanking BND pair, and the corrected row is a
reviewer correction rather than spec-verbatim — which is why
the registered R92 case uses the BND pairs and omits the shorthand row.

### 2.4 Legacy haplotype bundles, BDP/BCN — `4.1:911-954`, `4.2:928-971`, `4.3:1376-1427`

BDP and BCN occur exactly once each, in one prose sentence, with no declaration, Number, Type,
reserved-table entry or complete record; the bundle table's haplotype cells (`1>11`,
`2,3,4>12,13,14`) have no VCF grammar; VCF 4.4 deprecates bundles. Accepted unassessed limitation,
R94 stays unassessed. The quantities *are* declared under other names — DP/CN, **DPADJ/CNADJ**,
HQ, HAP/AHAP — which is where the R79 test came from.

> **Defect recorded here:** DPADJ, CNADJ and CICNADJ are declared as `##INFO=` lines in 4.1–4.3
> yet used as FORMAT keys in those very examples (`GT:DPADJ`, `GT:CNADJ`). The FORMAT usage is
> what the R79 case assesses.

### 2.5 Quality probabilities — `4.3:586-600`, `4.4:651-665`, `4.5:824-840` → error probability

The Q-suffix sentence calls the quantity a "log-complementary … posterior probability" but prints
−10 log₁₀ Pr(Data|Model), which is neither complementary nor posterior. The normative per-key
definitions govern: GQ is −10log₁₀ p(genotype call is wrong …) and CNQ likewise. A Q-suffixed value
is −10 log₁₀ (1 − Pr(Model|Data)). No assessment impact.

### 2.6 CNL ordering — `4.3:672-691`, `4.4:981-1002`, `4.5:1142-1163`

The prose governs: CNL is indexed by copy number from zero, so the value at 0-based index *i* is
log₁₀ L(CN = *i*), and cardinality is data-determined. The declared `Number=G` is a specification
defect carried over from GL — G is a function of allele count and ploidy, which cannot give
max(CN)+1. CNP inherits the same reading. R77 still has no case.

### 2.7 Older gVCF `GT:DP:GQ:P` — `4.3:1428-1451`, `4.4:1686-1711` → `PL`

`P` is a typo for `PL`: no reserved FORMAT key `P` exists; the six comma-separated integers are
exactly G for three alleles at ploidy two; they are integers, matching PL rather than GL or GP; and
`GQ=52` is the second-smallest of `0,52,95,66,95,97`, which is how GQ relates to PL. Applied in the
new `gvcf-blocks-v4.{3,4}.vcf` fixtures.

### 2.8 Header attribute order — `4.4:105-142`, `4.5:103-140`

Excluded from the scored requirement, retained as an unscored fidelity extension. See §1.

### 2.9 PSL / PSO — `4.4:445-639`, `4.5:497-812`

**The printed PSL table is a specification defect**, on three counts: `GT=|1/2|3` uses allele
index 3 where ALT lists two; `GT=1|2` uses index 2 where ALT lists one, and with the leading
indicator omitted and no `/` present 4.4/4.5 make the first indicator implicitly `|`,
contradicting its own `PSL=.,chr20*10*1`; and ploidy differs between rows for the same sample on
the same CHROM. **Reported upstream as
[samtools/hts-specs#871](https://github.com/samtools/hts-specs/issues/871).**

The reviewer's corrected rows — `GT=|1/2|2` and `GT=/0|1/0`, with in-range indices, explicit
leading indicators and consistent ploidy — are the registered oracle, tested in
`R82-4.{4,5}-phase-quality` together with PSQ values the reviewer authored, the specification
defining PSQ at `4.5:808-809` with no worked example. That case checks the per-allele phase-set
names, a name reused across chromosomes, and the positional PSQ values including the missing
ones.

**PS versus PSL** is likewise normative without an example: `4.5:775-776` says a sample-genotype
must not carry both, and that the two are not interoperable because PS is not tied to a specific
haplotype. `R82-4.{4,5}-phase-separation` uses a reviewer-authored record in which two samples
describe the same haplotype pair, one through PS and one through PSL, and checks that neither
exposes the mechanism it does not use.

**PSO is consistent and supplies the oracle**, now registered as `R82-4.{4,5}-phase-ordinals`:

| Record | GT slot | PSL | PSO |
| --- | ---: | --- | ---: |
| chr1:10 `<DUP>` | 3 | `chr1*10*3` | 3 |
| chr1:20 REF A | 3 | `chr1*10*1` | 4 |
| chr1:20 ALT G | 4 | `chr1*10*3` | 1 |
| chr1:30 REF G | 3 | `chr1*10*1` | 2 |
| chr1:30 ALT T | 4 | `chr1*10*3` | 5 |

Ordinals 1–5 occur exactly once each: ALT G at chr1:20 → REF at chr1:30 → the duplication junction
→ REF at chr1:20 → ALT T at chr1:30. Exactly the stated reading that the first SNV lies on the
first copy of the duplicated region and the second on the second copy. The rise from three to four
allele values inside the duplicated interval is intended.

### 2.10 Repeat field names — `4.4:666-980`, `4.5:841-1141` → RS→RUS, RL→RUL, RC→RUC

No key named RC, RS or RL is declared anywhere; the declared repeat keys are RN, RUS, RUL, RUC, RB,
RUB, CIRUC and CIRB. Three affected sentences per version (4.4 lines 973, 1759, 1827; 4.5 lines
1134, 1928, 1995). The overview's list "RN, RS, RL, RB, RC and RUL" both mis-spells three names and
repeats RUL; corrected it reads **RN, RUS, RUL, RUC, RB and RUB**.

The same correction settles the RUB nesting question: **RUB is partitioned by RUC** (one value per
repeat *unit*) while **RUS, RUL, RUC and RB are partitioned by RN** (one value per repeat
*sequence*). Two different flattening rules in one record, never stated as such. The R46 case
covers the RN rule; the RUB rule (R88) is still untested.

### 2.11 Structural-variant examples — `4.4:1181-1233`, `4.5:1342-1393`

With `chrA = ATGCGAAAAAAATGT`:

* **delbp2.** `delbp1` at chrA:2 has `ALT=T[chrA:5[`, so its mate is at chrA:5, where the reference
  base is G. The printed `chrA 2 delbp2 A ]chrA:2]A` has the wrong POS, the wrong REF and a
  self-referential mate. The correct reciprocal is
  **`chrA 5 delbp2 G ]chrA:2]G . . MATEID=delbp1;EVENT=DEL_split_bp_cn GT 0/1`**.
* **DUP.** `chrA 5 . G <DUP> … SVLEN=3;CIPOS=0,5` omits SVCLAIM, which 4.4/4.5 make mandatory for
  DEL/DUP. The example does not determine the value (DJ is readable, D is too), so it is excluded
  as an SVCLAIM oracle.
* **Erratum:** `chrA 14 . T <INS>` gives `REF=T` where the stated sequence has **G** at 14 — and
  the next row correctly writes `chrA 14 . G .CCCCCCG`. Both 4.4 and 4.5.

### 2.12 Partial / circular insertions — `4.4:1308-1360`, `4.5:1468-1520`

MATEID cannot serve as an oracle here: the partial table gives `bnd_U → bnd_U` and `bnd_V → bnd_V`,
the circular table repeats those and adds `bnd_Y → bnd_C`, an identifier that appears nowhere. More
fundamentally a MATEID names the breakend at the other end of the *same* adjacency, and the
contig-side breakends have no records — so even the first table's `MATEID=bnd_V`/`bnd_U` are wrong.
EVENT is the correct grouping mechanism, and the circular table already uses it. The one
determinable correction is `bnd_Y → bnd_X`. The `R92-4.5-contig-insertions` case is built exactly
this way, and reciprocal mates (R32) are tested on the Figure 1 example in `breakends-v4.5.vcf`.
**Reported upstream as [samtools/hts-specs#869](https://github.com/samtools/hts-specs/issues/869).**

### 2.13 Sample mixtures — `4.4:1571-1615`, `4.5:1731-1775` → version-scoped

`##SAMPLE=<ID=…,Genomes=…,Mixture=…>` is the normative SAMPLE grammar in 4.1/4.2 (4.1 line 129, 4.2
line 146), with the semicolon-separated lists positionally aligned. In 4.3–4.5 the normative
definition is the META-driven form and this example is retained but no longer normatively defined;
assess it there as generic structured-attribute retention (R34/R59). R35's version list was
deliberately left unchanged so the clarification cannot raise a percentage. **Accepted
limitation:** Genomes and Mixture use unquoted `;` as list separators while the parallel
Description list is a single quoted string containing `;`, so positional pairing of Description
entries is not recoverable by grammar alone.

> **Erratum, all five versions:** in these breakend tables `bnd_W` at 2:321681 has
> `ALT=G]2:421681]` with `MATEID=bnd_U`, and `bnd_V` at 2:321682 has `ALT=[2:421682[T` with
> `MATEID=bnd_X`, but `bnd_U` and `bnd_X` are on **CHROM 13**. The ALT coordinates should read
> `13:421681` and `13:421682` — applied in the `adjacency-v4.*.vcf` fixtures.

### 2.14 Tandem repeats — `4.4:1748-1879`, `4.5:1917-2047`

1. Obsolete key names, as §2.10.
2. `CAGCAGCAGTTGTTG` is **(CAG)₃(TTG)₂**, not (CAG)₄(TTG)₂ — three CAG units, fifteen bases.
   **Reported upstream as [samtools/hts-specs#870](https://github.com/samtools/hts-specs/issues/870).**
   Corrected figure values: `RN=2,1`; `RUS=CAG,TTG,CA`; `RUL=3,3,2`; `RUC=3,2,3`; `RB=9,6,6`, with
   the second allele `CACACA = (CA)₃`. This is the Figure 11 locus in the new fixture.
3. RUL/RUB nesting: RUB by RUC, the rest by RN.
4. **The main worked example is internally consistent and usable**, verified arithmetically:
   reference (CAG)₁₀ at 101–130 (`SVLEN=30`, POS=100 padding); allele 1 (CAG)₃₀ = 90 bases with
   `RN=1`, `RB=90`, INFO `CN=90/30=3`; allele 2 (CAG)₅(CA)(CAG)₄ = 29 bases with `RN=3`,
   `RUS=CAG,CA,CAG`, `RB=15,2,12`, INFO `CN=29/30`; flattened exactly as printed; FORMAT
   `CN=(90+29)/30`. The phased non-symbolic rows check out too, and printed CN values are truncated
   rather than rounded. The CIRUC example is likewise consistent (65×3/30 = 6.5).
5. **Erratum:** the RUB example `SVLEN=20000;CN=1.25;RUL=10000;RUC=5;RUB=10000,…,12000` is
   arithmetically inconsistent — Σ RUB = 55000 gives 2.75 and RUL×RUC = 50000 gives 2.5, neither of
   which is 1.25. Excluded as a CN oracle; still usable for RUB cardinality.
6. **Erratum, 4.4 only:** the same record carries `END=20000` at `POS=1000000`. It should read
   1020000; removed in 4.5.

### 2.15 `Number=P` erratum — `4.4:2558-2563`, `4.5:2740-2745`

"Type=P" is a drafting error for "Number=P": the main text lists P among the FORMAT Number
possibilities and the reserved table gives PSL/PSO `Number=P`. The 4.5 changelog corroborates.

### 2.16 Mandatory FORMAT attributes — `4.4:2564-2591`, `4.5:2746-2773`

The main text governs: ID, Number, Type and Description are required for both `##INFO` and
`##FORMAT`. The changelog's "only INFO" claim is wrong. R03 and R52 need no change.

### 2.17 Base modifications — `4.5:184-248`, `4.5:497-812`

**`MXaoN`, `DPMXaoN`, `ADMXaoN` with a capital X are normative**, per the reserved genotype-key
table; "Xao" is the standard abbreviation for xanthosine, matching `M5mC`, `M8oxoG`, `M6mA`. The
four prose occurrences of `MxaoN` are typos, and FORMAT keys are case-sensitive.
`declarations.json` already uses the table form.

**The four examples need no correction and now serve directly as the R84 oracle:**

| Record | Reasoning | Values |
| --- | --- | ---: |
| `chr 10 C A GT:M5mC 0/1:0.95` | C → 1; A → 0 | 1 |
| `chr 20 C CTAG GT:M5mC 0/1:0,0.5,0.7` | C → 1; CTAG → 2 (forward C at base 1, reverse-strand C opposite the G at base 4) | 3 |
| `chr 30 C . GT:M5mC:M5hmC 0\|0:0.9,0:0,0.1` | two phased C copies | 2 per field |
| `chr 40 C A,T,G,ACG GT:M5mC /3\|1/0\|4\|0/0/3/1:0.25,0.1,0.5,0.6,.` | GT order with unphased aggregation at first occurrence: G→1, A→0, C→1, ACG→2, phased C→1, then three repeats contributing none | 5 |

### 2.18 Local versus global genotypes, `GT=2/4` versus `GT=2/2` — `4.5:497-812` → **`2/2`**

GT is `Number=1, Type=String` and is **not** a local-allele field, so it carries global indices in
both rows — confirmed by row 2, where both rows print `0/3`. With `LAA=2,4` the local alleles are
`[G(REF), C, <*>]`; `LPL=90,80,0,100,110,120` is minimal at local 1/1 = C/C, and the global PL is
minimal at index 5 = 2/2 = C/C. Every other value maps consistently and `LAD=20,30,10` matches
`AD=20,.,30,.,10`. Rows 2–4 verified the same way. This row is now the `R27-4.5-local-allele-map`
fixture.

### 2.19 VCF 4.5 gVCF separators and LEN — `4.5:1846-1880`

* **Separators:** the `;` before each LEN value must be `:`; semicolon is the INFO separator.
* **LEN is the inclusive block length, so `END = POS + LEN − 1`.** The row `POS=4390, END=4390,
  LEN=1` is decisive, and `POS=4370, END=4383, LEN=14` confirms it. Corrected values: 4370→14 (as
  printed), 4384→**5** (printed 4), 4390→1, 4391→**5** (printed 4), 4397→**20** (printed 19).
* **Erratum:** the 4396 row is a variant row with no reference block, so MIN_DP and LEN do not
  apply and its four supplied sub-fields make MIN_DP absorb the PL vector. Its corrected FORMAT is
  `GT:DP:GQ:PL`.

`gvcf-v4.5.vcf` and `queries/r30-decode.rq` already implemented `END = POS + LEN − 1` and are
confirmed correct. **Reported upstream as
[samtools/hts-specs#868](https://github.com/samtools/hts-specs/issues/868)**, and because the
corrections above are what that issue disputes, the R45 tests drafted on them were withdrawn
rather than registered; R45 stays unassessed until #868 closes.

### 2.20 VCF 4.5 changelog — `4.5:2726-2739`

**`Number=P` was introduced in VCF 4.4, not 4.5** — the pinned 4.4 text defines it, gives PSL/PSO
`Number=P` and records it in the 4.4 errata. What 4.5 adds is the `M` Number and the local-allele
Numbers. **Modification key syntax:** the changelog's `M[0-9]+` is incomplete; the main text
reserves `M[0-9]+[ACGTUN]`, `DPM[0-9]+[ACGTUN]` and `ADM[0-9]+[ACGTUN]`, the trailing base letter
being required, with U synonymous with T.

---

# Source inventory completeness

### 3.1 What was verified, and how

The 344 sections partition every line of all five pinned sources with no gaps or overlaps; every
assertion lies inside its section, links at least one valid same-version requirement, and every
requirement is referenced. All 396 reserved-key assertions and all 119 changelog assertions were
verified mechanically against their passages; the 619 authored VCF-zone assertion instances reduce
to 150 distinct statements, each read individually. No VCF-zone content is excluded: the 98
`out-of-scope` sections are BCF, preamble and BCF-changelog material, and the 20 `context-only`
ones are single-line headings.

### 3.2 Reserved declarations (333 rows)

All 333 rows are faithful reproductions. The comparison covers only explicitly declared keys, so
**29 reserved keys per version in 4.1 and 4.2** (58 rows) are inventoried but not Number/Type
compared, because those versions define them in prose bullets with no Number and, for INFO, no
Type. The agreement figure is therefore weighted towards 4.3–4.5, and the README says so. Four of
the 333 rows are duplicate declarations of the same key in one source; the duplicates agree.
---

# What the registered tests cover

Nine tests were requested by the review; eight are registered and one (R45) was drafted and
withdrawn. Three more were added at the reviewer's request while signing.

| Requirement | Fixtures | Oracle | Not covered |
| --- | --- | --- | --- |
| **R27** local alleles | `local-alleles-v4.5.vcf` | The equivalence table's `LAA=2,4` on a four-ALT record, so local position 1 is global allele 2, plus a REF-only row with an empty LAA | — |
| **R29** modification depths | `features-v4.5.vcf` | Fraction, detecting depth and modified-read depth returned separately for one modification | — |
| **R31 / R46** repeat units and RN | `tandem-repeats-v4.{4,5}.vcf` | Two loci with *different* RN partitions (1,3 and 2,1), so ignoring RN cannot answer both | `RUB`'s partitioning by RUC (R88); a defaulted RN; RUL inferred from RUS |
| **R45** reference blocks | *withdrawn* | Drafted against this reviewer's reading of four corrections the gVCF tables need, then withdrawn: those corrections are disputed in [#868](https://github.com/samtools/hts-specs/issues/868) | everything; R45 stays unassessed until #868 closes |
| **R79** adjacency depth | `adjacency-v4.{1,2,3}.vcf` | The two worked cancer-genome tables, one sample column per table plus the Blood column both share | `CICNADJ`, which has no worked example; the segment-scoped DP/CN contrast |
| **R82** phase sets | `phase-ordinals-`, `phase-quality-`, `phase-separation-v4.{4,5}.vcf` | The PSO example's traversal order 1–5; the PSL table with corrected genotypes and authored PSQ values; a two-sample record separating PS from PSL | — |
| **R83** local↔global | `local-alleles-v4.5.vcf` | Both rows of all four pairs: a `Number=LR` depth and a `Number=R` depth join through the allele each resolves to | The `LPL`→`PL` genotype correspondence, which the graph cannot express — see the repository README |
| **R84** Number=M slots | `modifications-v4.5.vcf` | All four specification examples verbatim; value counts re-derived from the cardinality rules | U/T equivalence; the unstranded storage convention |
| **R85** modification keys | `modifications-v4.5.vcf` | `M5mC` beside `M27551C` on one modification, `DPM`/`ADM` depths, an unrecognised numeric identifier, `MXaoN` on both strands | The remaining alias keys |
| **R89** repeat ratios | `tandem-repeats-v4.{4,5}.vcf` | Reference SVLEN 30, allelic CN 3 and 0.9666, overall 3.9666, and phase set 100 as the relation to the non-symbolic records | Sequence-level equivalence; `CIRUC`/`CIRB` |
| **R92** contig insertions | `contig-insertions-v4.5.vcf` | Complete, partial and circular insertions: boundary and direction from the ALT brackets, grouped by EVENT | The 4.1–4.4 equivalents; the shorthand row |

Three cases are **reviewer-authored rather than spec-verbatim**, and say so in their `note`:
R82's PSQ and PS/PSL records, and both of R85's. In each the rule is normative but the
specification prints no record exercising it.

## Corrections carried into the fixtures

Nothing silently claims to be spec-verbatim; each case `note` records the correction it carries.

| Fixture | Correction | Decision |
| --- | --- | --- |
| `adjacency-v4.*.vcf` | `bnd_W`/`bnd_V` ALT coordinates read `13:421681`/`13:421682`, their mates being on CHROM 13 | §2.13 |
| `adjacency-v4.*.vcf` | DPADJ and CNADJ declared as `##FORMAT`, the examples using them there although the specification declares them as `##INFO` | §2.4 |
| `tandem-repeats-v4.*.vcf` | Figure 11 reads `RUS=CAG,TTG,CA`, `RUL=3,3,2`, `RUC=3,2,3`, `RB=9,6,6` for `(CAG)₃(TTG)₂` | §2.14 |
| `tandem-repeats-v4.*.vcf` | The two non-symbolic rows print only nine columns, omitting INFO; `.` is supplied | §2.14 |
| `local-alleles-v4.5.vcf` | Row 1's GT reads `2/2`, not the printed `2/4` | §2.18 |
| `phase-quality-v4.*.vcf` | `GT=\|1/2\|2` and `GT=/0\|1/0`, replacing indices beyond the ALT list and an ambiguous leading indicator | §2.9 |
| `contig-insertions-v4.5.vcf` | MATEID registered only for `bnd_X`/`bnd_Y` | §2.12 |

Where a source example could not be corrected it was moved: the three assembly-contig insertions
all reuse POS 123456/123457 and the IDs `bnd_U`/`bnd_V`, so the partial and circular ones sit at
distinct positions and are grouped by EVENT; Figure 11 has no coordinates and was placed at
chr1:200.

## Changes the tests forced in the converter

`scripts/vcf_examples.py` could not represent three source examples at all — it raises rather
than guessing — so three changes were made, all using vocabulary terms that already exist:

1. **Number=M keys are parsed as a family**: `M`/`DPM`/`ADM` followed by a ChEBI identifier or one
   of the ten documented aliases, then the base letter, with U treated as T and N reporting both
   strands. The alias table mirrors `scripts/generate-reserved-keys.mjs`.
2. **The aggregation rule is implemented.** "Unphased allele values are aggregated and encoded at
   the position of the first occurrence" was not applied, so the specification's own octoploid
   example was rejected as a cardinality mismatch. This was a genuine defect. The fix was checked
   against nine genotype patterns, including `|0/0/0` and `/0|0`, which pin down that aggregation
   groups unphased occurrences only.
3. **A breakend mate may lie on an assembly contig.** `C[<ctg1>:1[` previously raised; the
   angle-bracketed form now resolves to the same `AssemblyContig` resource an angle-bracketed
   CHROM already used.

Base-modification resources are now keyed by ChEBI identifier and strand as well as by allele
slot and offset, so two chemistries on one base stay apart. The only effect outside the
methodology fixtures is four IRIs in `examples/vcf-versions/vcf-4.5/example-vcf45-features.ttl`.

## The condensed structure failures

Every failing witness — 45 of them — is a condensed-profile **structure** query over
per-sample FORMAT data, and every one passes on the structure axis in the expanded profile.

The cause is by construction. The condensed profile emits, per record and FORMAT key, a single
`vcfc:FormatValueVector` carrying `vcfc:encodedValues` plus `vcfc:appliesToSampleSet`, and no
per-sample node at all. Neither the vector nor the sample set exposes per-index items, so there is
no RDF path from a sample to its own value, and the structure axis forbids parsing the compound
literal.

**Verdict: neither a vocabulary limitation nor an assessment error.** It is a correctly reported
consequence of a profile design that trades structural accessibility of per-sample values for
compactness. A preservation pass does not and should not resolve it.

## Defects found in the assessment's own inputs

| Finding | Action |
| --- | --- |
| **R47 and R48 anchors are swapped** in 4.1/4.2, and R47's 4.3–4.5 anchors point at "Fixed fields" instead of "Data types" | Fixed; anchor hashes recomputed |
| **`repeats-v4.5.vcf` CN values were internally inconsistent** with `SVLEN=30`, `RUC=10`, `RB=30` | Fixed to `CN=1` / `0/1:2`; no expected answer changed |
| **R27's local-allele case is a degenerate oracle** — `LAA=1,2` on a two-ALT record makes the mapping the identity | Superseded by `R27-4.5-local-allele-map`; the weak case is retained as extra evidence |
| **`4.5:497-812:A16` claimed a targeted test** although ADM was never queried | Closed by `R29-4.5-modification-depths` |
| **A stray `\label` was folded into two section titles** by the heading extractor | Fixed in `scripts/source.py`; the two stored section fingerprints were updated, the passage text being unchanged |
| **`features-v4.5.vcf` uses `CILEN=15,25` as absolute bounds**, and **`boundaries-v4.5.vcf` uses `<*>` without `##ALT=<ID=*>`** | Reported, not changed — both fixtures are byte-identical copies of published examples |

Yes, if read alone — and the README forbids reading them alone. Two reasons to keep in view:

1. **The denominators are dominated by untested requirements** (40 of 91 in 4.5, down from 47).
   "51/91 demonstrated" is not "56% of VCF 4.5 is covered"; it is "56% of the registered
   requirements have at least one passing witness in this profile and axis".
2. **Requirement granularity is uneven.** R67 and R68 each stand for *every* reserved INFO or
   FORMAT key's meaning and value scope — 396 reserved-key assertions between them, none with a
   targeted case — while R01 stands for a single header value.

Report the numerator/denominator pair with the unassessed count beside it, never a bare
percentage, and cite the assertion test inventory (149 targeted / 154 partial / 831 without a
targeted case) as the workload measure it is.

---

# Open work

## Deliberately not changed

| Item | Why | What you would have to decide |
| --- | --- | --- |
| `features-v4.5.vcf` uses `CILEN=15,25` as absolute bounds around `SVLEN=20` | The CILEN paragraph omits the "relative to" that CIPOS, CIEND, CIRUC and CIRB carry, but the specification's only CILEN example (`SVLEN=100;CILEN=-50,50`) is only readable as relative offsets. No registered case queries CILEN, so nothing is currently wrong | This fixture is a **byte-identical copy** of `examples/vcf-versions/vcf-4.5/example-vcf45-features.vcf`. Correcting it to `CILEN=-5,5` is an examples-level change that ripples into the published TTL, the SHACL snapshots and the profile comparison. Worth doing as its own change, with a CILEN case added at the same time |
| `boundaries-v4.5.vcf` uses `<*>` without an `##ALT=<ID=*>` line | Declaring it is recommended, not required, so the file is legal | Same copy-of-an-example situation. Adding the line would let R53/R54 test the declaration-to-allele link for `<*>` |
| The original `R27-4.5-local-alleles` case is retained | Removing it would have deleted evidence; it is simply weak on its own. Its degenerate `LAA=1,2` mapping is now stated in the requirement's interpretation, and the new case carries the real oracle | Whether to keep both or retire the weak one |
| R92 has a case only in 4.5 | The passage is nearly identical in all five versions, but each extra version is another fixture with its own breakend syntax to get right | Whether 4.1–4.4 need their own cases or the version gap is acceptable |
| PSQ, `<NON_REF>`, U/T equivalence, CICNADJ | No worked example exists to author an oracle from. Inventing one would test the converter against itself | Whether to accept them as gaps or author reviewer-designed fixtures, clearly labelled |

## Tests not written

* **R45** — reference blocks, pending [#868](https://github.com/samtools/hts-specs/issues/868).
  Drafted and withdrawn; register once the specification settles the gVCF corrections.
* **R77** — CNL/CNP indexed by copy number from zero, despite the declared `Number=G` (§2.6).
* **R88** — RUB partitioned by RUC while the other repeat lists are partitioned by RN (§2.10).

## Accepted unassessed limitations

No source-derived oracle exists for **R80** (GLE — the value contains the sample sub-field
separator and 4.3 removes the key), **R94** (BDP/BCN — undeclared, unserialized, deprecated in
4.4), or the positional pairing of SAMPLE `Description` entries under **R35**.

## Errata reported upstream

| Finding | Issue |
| --- | --- |
| gVCF separators, LEN values and the MIN_DP row (§2.19) | [#868](https://github.com/samtools/hts-specs/issues/868) |
| Self-referential and undefined MATEIDs in the contig insertions (§2.12) | [#869](https://github.com/samtools/hts-specs/issues/869) |
| Figure 11's `(CAG)4` exponent, and the tandem-repeat rows omitting the INFO column (§2.14) | [#870](https://github.com/samtools/hts-specs/issues/870) |
| The PSL table's allele indices, leading indicator and ploidy (§2.9), and `GT=2/4` in the local-allele table (§2.18) | [#871](https://github.com/samtools/hts-specs/issues/871) |

Still to report: the `delbp2` row and the `<INS>` REF base (§2.11), the cross-chromosome breakend
ALT coordinates (§2.13), the RUB example's CN and 4.4's `END=20000` (§2.14), and the `MxaoN`
spelling (§2.17).

## Housekeeping

The 83 requirements not revisited in the signing session carry fingerprints refreshed
mechanically — their text, cases, fixtures, queries and expected answers are byte-identical to
what was accepted on 10 September — but their `reviewer` field still names the agent pass.
Replace it, or state in the README that those entries stay attributed to it. `review.json` is
outside the provenance hash set, so editing the name invalidates nothing.

---

# Reviewer reference

## What you edit, and what is generated

Everything under `generated/` is rebuilt from the authored inputs and must never be hand-edited.

| File | Required judgment |
| --- | --- |
| [requirements.json](inputs/requirements.json) | `question`, `interpretation`, `testPlan`, `versions`, `anchors.{version}`, `area`. Are capability and version scope faithful to the source? Keep IDs stable. |
| [cases.json](inputs/cases.json) | `requirement`, `version`, `fixture`, `note`, and each axis/profile's `query` and `expected`. Does the expected answer follow from the source? Reused query code needs reading once; each case's expected answers and version need checking. |
| [source-assertions.json](inputs/source-assertions.json) | The authored passage interpretations, their requirement links, `caseIds`, `testGap` and exclusions. This is input data, not automatic extraction. |
| [declarations.json](generated/declarations.json) | `version`, `line`, `kind`, `key`, `number`, `type` against the reserved definitions, and extraction omissions. `status`/`actual` report literal comparisons. |
| [results.json](generated/results.json) | Join `requirements[].requirement` and `queries[].case` to input IDs. Inspect every version/profile, both axes, `status`, `expected`, `actual`, `witness` and the controls. Check meaningful passes as well as failures. |
| [summary.json](generated/summary.json) | `byVersion` denominators, axis counts, `percentDemonstrated`, `sourceAssertions`, `declarations`, `pendingReviews`. Arithmetic is automated; judge whether the scope supports the claims. |

Within `expected`, outer arrays are answer rows and columns follow the SPARQL `SELECT`. Row order
is ignored; duplicate rows count. JSON `null` means unbound; `"."` is the VCF missing-value token.
**Never change an expected answer merely to match execution.**

## Source-audit rows

One row inventories a source section, not a test outcome. `requirements` holds the explicit
semantic links from the authored assertions; the old line-overlap suggestions remain as
`anchorRequirements`, and an overlap alone never establishes that a passage is accounted for.
`assertions[].testStatus` reads `targeted-tests` (cases identified), `partial-tests` (some
evidence with a stated gap) or `no-targeted-test` — none of which mean pass or fail.

`disposition`, `note` and `relatedRequirements` are the only fields edited by hand:

| Disposition | Meaning |
| --- | --- |
| `pending` | Passage not reviewed. |
| `mapped` | All identified in-scope information is linked to requirements; this does not mean tests pass or exist. |
| `needs-requirement` | A requirement needs adding, splitting or correcting. |
| `needs-review` | Source meaning, scope or a defensible expected-answer test needs judgment. |
| `duplicate` | Adds nothing beyond the linked requirements; identify them. |
| `context-only` | Heading or background with no information capability. |
| `out-of-scope` | Entire passage concerns excluded matters; explain why. |

Save annotations **before** changing requirements, cases or the assertion input, because
rebuilding refuses unsaved ones:

```sh
.venv/bin/python coverage/methodology/scripts/assess.py save-source-review
npm run methodology:build
```

## Recording an acceptance

An entry under `requirements` in [review.json](inputs/review.json), or the top-level
`sourceAudit`, with four fields: the `fingerprint` currently in
[review-queue.json](generated/review-queue.json) for that ID, `reviewer`, `date` and `rationale`.
A blank rationale never counts as acceptance, and a fingerprint that has since moved is treated
as unsigned. Editing `review.json` requires a rebuild, because its hash is recorded in the
provenance.

Every fingerprint mixes in a digest of the whole hashed input set — sources, scripts, queries,
fixtures, the authored inputs and the ontology — so a change to that set re-opens every
acceptance, including requirements the change did not touch. That is deliberate: changed evidence
invalidates review. Batch input changes rather than interleaving them with signing.

**One exception, by design: a release version bump.** `owl:versionInfo` and `owl:versionIRI`
values are blanked before an ontology module is hashed, so stamping a new release leaves the
digest untouched and recorded decisions stand. Only the stamped value is ignored; every other
byte of those files still counts, and the VCF specification version a registry describes is a
different property and is not exempt. A regression test in
[test_assessment.py](tests/test_assessment.py) holds both halves of that behaviour in place.

## Reproducing this state

```sh
npm run methodology:build
npm run methodology:check
npm run methodology:test
npm run methodology:check -- --require-reviewed
```

All four succeed. The wider repository checks (`validate:rdf`, `validate:examples`,
`validate:profiles`, `validate:shacl`, `validate:regressions`) also pass.
