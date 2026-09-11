#!/usr/bin/env node
/**
 * Generate a full reserved-key registry for one VCF specification version.
 *
 * The VCF specification intentionally uses two source layouts: its general
 * INFO/FORMAT keys are longtables, while its SV keys are concrete ##INFO and
 * ##FORMAT declarations.  This generator reads both layouts and fails closed
 * if their expected counts change, so a VCF 4.6 update cannot silently alter
 * the 4.5 registry.
 *
 * Which versions exist, where their sources live, how many rows each is
 * expected to yield and where the output belongs all come from
 * ontology/versions/registry.json.  Adding a version is an edit to that table.
 *
 * Usage:
 *   node scripts/generate-reserved-keys.mjs                  # the current version
 *   node scripts/generate-reserved-keys.mjs --version 4.5
 *   node scripts/generate-reserved-keys.mjs --source VCFv4.5.tex
 */

import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const REGISTRY_PATH = path.join(REPO_ROOT, "ontology", "versions", "registry.json");
const PACKAGE_PATH = path.join(REPO_ROOT, "package.json");

/**
 * The artifact version, for owl:versionInfo. The hand-authored modules carry the
 * release version there, so this generated module has to as well: a bundle that
 * mixes release versions with a VCF version leaves consumers of the merged graph
 * -- WebVOWL among them -- reading whichever ontology header they happen to pick.
 * The VCF version it describes goes on vcfc:specificationVersion instead.
 */
async function artifactVersion() {
  const manifest = JSON.parse(await fs.readFile(PACKAGE_PATH, "utf8"));
  if (!manifest.version) {
    throw new Error("package.json declares no version; cannot stamp owl:versionInfo");
  }
  return manifest.version;
}

function option(name, fallback) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

async function loadVersion(requested) {
  const registry = JSON.parse(await fs.readFile(REGISTRY_PATH, "utf8"));
  const id = requested ?? registry.current;
  const entry = registry.versions.find((version) => version.id === id);
  if (!entry) {
    const known = registry.versions.map((version) => version.id).join(", ");
    throw new Error(`Unknown VCF version ${id}; registry.json declares ${known}`);
  }
  if (entry.reservedKeys.mode !== "registry") {
    throw new Error(
      `VCF ${id} is declared as a "${entry.reservedKeys.mode}" version. Only "registry" versions ` +
        "have a machine-readable reserved-key source; snapshot versions are built by " +
        "scripts/build-shacl-profiles.py --spec-dir.",
    );
  }
  for (const field of ["expectedCounts", "graph", "ontologyIri"]) {
    if (!entry.reservedKeys[field]) {
      throw new Error(`VCF ${id} registry entry is missing reservedKeys.${field}`);
    }
  }
  return entry;
}

async function readSource(source) {
  if (/^https?:\/\//i.test(source)) {
    const response = await fetch(source);
    if (!response.ok) {
      throw new Error(`Could not download ${source}: ${response.status} ${response.statusText}`);
    }
    return response.text();
  }
  return fs.readFile(path.resolve(process.cwd(), source), "utf8");
}

function section(text, startMarker, endMarker) {
  const start = text.indexOf(startMarker);
  if (start < 0) throw new Error(`Missing source marker: ${startMarker}`);
  const end = text.indexOf(endMarker, start);
  if (end < 0) throw new Error(`Missing source marker: ${endMarker}`);
  return text.slice(start, end);
}

function longtableRows(text, label) {
  const labelAt = text.indexOf(`\\label{${label}}`);
  if (labelAt < 0) throw new Error(`Missing longtable label: ${label}`);
  const start = text.lastIndexOf("\\begin{longtable}", labelAt);
  const end = text.indexOf("\\end{longtable}", labelAt);
  if (start < 0 || end < 0) throw new Error(`Malformed longtable: ${label}`);

  return text
    .slice(start, end)
    .split(/\r?\n/)
    .filter((line) => line.includes("&") && /\\\\\s*$/.test(line))
    .map((line) => line.replace(/\\\\\s*$/, "").split("&").map((cell) => cleanTex(cell)))
    .filter((cells) => cells.length === 4 && cells[0] !== "Key" && cells[0] !== "Field")
    .map(([id, number, type, description]) => ({ id, number, type, description }));
}

function declarationRows(text, startMarker, endMarker, kind) {
  const source = section(text, startMarker, endMarker);
  const pattern = new RegExp(
    `##${kind}=<ID=([^,>]+),Number=([^,>]+),Type=([^,>]+),Description="([^"]*)">`,
    "g",
  );
  return [...source.matchAll(pattern)].map((match) => ({
    id: cleanTex(match[1]),
    number: cleanTex(match[2]),
    type: cleanTex(match[3]),
    description: cleanTex(match[4]),
  }));
}

