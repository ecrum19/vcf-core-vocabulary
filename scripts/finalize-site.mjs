#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const repoRoot = process.cwd();
const sitePath = path.resolve(repoRoot, process.argv[2] || "site");
const hierarchyPath = path.join(sitePath, "assets", "ontology_hierarchy.ttl");
const referencePath = path.join(sitePath, "ontology-reference.html");
const ontologyPath = path.join(repoRoot, "ontology", "vcf-core-vocabulary.bundle.ttl");

// OCG hardcodes this note on the Reference page and offers no configuration for
// it. The page's own heading and table of contents already say what it is, so
// the sentence is removed here rather than left to describe a build detail.
const GENERATED_PAGE_NOTE =
  '<p class="section-note">This page is generated from the configured ontology file '
  + 'and links through to per-term pages when that feature is enabled.</p>';

if (!fs.existsSync(hierarchyPath)) {
  throw new Error(`OCG did not generate the hierarchy asset: ${path.relative(repoRoot, hierarchyPath)}`);
}

if (!fs.existsSync(referencePath) || !fs.readFileSync(referencePath, "utf8").includes('id="ontology-hierarchy"')) {
  throw new Error("OCG did not insert the configured class hierarchy into ontology-reference.html.");
}

const hierarchy = fs.readFileSync(hierarchyPath, "utf8");
const sourcePrefixes = fs.readFileSync(ontologyPath, "utf8")
  .split(/\r?\n/)
  .filter((line) => /^\s*@prefix\s+[^\s:]+:\s*<[^>]+>\s*\.\s*$/.test(line));
const declaredPrefixes = new Set(
  [...hierarchy.matchAll(/^\s*@prefix\s+([^\s:]+):/gm)].map((match) => match[1])
);
const missingPrefixes = sourcePrefixes.filter((line) => {
  const match = line.match(/^\s*@prefix\s+([^\s:]+):/);
  return match && !declaredPrefixes.has(match[1]);
});

if (missingPrefixes.length) {
  fs.writeFileSync(hierarchyPath, `${missingPrefixes.join("\n")}\n${hierarchy}`);
}

const reference = fs.readFileSync(referencePath, "utf8");
if (!reference.includes(GENERATED_PAGE_NOTE)) {
  throw new Error(
    "The generated-page note was not found in ontology-reference.html; OCG changed its wording, "
    + "so scripts/finalize-site.mjs needs updating."
  );
}
// Take the surrounding indentation and newline with it, so the published
// markup keeps no blank line where the note stood.
const escaped = GENERATED_PAGE_NOTE.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
fs.writeFileSync(referencePath, reference.replace(new RegExp(`[ \\t]*${escaped}\\n?`), ""));

console.log(
  `Class hierarchy verified and the generated-page note removed in ${path.relative(repoRoot, referencePath)}.`
);
