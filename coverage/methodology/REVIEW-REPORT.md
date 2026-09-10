# Coverage assessment: VCF-expert reviewer report

Reviewer: Claude Opus 5, acting as a VCF-format expert reviewer
(the acceptance entries in [inputs/review.json](inputs/review.json) name this pass and
still need a human countersignature — see [Status](#status)).
Review date: 10 September 2026.
Reviewed artefact: `coverage/methodology/` at the pinned sources in
[sources.lock.json](sources.lock.json) (all five SHA-256 pins re-verified against the
files in [sources/](sources/)).

This report answers the [reviewer checklist](REVIEW-CHECKLIST.md). Section numbers below
match the checklist's.

---

## Status

| Checklist section | Outcome |
| --- | --- |
| 1. Agree the claim | Done — claim accepted with one scope correction (attribute ordering). |
| 2. Resolve flagged source interpretations | **All 21 items resolved**; `needsReviewSections` is now 0. |
| 3. Source inventory completeness | Done for all 344 sections and all 1134 assertions; one disclosed limitation in the reserved-declaration comparison. |
| 4. Requirements, tests and results | Done for all 94 requirements, 189 cases, 66 distinct expected-answer sets and all 756 query results. |
| 5. Close the review | Decisions implemented, rebuilt, and acceptance recorded. `methodology:build`, `check`, `test` and `check --require-reviewed` all pass. |

The measured percentages are **unchanged** by this review. That is deliberate: every
correction made here is interpretive, documentary or defect-fixing. Where a change would
have raised a coverage percentage — for example narrowing R35's version list, which has no
cases in any version — the change was *not* made, and the reasoning was recorded in the
requirement instead. A reviewer should not improve a score by shrinking a denominator.

---

## 1. What the assessment should claim

The two axes, the exclusions and the equal weighting of requirements are appropriate, and
the intended claim — **demonstrated coverage of registered information requirements** — is
the one the evidence supports. Complete specification coverage is not supported and the
README says so.

Three qualifications were added to the README as a result of this review:

1. **Structured-header attribute order is not information.** VCF 4.4 and 4.5 state that
   implementations "must not rely on the order of the fields within structured lines and are
   not required to preserve field ordering", and present the recommended
   ID/Number/Type/Description sequence explicitly as a human-readability aid; 4.1–4.3 nowhere
   give the order meaning. R34's question and interpretation were corrected to drop ordering
   from the scored capability and keep it as an unscored round-trip fidelity extension. Its
   registered cases already demonstrate the scored part (identity, decoded value, escaping),
   so no score changes. This is distinct from R02, which is the order of meta-information
   *lines* and is legitimately scored.

2. **The condensed structure column measures a profile choice, not the vocabulary.** See
   [§4.1](#41-the-condensed-structure-failures-r18r21-r27r30-r60).

3. **"333/333 declarations match" covers a version-biased subset.** See
   [§3.2](#32-reserved-declarations-333-rows).

---

## 2. The 21 flagged source interpretations

Every flagged section now carries the decision verbatim in its `note`, both in
[generated/source-audit.json](generated/source-audit.json) and in
`inputs/review.json.sourceSections`; the questions were then cleared from
[inputs/source-assertions.json](inputs/source-assertions.json) and the affected assertion
statements and test gaps updated. Summary of each decision:

### 2.1 Legacy GLE — `4.1:193-222`, `4.2:210-239` → accepted unassessed limitation

The reserved example value `0:-75.22,1:-223.42,0/0:-323.03,1/0:-99.29,1/1:-802.53` uses `:`
as its internal separator, but `:` is the sample sub-field separator that delimits the FORMAT
key list. A sample column carrying that value cannot be split against its FORMAT keys, and
the specification supplies no escaping rule and no complete sample-column example — the
printed `GLE=` prefix is INFO syntax, a further slip. VCF 4.3 removes the key as "unused and
ill-defined", which confirms the defect rather than leaving it open.

**Decision:** no valid 4.1/4.2 serialization, therefore no oracle. R80 stays *unassessed by
decision*, not by omission. GLE remains in scope only as an opaque declared `String` value on
the preservation axis. This is a specification defect, not vocabulary incapability.

### 2.2 Deletion length — `4.1:468-523` → 205 bp

`POS=321682`, `END=321887`, `SVLEN=-205` all agree on 205 deleted bases (321683–321887, with
`REF=T` at POS as the padding base). The prose "105 bp" is a typo, and the pinned VCF 4.2
(line 534) and 4.3 (line 874) both print "205 bp". The example is usable as a POS/END/SVLEN
oracle with the corrected figure.

### 2.3 Complete assembly insertion `C<ctg1>` — `4.1:586-638`, `4.2:603-655`, `4.3:1000-1052`

The shorthand row `13 321682 INS0 T C<ctg1>` copies its POS and REF from the unrelated chr2
breakend row `2 321682 bnd_V T`. The flanking pair immediately above places the insertion
between 13:123456 (`REF=C`) and 13:123457 (`REF=A`).

**Decision:** the consistent record is **`13 123456 INS0 C C<ctg1> 6 PASS SVTYPE=INS`**.
VCF 4.4 independently corrects the same row to POS=123456 with REF=C, which settles it. Any
oracle must be justified from the flanking BND pair, and the corrected row labelled as a
reviewer correction rather than spec-verbatim.

### 2.4 Legacy haplotype bundles, BDP/BCN — `4.1:911-954`, `4.2:928-971`, `4.3:1376-1427`

BDP and BCN occur **exactly once** in each of 4.1/4.2/4.3, in one prose sentence. Neither has
an `##INFO`/`##FORMAT` declaration, a Number, a Type, a reserved-key table entry, or any
complete VCF record. The bundle table is an abstract visualisation whose haplotype cells
(`1>11`, `2,3,4>12,13,14`, `5>5`) have no VCF grammar, and multiple bundles per breakend per
sample have no defined sample-column encoding. VCF 4.4 deprecates bundles outright.

**Decision:** accepted unassessed limitation; R94 stays unassessed. The quantities the passage
describes *are* declared under other names — DP and CN (segment depth and copy number),
**DPADJ and CNADJ** (the table's "Bundle Depth" and "Bundle Copy Number"), HQ, and HAP/AHAP —
and a targeted **R79 test is requested** using those declared keys and the worked example at
`4.1:836-839` / `852-855`.

> **Additional defect found here:** DPADJ, CNADJ and CICNADJ are declared as `##INFO=` lines
> in 4.1–4.3 yet used as FORMAT keys in those very examples (`GT:DPADJ`, `GT:CNADJ`). Assess
> the FORMAT usage the examples actually show.

### 2.5 Quality probabilities — `4.3:586-600`, `4.4:651-665`, `4.5:824-840` → error probability

The Q-suffix sentence is internally inconsistent: it calls the quantity a
"log-complementary … posterior probability" but prints `−10 log₁₀ Pr(Data|Model)`, which is
neither complementary nor posterior. The normative per-key definitions in the same document
govern — GQ is "−10log₁₀ p(genotype call is wrong, conditioned on the site's being variant)"
and CNQ is "−10log₁₀ p(copy number genotype call is wrong)".

**Decision:** a Q-suffixed value is `−10 log₁₀ (1 − Pr(Model|Data))`, the phred-scaled
probability that the reported call is wrong. **Assessment impact: none** — the vocabulary
carries this meaning through the reserved definition and the declaration `Description`, and no
registered expected answer depends on the numeric semantics.

### 2.6 CNL ordering — `4.3:672-691`, `4.4:981-1002`, `4.5:1142-1163`

CNL "specifies a list of log₁₀ likelihoods for each potential copy number, starting from
zero", but is declared `Number=G`. `G` is a function of allele count and ploidy; a
copy-number-indexed list has length `max(CN)+1`, which is not derivable from REF/ALT/GT.

**Decision:** the prose governs the meaning — the *i*-th 0-based value is log₁₀ L(CN = *i*) —
and cardinality is **data-determined**, taken from the values present, not from `Number=G`.
CNP inherits the same reading. `Number=G` is a specification defect carried over from GL and
unchanged through 4.5. The reserved-declaration check must keep comparing `Number=G`
literally; the README now says that literal agreement is not semantic agreement.

### 2.7 Older gVCF `GT:DP:GQ:P` — `4.3:1428-1451`, `4.4:1686-1711` → `PL`

Four independent confirmations, any one of which would suffice:

* no reserved FORMAT key named `P` exists in any VCF version;
* the value carries six comma-separated items, exactly `G` for the three alleles G, C and
  `<*>` at ploidy two;
* the items are integers, matching PL (Integer) rather than GL or GP (Float);
* `GQ=52` equals the second-smallest value in `0,52,95,66,95,97`, which is precisely how GQ
  relates to PL.

Every sibling row in the same table uses PL, and the row correctly omits MIN_DP because it is a
variant row rather than a reference block. Usable as a fixture after the correction.

### 2.8 Header attribute order — `4.4:105-142`, `4.5:103-140`

See [§1](#1-what-the-assessment-should-claim). Order removed from the scored requirement,
retained as an unscored fidelity extension; R34's question, interpretation and testPlan updated.

### 2.9 PSL / PSO — `4.4:445-639`, `4.5:497-812`

**PSL: excluded as an oracle.** The table has three separate defects.

| Row | Defect |
| --- | --- |
| `chr20 10 . A T,G … GT=\|1/2\|3` | allele index 3, but ALT lists only two alleles |
| `chr20 15 . G C … GT=1\|2` | allele index 2, but ALT lists one; and with the leading indicator omitted and no `/` present, VCF 4.4/4.5 make the first indicator implicitly `\|` (phased), contradicting `PSL=.,chr20*10*1` |
| rows 2 vs 3 | ploidy 3 vs 2 for the same sample on the same CHROM |

A corrected, internally consistent equivalent preserving the illustrative content:

```
chr19  5  . T G   . PASS DP=100 GT:PSL  |0/1:chr19*5*1,.                (unchanged)
chr20 10  . A T,G . PASS DP=100 GT:PSL  |1/2|0:chr20*10*1,.,chr19*5*1
chr20 15  . G C   . PASS DP=100 GT:PSL  /0/0|1:.,.,chr20*10*1
```

Any test built on it must be labelled reviewer-authored.

**PSO: the example is consistent and supplies the oracle.** Per sample-allele:

| Record | GT slot | PSL | PSO |
| --- | ---: | --- | ---: |
| chr1:10 `<DUP>` | 3 | `chr1*10*3` | 3 |
| chr1:20 REF A | 3 | `chr1*10*1` | 4 |
| chr1:20 ALT G | 4 | `chr1*10*3` | 1 |
| chr1:30 REF G | 3 | `chr1*10*1` | 2 |
| chr1:30 ALT T | 4 | `chr1*10*3` | 5 |

Ordinals 1–5 occur exactly once each and give one total traversal order of the derivative
chromosome: ALT G at chr1:20 (1) → REF at chr1:30 (2) → the duplication junction (3) → REF at
chr1:20 (4) → ALT T at chr1:30 (5). That is exactly the stated reading, "the first SNV occurs
on the first copy of the duplicated region, and second SNV on the second copy". The rise from
three to four allele values inside the duplicated interval is intended, not an error. An R82
test is requested on this basis.

### 2.10 Repeat field names — `4.4:666-980`, `4.5:841-1141` → RS→RUS, RL→RUL, RC→RUC

No key named RC, RS or RL is declared anywhere in 4.4 or 4.5; the declared repeat keys are RN,
RUS, RUL, RUC, RB, RUB, CIRUC and CIRB. There are exactly three affected sentences per version
(4.4 lines 973, 1759, 1827; 4.5 lines 1134, 1928, 1995). The overview's list "RN, RS, RL, RB,
RC and RUL" both mis-spells three names and repeats RUL; corrected it reads **"RN, RUS, RUL,
RUC, RB and RUB"**.

The same correction settles the RUB nesting question. The sentence "a list for each **RC**
entry, the length of which is determined by the corresponding integer RUC value" means:

* **RUB is partitioned by RUC** — one value per repeat *unit*;
* **RUS, RUL, RUC and RB are partitioned by RN** — one value per repeat *sequence*.

Two different flattening rules in the same record. The specification never states this
contrast explicitly.

### 2.11 Structural-variant examples — `4.4:1181-1233`, `4.5:1342-1393`

With `chrA = ATGCGAAAAAAATGT`:

* **delbp2.** `delbp1` at chrA:2 (`REF=T`, correct) has `ALT=T[chrA:5[`, so its mate is at
  chrA:5, where the reference base is G. The printed `chrA 2 delbp2 A ]chrA:2]A` has the wrong
  POS (2, duplicating delbp1), the wrong REF (A; chrA:2 is T and chrA:5 is G) and a
  self-referential mate coordinate. Correct reciprocal:
  **`chrA 5 delbp2 G ]chrA:2]G . . MATEID=delbp1;EVENT=DEL_split_bp_cn GT 0/1`**, matching the
  copy-number row `chrA 2 . T <DEL> SVLEN=2;SVCLAIM=D`.
* **DUP.** `chrA 5 . G <DUP> . . SVLEN=3;CIPOS=0,5;EVENT=homology_dup` omits SVCLAIM, which
  4.4/4.5 make mandatory for DEL/DUP ("SVCLAIM must be specified and can be D, J, or DJ"). The
  example does not determine the value — as the duplication rendering of the sequence-resolved
  `chrA 5 . G GAAA` it asserts both abundance and adjacency (DJ), but a pure abundance claim
  (D) is also readable. **Excluded as an SVCLAIM oracle.**
* **Erratum found in this review, not previously flagged:** `chrA 14 . T <INS> …` gives
  `REF=T` at chrA:14, but the stated sequence has **G** at 14 (T is at 13 and 15) — and the
  very next row correctly writes `chrA 14 . G .CCCCCCG`. Present in both 4.4 and 4.5.

### 2.12 Partial / circular insertions — `4.4:1308-1360`, `4.5:1468-1520`

MATEID in this subsection cannot serve as an oracle for reciprocal-mate reconstruction:

* the partial-insertion table gives `bnd_U → bnd_U` and `bnd_V → bnd_V`, both self-references;
* the circular table repeats those and gives `bnd_Y → bnd_C`, an identifier that appears
  nowhere in the specification;
* more fundamentally, a MATEID names the breakend at the other end of the **same novel
  adjacency**. `bnd_U`'s adjacency ends on `<ctg1>` (at 1, 7 or 229) and `bnd_V`'s ends on
  `<ctg1>` (at 329, 214 or 45), and no records exist for those contig-side breakends. So no
  correct MATEID for `bnd_U` or `bnd_V` exists anywhere in the section — **including the first
  table**, whose printed `MATEID=bnd_V`/`bnd_U` are wrong for the same reason. `EVENT` is the
  correct grouping mechanism here, and the circular table already uses it (`EVENT=INS0`).

The one determinable correction is `bnd_Y`'s: at `<ctg1>:329` with `ALT=T[<ctg1>:1[` its mate
is the breakend at `<ctg1>:1`, i.e. **`MATEID=bnd_X`** (`bnd_X`'s printed `MATEID=bnd_Y` is
already correct). Test reciprocal mates (R32) on the six-breakend Figure 1 example instead —
the existing `breakends-v4.5.vcf` fixture already does this correctly.

### 2.13 Sample mixtures — `4.4:1571-1615`, `4.5:1731-1775` → version-scoped

* **4.1/4.2:** `##SAMPLE=<ID=…,Genomes=…,Mixture=…,Description=…>` is the *normative* SAMPLE
  grammar (4.1 line 129, 4.2 line 146). In scope, with the semicolon-separated lists
  positionally aligned (Germline↔.3, Tumor↔.7).
* **4.3–4.5:** the normative SAMPLE definition is the META-driven form
  (Assay/Ethnicity/Disease/Tissue/Description/DOI) and the Genomes/Mixture example is
  *retained but no longer normatively defined*. It stays syntactically legal because these
  versions permit arbitrary additional attributes on structured lines. Assess it there as
  **generic structured-attribute retention** (R34/R59), not as a version-specific capability.
  R35's interpretation records this; its version list was deliberately left unchanged so the
  clarification cannot raise a percentage.
* **Accepted limitation:** Genomes and Mixture use unquoted `;` as list separators while the
  parallel Description list is a single quoted string containing `;`, and no rule makes the
  quoted Description a list — so positional pairing of Description entries is not recoverable
  by grammar alone.

> **Erratum found in this review, present in all five versions:** in these breakend tables,
> `bnd_W` at 2:321681 has `ALT=G]2:421681]` with `MATEID=bnd_U`, and `bnd_V` at 2:321682 has
> `ALT=[2:421682[T` with `MATEID=bnd_X`, but `bnd_U` and `bnd_X` are on **CHROM 13**
> (13:421681 and 13:421682). The ALT coordinates should read `13:421681` and `13:421682`.
> Excluded as a mate-coordinate oracle.

### 2.14 Tandem repeats — `4.4:1748-1879`, `4.5:1917-2047`

1. Obsolete key names: as [§2.10](#210-repeat-field-names--44666-980-45841-1141--rsrus-rlrul-rcruc).
2. `CAGCAGCAGTTGTTG` is **`(CAG)₃(TTG)₂`**, not `(CAG)₄(TTG)₂` — it contains three CAG units
   and is fifteen bases. Corrected figure values: `RN=2,1`; `RUS=CAG,TTG,CA`; `RUL=3,3,2`;
   `RUC=3,2,3`; `RB=9,6,6`, with the second allele `CACACA = (CA)₃`.
3. RUL/RUB nesting: RUB by RUC, the rest by RN.
4. **The main worked example is internally consistent and usable as an oracle**, verified
   arithmetically here: reference `(CAG)₁₀` at 101–130 (30 bases, `SVLEN=30`, POS=100 padding);
   allele 1 `(CAG)₃₀` = 90 bases with `RN=1`, `RB=90`, INFO `CN=90/30=3`; allele 2
   `(CAG)₅(CA)(CAG)₄` = 29 bases with `RN=3`, `RUS=CAG,CA,CAG`, `RB=15,2,12`, INFO
   `CN=29/30`; the flattened `RUS=CAG,CAG,CA,CAG` and `RB=90,15,2,12` exactly as printed;
   FORMAT `CN=(90+29)/30`. The phased non-symbolic rows also check out: `chr1 117 AG A`
   deletes the G of the sixth CAG unit (116–118) on haplotype 2 (`GT=0|1`), and
   `chr1 130 G G+20×CAG` adds twenty units on haplotype 1 (`GT=1|0`), matching `GT=1|2` on the
   summary record. Printed CN values are truncated rather than rounded (0.9666 and 3.9666).
   The CIRUC example is likewise consistent (65×3/30 = 6.5).
5. **Erratum found in this review:** the RUB example
   `chr1 1000000 . T <CNV:TR> . . SVLEN=20000;CN=1.25;RUL=10000;RUC=5;RUB=10000,10500,11000,11500,12000`
   is arithmetically inconsistent — CN must be sample allelic length over reference allelic
   length, and Σ RUB = 55000 gives 2.75 while RUL×RUC = 50000 gives 2.5, neither of which is
   1.25. Excluded as a CN oracle; still usable for RUB cardinality (five values = RUC).
6. **Erratum found in this review, 4.4 only:** the same record carries `END=20000` at
   `POS=1000000`, i.e. END below POS. It should read 1020000. Removed in 4.5 with the
   deprecation of INFO END.

### 2.15 `Number=P` erratum — `4.4:2558-2563`, `4.5:2740-2745`

The main text governs: **P is a Number, not a Type.** The FORMAT section lists P among the
additional Number possibilities, the reserved genotype table gives PSL/PSO/PSQ `Number=P` with
Types String/Integer/Integer, and the enumerated FORMAT Types are only Integer, Float,
Character and String. The VCF 4.5 changelog itself writes "Added **Number=P** support",
corroborating the correction. The erratum should read "Number=P added to the FORMAT Number
list".

### 2.16 Mandatory FORMAT attributes — `4.4:2564-2591`, `4.5:2746-2773`

The main text governs: ID, Number, Type and Description are required for **both** `##INFO` and
`##FORMAT` lines — "FORMAT meta-information lines are structured lines with required fields
ID, Number, Type, and Description" is as explicit as the INFO sentence. The changelog entry
"Number, Type and Description required only for INFO meta-information lines" omits FORMAT and
is a drafting error. What actually changed relative to 4.3 is that they are *not* required for
the other spec-defined structured lines (FILTER, ALT, contig, META, SAMPLE, PEDIGREE) nor for
undefined ones, where only ID is required. R03 and R52 are correctly scoped; no change.

### 2.17 Base modifications — `4.5:184-248`, `4.5:497-812`

**Capitalisation: `MXaoN`, `DPMXaoN`, `ADMXaoN` (capital X) are normative.** The reserved
genotype-key table is the declaration table and uses the capital form; the alias pattern is
`M` + modification abbreviation + base letter, and "Xao" is the standard abbreviation for
xanthosine (as used for the SAM/BAM `MM` tag modification codes), matching `M5mC`, `M8oxoG`,
`M6mA`. The four prose occurrences of `MxaoN`/`DPMxaoN`/`ADMxaoN` (lines 218, 724, 734, 740)
are typos. FORMAT keys are case-sensitive, so this is material. The extraction in
[declarations.json](generated/declarations.json) already uses the table form; that choice is
confirmed.

**The examples need no correction and are usable directly as an oracle.** Every value count
was manually enumerated in this review and matches the prose:

| Record | Reasoning | Values |
| --- | --- | ---: |
| `chr 10 C A GT:M5mC 0/1:0.95` | C → 1; A → 0 (A is T on the reverse strand) | 1 |
| `chr 20 C CTAG GT:M5mC 0/1:0,0.5,0.7` | C → 1; CTAG → 2 (forward C at base 1, reverse-strand C opposite the G at base 4) | 3 |
| `chr 30 C . GT:M5mC:M5hmC 0\|0:0.9,0:0,0.1` | two phased C copies | 2 per field |
| `chr 40 C A,T,G,ACG GT:M5mC /3\|1/0\|4\|0/0/3/1:0.25,0.1,0.5,0.6,.` | octoploid GT with allele values 0,1,3,4, all in range; in GT order with unphased aggregation at first occurrence: G→1, A→0, C→1, ACG→2, phased C→1, then three repeats contributing none | 5 |

### 2.18 Local vs global genotypes, `GT=2/4` vs `GT=2/2` — `4.5:497-812` → **`2/2`**

GT is `Number=1, Type=String` and is **not** a local-allele field, so it carries global allele
indices in both rows — confirmed by row 2 of the same table, where both rows print `0/3`.
With `LAA=2,4` the local alleles are `[G(REF), C, <*>]`; `LPL=90,80,0,100,110,120` is minimal
(0) at local genotype 1/1 = C/C, and the global `PL` list is minimal (0) at index 5 = genotype
2/2 = C/C. Every other value maps consistently (local 00/01/02/12/22 → global 00/02/04/24/44 =
90/80/100/110/120) and `LAD=20,30,10` matches `AD=20,.,30,.,10`. Rows 2–4 were verified the
same way and are correct as printed.

### 2.19 VCF 4.5 gVCF separators and LEN — `4.5:1846-1880`

* **Separators:** the `;` before each LEN value must be `:`. Semicolon is the INFO separator;
  sample sub-fields are colon-delimited. The first row reads `0/0:25:60:23:0,60,900:14`.
* **LEN is the inclusive block length, so `END = POS + LEN − 1`.** The reserved definition is
  "length of the `<*>` reference block for this sample" and END is "the end position …
  calculated from FORMAT LEN". The row `POS=4390, END=4390, LEN=1` is decisive — `END − POS`
  would give a block length of zero — and `POS=4370, END=4383, LEN=14` confirms it. Corrected
  LEN values: 4370→**14** (as printed), 4384–4388→**5** (printed 4), 4390→**1** (as printed),
  4391–4395→**5** (printed 4), 4397–4416→**20** (printed 19).
* **Erratum found in this review:** the row
  `1 4396 . G C,<*> … GT:DP:GQ:MIN_DP:PL:LEN 0/0:24:52:0,52,95,66,95,97` is a variant row with
  no reference block, so MIN_DP and LEN do not apply, and its four supplied sub-fields make
  MIN_DP absorb the PL vector. The uniform FORMAT string was applied to every row of the table
  without adjusting this one. Its corrected FORMAT is `GT:DP:GQ:PL`.

The registered `gvcf-v4.5.vcf` fixture and `queries/r30-decode.rq` already implement
`END = POS + LEN − 1` and are **confirmed correct** by this decision.

### 2.20 VCF 4.5 changelog — `4.5:2726-2739`

* **`Number=P` was introduced in VCF 4.4, not 4.5.** The pinned 4.4 text defines P in the
  FORMAT Number list, gives PSL/PSO `Number=P` in the reserved table, and records it in the 4.4
  errata. The 4.5 entry is inaccurate as a 4.4→4.5 delta; what 4.5 adds is the new `M` Number
  and the local-allele Numbers alongside it. R82 already lists both 4.4 and 4.5, so no
  version-scope change was needed.
* **Modification key syntax.** The changelog's "FORMAT keys of the form `M[0-9]+`" is
  incomplete: the main text reserves **`M[0-9]+[ACGTUN]`**, and equally
  `DPM[0-9]+[ACGTUN]` and `ADM[0-9]+[ACGTUN]`. The trailing base letter is required and defines
  the base the modification occurs on, with U synonymous with T. `declarations.json` already
  records all three patterns.

---

## 3. Source inventory completeness

### 3.1 What was verified, and how

| Check | Result |
| --- | --- |
| Pinned source SHA-256 pins | all 5 re-verified against `sources/` |
| Section partition | 344 sections cover **every line** of all five sources with **no gaps and no overlaps** (4.1 62, 4.2 62, 4.3 71, 4.4 74, 4.5 75) |
| Assertion bounds | all 1134 assertions lie inside their section |
| Assertion→requirement links | 0 assertions with no link; all 94 requirements referenced by at least one assertion |
| Exclusions | 98 `out-of-scope` = 90 BCF + 5 preamble + 3 BCF changelog subsections; 20 `context-only` = single-line headings. **No VCF-zone content is excluded.** |
| Reserved-key assertions | all **396** verified mechanically to reproduce the key, Number, Type and Description of their source passage (333 with Number/Type, of which 161 are reserved-table rows) |
| Changelog assertions | all **119** verified to be verbatim source bullets |
| Authored VCF-zone assertions | 619 instances reduce to **150 distinct statements**, all read individually against their sections |

The exclusion policy and the assertion inventory are sound. The `mapped` sections' assertion
statements are accurate and appropriately version-aware — for example, R69's interpretation
correctly records that GP changes from phred-scaled to linear in 4.3 and that PP is phred from
4.3, and R44's correctly separates pre-4.4 segment CN from 4.4+ allele-specific CN.

### 3.2 Reserved declarations (333 rows)

The 333 rows are all `exact`, and each was verified to be a faithful reproduction. The
**extraction omission** the checklist asks about is real and is now disclosed in the README:

| Version | Rows compared |
| --- | ---: |
| 4.1 | 31 (25 INFO, 6 FORMAT) |
| 4.2 | 31 (25 INFO, 6 FORMAT) |
| 4.3 | 69 (46 INFO, 23 FORMAT) |
| 4.4 | 79 (52 INFO, 27 FORMAT) |
| 4.5 | 123 (52 INFO, 71 FORMAT) |

VCF 4.1 and 4.2 define **29 further reserved keys each** in prose bullets rather than in
`##INFO=`/`##FORMAT=` blocks:

* INFO (16): `AA AC AF AN BQ CIGAR DB H2 H3 MQ MQ0 NS SB SOMATIC VALIDATED 1000G`
* FORMAT (13): `GT DP FT GL GLE GP GQ HQ PL PQ PS EC MQ`

Those 58 rows **are** inventoried as source assertions (that is why there are 396
reserved-key assertions against 333 declaration rows), but they cannot enter a Number/Type
comparison, because the 4.1/4.2 prose supplies no Number at all and, for INFO, no Type either.
The omission is therefore *justified*, but "333/333 explicit source rows match" reads as
complete agreement and needed the qualification. Four rows are duplicate declarations of one
key in one source (4.3 DP and END, 4.4/4.5 END); the duplicates agree, so the distinct-key
count is 329.

**Cosmetic defect, left unfixed:** the section titles for "Alternative allele field format" in
4.4/4.5 render as `Alternative allele field format \labelaltfield`, because the title regex in
`scripts/source.py` does not strip a trailing `\label{…}` on the same line. Fixing it changes
the provenance digest and hence every fingerprint, so it is reported rather than applied.

---

## 4. Requirements, tests and results

All 94 requirements' questions, interpretations, testPlans, version lists and source anchors
were read against the specification; all 189 cases reduce to **66 distinct (query, expected)
pairs**, every one of which was read against its fixture and the pinned source; all 756 query
results were inspected.

**Query controls are sound.** Every one of the 727 passing queries rejects both an empty graph
and at least one applicable predicate-deletion control — 0 exceptions. The 60 single-cell
expected answers belong to R01 (fileformat), R15 (INFO flag) and R58 (pedigree DB URL), all of
which are genuinely single-value questions.

**The preservation/structure distinction is honestly implemented.** The condensed decode
queries (`r18-decode.rq`, `sample-filter-decode.rq`, …) split the tab-separated
`vcfc:encodedValues` literal by the sample's RDF-provided `sampleIndex`. Only the value vector
is parsed; the sample-to-column correspondence comes from the graph. That is a fair reading of
"explicitly decoding VCF text literals".

### 4.1 The condensed structure failures (R18–R21, R27–R30, R60)

All 29 failing witnesses are condensed-profile **structure** queries over per-sample FORMAT
data, and every one of them **passes on the structure axis in the expanded profile**.

The cause is by construction. The condensed profile emits, per record and FORMAT key, a single
`vcfc:FormatValueVector` carrying `vcfc:encodedValues "12\t."` plus
`vcfc:appliesToSampleSet`, and no per-sample node at all (`hasSampleCall` appears 6 times in
`basic-v4.5-expanded.nt` and 0 times in `basic-v4.5-condensed.nt`). Neither the vector nor the
sample set exposes per-index items, so there is no RDF path from a sample to its own value; the
structure axis forbids parsing the compound literal.

**Verdict: neither a vocabulary limitation nor an assessment error.** It is a correctly
reported consequence of a deliberate profile design that trades structural accessibility of
per-sample values for compactness. The assessment is right to record the failures; the README
now states that this column measures a profile choice and must not be read as "the vocabulary
cannot do this". A preservation pass does not and should not resolve it.

### 4.2 Defects found in the assessment's own inputs, and what was done

| Finding | Action |
| --- | --- |
| **R47 and R48 anchors are swapped** in 4.1/4.2, and R47's 4.3–4.5 anchors point at "Fixed fields" instead of "Data types". R47 (numeric types and precision) is asserted in the Data types sections; R48 ("arbitrary keys are permitted", "additional FORMAT keys can be defined") is asserted in Fixed fields and Genotype fields. | **Fixed.** R47 → 4.1:65-73, 4.2:65-82, 4.3:99-104, 4.4:99-104, 4.5:97-102. R48 → 4.1:158-192, 4.2:175-209, 4.3:321-426, 4.4:335-444, 4.5:384-496. Anchor hashes recomputed. |
| **`repeats-v4.5.vcf` CN values were internally inconsistent.** With `SVLEN=30`, `RUC=10`, `RB=30` the ALT allele is 30 bases, so allele-specific INFO CN is 30/30 = 1 and, with `GT=0/1`, the overall FORMAT CN is 60/30 = 2 — not the `CN=2` / `CN=3` printed. | **Fixed** to `CN=1` / `0/1:2`. No expected answer changes (R31 queries only RUS and RUC); scores unchanged. |
| **R27's local-allele case is a degenerate oracle.** The fixture uses `LAA=1,2` on a two-ALT record, so the local→global mapping is the identity and cannot distinguish a correct implementation from one that ignores LAA. The recorded test gap wrongly described the fixture as `LAA=2,4`. | **Test gap corrected**, and a non-identity fixture requested (e.g. `ALT=A,C,T,<*>` with `LAA=2,4`, as in the specification's own equivalence table). Fixture not changed, because it is shared with R28/R29 and changing it would move expected answers. |
| **Assertion `4.5:497-812:A16` was marked `targeted-tests` with an empty gap**, but its case checks the modification fraction and the *total* detecting depth (DPM) only; the modified-read depth (ADM) is in the fixture and never queried. | **Test gap added**; the assertion is now correctly `partial-tests` (146 targeted / 135 partial). |
| **`features-v4.5.vcf` uses `CILEN=15,25` as absolute bounds around `SVLEN=20`.** The CILEN paragraph says "lower and upper bounds", omitting the "relative to" that CIPOS, CIEND, CIRUC and CIRB all carry — but the specification's only CILEN example is `SVLEN=100;CILEN=-50,50`, which is only interpretable as relative offsets. | **Reported, not changed.** No registered case queries CILEN, so nothing is currently wrong; but if one is added, the relative reading should govern and the fixture should read `CILEN=-5,5`. |
| **`boundaries-v4.5.vcf` uses `<*>` at chr1:80 without an `##ALT=<ID=*>` line.** Declaring it is recommended, not required, so this is legal. | **Reported.** Worth adding for the R53/R54 declaration-to-allele link. |

### 4.3 Tests requested vs limitations accepted

Recorded per assertion in `testGap`, and per requirement in `interpretation`:

**Accepted unassessed limitations** (no source-derived oracle exists): R80 (GLE — the value
contains the sample sub-field separator and 4.3 removes the key), R94 (BDP/BCN — undeclared,
unserialized, deprecated in 4.4), and the positional pairing of SAMPLE `Description` entries
under R35.

**Tests requested** (an oracle exists and was specified): R79 (DPADJ/CNADJ/CICNADJ from the
4.1–4.3 worked examples), R82 (the PSO per-allele traversal oracle in §2.9), R31/R46 (RN
partitioning of the flattened repeat lists), R84/R85 (the four Number=M examples, verified
usable as printed), R89 (the tandem-repeat allelic-length ratios, verified arithmetically),
R45 (the gVCF tables, usable after the `P`→`PL` and LEN corrections), R92 (assembly-contig
insertions from the flanking BND pairs rather than the printed MATEIDs), R27 (a non-identity
LAA fixture) and R29 (a case returning DPM and ADM separately).

### 4.4 Are the percentages too coarse for the claim?

Yes, if read alone — and the README already forbids reading them alone. Two specific reasons a
reader must keep in view:

1. **The denominators are dominated by untested requirements** (47 of 91 in 4.5). "44/91
   demonstrated" is not "48% of VCF 4.5 is covered"; it is "48% of the registered requirements
   have at least one passing witness in this profile and axis", with the remainder explicitly
   unassessed rather than failed.
2. **Requirement granularity is uneven.** R67 and R68 each stand for *every* reserved INFO or
   FORMAT key's meaning and value scope — 396 reserved-key assertions between them, none with a
   targeted case — while R01 stands for a single header value. Equal weighting is a defensible
   operational choice but makes the percentage a count of heterogeneous items, not a measure of
   specification surface.

The recommendation for the paper is to report the numerator/denominator pair with the
unassessed count beside it, never a bare percentage, and to cite the assertion test inventory
(146 targeted / 135 partial / 853 without a targeted case) as the workload measure it is.

---

## 5. Closing the review

Decisions were saved before the assertion input was edited, as the README requires, then
applied and rebuilt:

```sh
.venv/bin/python coverage/methodology/scripts/assess.py save-source-review
npm run methodology:build
npm run methodology:check
npm run methodology:test
npm run methodology:check -- --require-reviewed
```

All four commands succeed. `needsReviewSections` is 0, `reviewIssue` is empty for all 344
sections, and `pendingReviews` is 0.

**Human countersignature still required.** The acceptance entries in
[inputs/review.json](inputs/review.json) carry a per-requirement rationale describing what was
actually checked for that requirement, but the `reviewer` field names this agent pass. Replace
it with the accepting person's name before publication. `inputs/review.json` is excluded from
the provenance hash set in `assess.py`, so editing the name invalidates nothing and requires
no rebuild.

### Recommended follow-up, in priority order

1. Write the requested tests in §4.3, starting with R79, R82, R31/R46 and R29 — each has a
   specified oracle and needs only a fixture and a query.
2. Replace the R27 fixture's `LAA=1,2` with a non-identity local set.
3. Report the errata found here upstream to `samtools/hts-specs`: the delbp2 row and the `<INS>`
   REF base (§2.11), the self-referential and undefined MATEIDs (§2.12), the cross-chromosome
   breakend ALT coordinates (§2.13), the RUB example's CN and 4.4's `END=20000` (§2.14), the
   gVCF separators, LEN values and the MIN_DP row (§2.19), and the `MxaoN` spelling (§2.17).
4. Fix the `\label` title glitch in `scripts/source.py` in the same change as any other
   provenance-invalidating edit, so fingerprints are regenerated only once.