function cleanTex(value) {
  return value
    .trim()
    .replace(/\\verb\|([^|]*)\|/g, "$1")
    .replace(/\\texttt\{([^}]*)\}/g, "$1")
    .replace(/\\textsc\{([^}]*)\}/g, "$1")
    .replace(/\\textbf\{([^}]*)\}/g, "$1")
    .replace(/\\emph\{([^}]*)\}/g, "$1")
    .replace(/\$<\$/g, "<")
    .replace(/\$>\$/g, ">")
    .replace(/\$<\$\*\$>\$/g, "<*>")
    .replace(/\$\{([^}]*)\}\$/g, "$1")
    .replace(/\\_/g, "_")
    .replace(/\\%/g, "%")
    .replace(/``|''/g, '"')
    .replace(/\s+/g, " ");
}

function turtleString(value) {
  return JSON.stringify(value);
}

function localName(kind, id) {
  const normalized = id
    .replace(/\[0-9\]\+/g, "ChEBI")
    .replace(/[^A-Za-z0-9_]/g, "_");
  return `Reserved${kind}_${normalized}`;
}

function arityStatements(number) {
  const symbolic = {
    A: "ArityPerAlt",
    R: "ArityPerAllele",
    G: "ArityPerGenotype",
    ".": "ArityVariable",
    LA: "ArityPerLocalAlt",
    LR: "ArityPerLocalAllele",
    LG: "ArityPerLocalGenotype",
    P: "ArityPerGTAllele",
    M: "ArityPerBaseModification",
  };
  if (symbolic[number]) return [`vcfc:fieldArity vcfc:${symbolic[number]}`];
  if (/^\d+$/.test(number)) return [`vcfc:fieldNumberInteger ${number}`];
  throw new Error(`Unsupported VCF Number value: ${number}`);
}

const CHEBI_ALIASES = new Map([
  ["M5mC", "27551"],
  ["M5hmC", "76792"],
  ["M5fC", "76794"],
  ["M5caC", "76793"],
  ["M5hmU", "16964"],
  ["M5fU", "80961"],
  ["M5caU", "17477"],
  ["M6mA", "28871"],
  ["M8oxoG", "44605"],
  ["MXaoN", "18107"],
]);

function aliasTarget(id) {
  const match = /^(DPM|ADM|M)(5mC|5hmC|5fC|5caC|5hmU|5fU|5caU|6mA|8oxoG|XaoN)$/.exec(id);
  if (!match) return null;
  const [, prefix, suffix] = match;
  const chebi = CHEBI_ALIASES.get(`M${suffix}`);
  const base = suffix.endsWith("U") ? "T" : suffix.endsWith("N") ? "N" : suffix.at(-1);
  return `${prefix}${chebi}${base}`;
}

function renderDefinition(kind, definition, entry) {
  const isPatternFamily = /^(M|DPM|ADM)\[0-9\]\+\[ACGTUN\]$/.test(definition.id);
  const statements = [
    `a owl:NamedIndividual, vcfc:${kind}FieldDefinition`,
    `rdfs:label ${turtleString(`${kind} ${definition.id} reserved field definition`)}@en`,
    `vcfc:fieldNumber ${turtleString(definition.number)}`,
    ...arityStatements(definition.number),
    `vcfc:fieldType vcfc:${definition.type}Type`,
    `vcfc:fieldDescription ${turtleString(definition.description)}`,
    `vcfc:reservedIn ${turtleString(entry.code)}`,
  ];

  // M, DPM, and ADM are parameterized key families in the VCF specification,
  // not literal keys.  Represent their grammar with keyPattern rather than
  // fabricating a fieldId that cannot satisfy the identifier lexical rule.
  if (!isPatternFamily) statements.splice(2, 0, `vcfc:fieldId ${turtleString(definition.id)}`);

  // Deprecations are a curated per-version table; the LaTeX source marks them
  // only in prose, so the registry records them explicitly.
  const deprecated = kind === "Info" ? entry.reservedKeys.deprecatedInfo?.[definition.id] : undefined;
  if (deprecated) statements.push(`vcfc:deprecatedInVersion ${turtleString(deprecated)}`);
  if (isPatternFamily) {
    statements.push(`vcfc:keyPattern ${turtleString(definition.id)}`);
  }
  const target = aliasTarget(definition.id);
  if (target) statements.push(`vcfc:aliasOf ${turtleString(target)}`);
  const chebi = CHEBI_ALIASES.get(definition.id);
  if (chebi) statements.push(`skos:exactMatch chebi:${chebi}`);

  return `vcfc:${localName(kind, definition.id)} ${statements.join(" ;\n  ")} .`;
}

function ensureCount(name, definitions, expected) {
  if (definitions.length !== expected) {
    throw new Error(`Expected ${expected} ${name} definitions, found ${definitions.length}`);
  }
}

function deduplicate(kind, definitions) {
  const seen = new Map();
  for (const definition of definitions) {
    const current = seen.get(definition.id);
    if (current && JSON.stringify(current) !== JSON.stringify(definition)) {
      throw new Error(`Conflicting ${kind} definitions for ${definition.id}`);
    }
    seen.set(definition.id, definition);
  }
  return [...seen.values()];
}

