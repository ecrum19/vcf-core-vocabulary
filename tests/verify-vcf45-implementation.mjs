#!/usr/bin/env node
/** Fast, dependency-free regression checks for the VCF 4.5 implementation. */

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { DataFactory, Parser, Store } from "n3";

const { namedNode } = DataFactory;
const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const namespace = "https://w3id.org/vcf-core/vocab#";
const rdfType = namedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#type");
const owlNamedIndividual = namedNode("http://www.w3.org/2002/07/owl#NamedIndividual");
const infoDefinition = namedNode(`${namespace}InfoFieldDefinition`);
const formatDefinition = namedNode(`${namespace}FormatFieldDefinition`);

const files = ["ontology", "shacl", "examples", "tests/shacl", "legacy"]
  .flatMap(directory => fs.readdirSync(path.join(repoRoot, directory), { recursive: true })
    .filter(file => file.endsWith(".ttl"))
    .map(file => path.join(directory, file)));


function parse(relativePath) {
  const source = fs.readFileSync(path.join(repoRoot, relativePath), "utf8");
  return new Store(new Parser().parse(source));
}

for (const file of files) parse(file);

const bundle = parse("ontology/vcf-core-vocabulary.bundle.ttl");
for (const localName of [
  "fieldArity",
  "hasAttribute",
  "lineIndex",
  "recordIndex",
  "Allele",
  "FieldValueItem",
  "Genotype",
  "SymbolicAlleleType",
  "ReferenceBlock",
  "VCFFloat",
]) {
  assert.ok(
    bundle.getQuads(namedNode(`${namespace}${localName}`), null, null, null).length > 0,
    `Missing implemented term vcfc:${localName}`,
  );
}

const registry = parse("ontology/vcf-core-reserved-keys.ttl");
const reservedDefinitions = new Set(
  registry
    .getQuads(null, rdfType, owlNamedIndividual, null)
    .map((quad) => quad.subject.value)
    .filter((subject) =>
      registry.getQuads(namedNode(subject), rdfType, infoDefinition, null).length > 0 ||
      registry.getQuads(namedNode(subject), rdfType, formatDefinition, null).length > 0,
    ),
);
assert.equal(reservedDefinitions.size, 122, "Registry must contain 122 unique VCF 4.5 reserved definitions");

for (const localName of ["ReservedInfo_END", "ReservedInfo_SVTYPE", "ReservedFormat_M5mC"]) {
  assert.ok(
    registry.getQuads(namedNode(`${namespace}${localName}`), null, null, null).length > 0,
    `Missing generated registry entry vcfc:${localName}`,
  );
}

const example = parse("examples/vcf-versions/vcf-4.5/example-vcf45-features.ttl");
for (const localName of [
  "HeaderAttribute",
  "ReferenceAllele",
  "AltAllele",
  "FieldValueItem",
  "Genotype",
  "ConfidenceInterval",
  "BaseModification",
]) {
  assert.ok(
    example.getQuads(null, rdfType, namedNode(`${namespace}${localName}`), null).length > 0,
    `Feature example does not exercise vcfc:${localName}`,
  );
}

console.log("VCF 4.5 implementation regression checks passed.");