function sourceIri(source) {
  return /^https?:\/\//i.test(source) ? source : new URL(`file://${path.resolve(source)}`).href;
}

function render(text, source, sourceReference, entry, release) {
  const { expectedCounts: EXPECTED_COUNTS } = entry.reservedKeys;
  const info = longtableRows(text, "table:reserved-info");
  const format = longtableRows(text, "table:reserved-genotypes");
  const svInfo = declarationRows(
    text,
    "\\label{sv-info-keys}",
    "\\section{FORMAT keys used for structural variants}",
    "INFO",
  );
  const svFormat = declarationRows(
    text,
    "\\label{sv-format-keys}",
    "\\section{Representing variation in VCF records}",
    "FORMAT",
  );

  ensureCount("general INFO", info, EXPECTED_COUNTS.info);
  ensureCount("general FORMAT", format, EXPECTED_COUNTS.format);
  ensureCount("SV INFO", svInfo, EXPECTED_COUNTS.svInfo);
  ensureCount("SV FORMAT", svFormat, EXPECTED_COUNTS.svFormat);

  const allInfo = deduplicate("INFO", [...info, ...svInfo]);
  const allFormat = deduplicate("FORMAT", [...format, ...svFormat]);
  if (allInfo.length + allFormat.length !== EXPECTED_COUNTS.unique) {
    throw new Error(
      `Expected ${EXPECTED_COUNTS.unique} unique definitions, found ${allInfo.length + allFormat.length}`,
    );
  }

  const digest = createHash("sha256").update(text).digest("hex");
  const body = [
    ...allInfo.map((definition) => renderDefinition("Info", definition, entry)),
    ...allFormat.map((definition) => renderDefinition("Format", definition, entry)),
  ].join("\n\n");

  return `@prefix vcfc:  <https://w3id.org/vcf-core/vocab#> .
@prefix owl:   <http://www.w3.org/2002/07/owl#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dct:   <http://purl.org/dc/terms/> .
@prefix skos:  <http://www.w3.org/2004/02/skos/core#> .
@prefix chebi: <http://purl.obolibrary.org/obo/CHEBI_> .

#################################################################
# VCF ${entry.id} reserved-key registry
#
# Generated by scripts/generate-reserved-keys.mjs from ${sourceReference}
# SHA-256: ${digest}
# Source rows: ${info.length} general INFO, ${svInfo.length} SV INFO,
# ${format.length} general FORMAT, ${svFormat.length} SV FORMAT.
# Do not edit by hand; regenerate from the cited VCF ${entry.id} source.
#################################################################

<${entry.reservedKeys.ontologyIri}> a owl:Ontology ;
  rdfs:label "VCF Core reserved-key registry for VCF ${entry.id}"@en ;
  dct:source <${sourceIri(sourceReference)}> ;
  owl:imports <https://w3id.org/vcf-core/vocab> ;
  owl:versionInfo ${turtleString(release)} ;
  vcfc:specificationVersion ${turtleString(entry.code)} .

vcfc:specificationVersion a owl:AnnotationProperty ;
  rdfs:label "specification version"@en ;
  rdfs:comment "The VCF specification version a registry graph describes. It is distinct from owl:versionInfo, which records the release version of this vocabulary."@en .

vcfc:reservedIn a owl:AnnotationProperty ;
  rdfs:label "reserved in"@en ;
  rdfs:comment "Records the VCF specification version that reserves a field identifier or identifier pattern."@en .

vcfc:deprecatedInVersion a owl:AnnotationProperty ;
  rdfs:label "deprecated in version"@en ;
  rdfs:comment "Records the VCF specification version in which a reserved field is deprecated."@en .

vcfc:keyPattern a owl:AnnotationProperty ;
  rdfs:label "key pattern"@en ;
  rdfs:comment "The regular-expression family reserved by a FORMAT field definition rather than one concrete key."@en .

vcfc:aliasOf a owl:AnnotationProperty ;
  rdfs:label "alias of"@en ;
  rdfs:comment "The canonical reserved key denoted by a VCF base-modification alias."@en .

${body}
`;
}

const entry = await loadVersion(option("--version", undefined));
const source = option("--source", entry.source);
const output = option("--output", path.join(REPO_ROOT, entry.reservedKeys.graph));
const sourceReference = option("--source-reference", entry.source);
if (!source || !output) {
  throw new Error(
    "Usage: node scripts/generate-reserved-keys.mjs [--version <id>] [--source <path-or-url>] [--output <path>]",
  );
}

const sourceText = await readSource(source);
const generated = render(sourceText, source, sourceReference, entry, await artifactVersion());
await fs.writeFile(path.resolve(process.cwd(), output), generated, "utf8");
console.log(
  `Generated ${path.relative(REPO_ROOT, path.resolve(process.cwd(), output))} for VCF ${entry.id} from ${source}.`,
);
