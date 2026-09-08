// Bounded fixture checks; this is neither a general VCF converter nor a SHACL validator.
import assert from 'node:assert/strict';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { Parser, Store, DataFactory } from 'n3';

const { namedNode } = DataFactory;
const V = 'https://w3id.org/vcf-core/vocab#';
const X = 'http://www.w3.org/2001/XMLSchema#';
const type = namedNode('http://www.w3.org/1999/02/22-rdf-syntax-ns#type');
const v = name => namedNode(V + name);
const read = name => readFileSync(new URL(name, import.meta.url), 'utf8');
const lines = read('synthetic.vcf').trimEnd().split('\n');
const columnNames = lines.find(line => line.startsWith('#CHROM\t')).split('\t');
const rows = lines.filter(line => !line.startsWith('#'));
assert.equal(rows.length, 1);
const row = rows[0].split('\t');
assert.equal(row.length, 12);
const sampleNames = columnNames.slice(9);
const keys = row[8].split(':');
const sourceCells = row.slice(9).map(block => block.split(':'));
assert.deepEqual(sampleNames, ['SAMPLE1', 'SAMPLE2', 'SAMPLE3']);
assert.deepEqual(keys, ['GT', 'DP']);
assert.deepEqual(sourceCells, [['0/1', '42'], ['0/0', '18'], ['./.', '.']]);

function objects(store, subject, predicate) {
  return store.getObjects(subject, typeof predicate === 'string' ? v(predicate) : predicate, null);
}
function one(store, subject, predicate) {
  const terms = objects(store, subject, predicate);
  assert.equal(terms.length, 1, `${subject.value}: expected exactly one ${predicate.value ?? predicate}`);
  return terms[0];
}
function instances(store, className) { return store.getSubjects(type, v(className), null); }
function assertType(store, subject, className) {
  assert(store.countQuads(subject, type, v(className), null), `${subject.value} lacks ${className}`);
}
function fieldKey(store, value) {
  const definition = one(store, value, 'declaredBy');
  assertType(store, definition, 'FormatFieldDefinition');
  const key = one(store, definition, 'fieldId').value;
  assert.equal(one(store, definition, 'fieldNumber').value, '1');
  assert.equal(one(store, definition, 'fieldType').value, V + (key === 'GT' ? 'StringType' : 'IntegerType'));
  one(store, definition, 'fieldDescription');
  return key;
}

const results = {};
for (const profile of ['expanded', 'condensed']) {
  // Reverse parse order deliberately: RDF statement order is not sample order.
  const store = new Store(new Parser().parse(read(`${profile}.ttl`)).reverse());
  const files = instances(store, 'VCFFile');
  assert.equal(files.length, 1);
  const file = files[0];
  assert.equal(one(store, file, 'fileFormat').value, 'VCFv4.5');
  const representation = one(store, file, 'representationProfile');
  assert.equal(representation.value, V + (profile === 'expanded' ? 'ExpandedRepresentation' : 'CondensedRepresentation'));
  assertType(store, representation, 'RepresentationProfile');
  const header = one(store, file, 'hasHeader');
  assertType(store, header, 'VCFHeader');
  const headerLines = objects(store, header, 'hasHeaderLine');
  assert.equal(headerLines.length, lines.filter(line => line.startsWith('##')).length);
  headerLines.forEach(line => assertType(store, line, 'HeaderLine'));
  const sampleSet = one(store, file, 'hasSampleSet');
  assertType(store, sampleSet, 'SampleSet');
  const samples = objects(store, sampleSet, 'hasSample').map(sample => {
    assertType(store, sample, 'VCFSample');
    const index = one(store, sample, 'sampleIndex');
    assert.equal(index.datatype.value, X + 'positiveInteger');
    return { sample, index: Number(index.value), name: one(store, sample, 'sampleName').value };
  }).sort((a, b) => a.index - b.index);
  assert.deepEqual(samples.map(sample => sample.index), [1, 2, 3]);
  assert.deepEqual(samples.map(sample => sample.name), sampleNames);
  const record = one(store, file, 'hasRecord');
  assertType(store, record, 'VCFRecord');
  for (const [property, column] of [['chrom', 0], ['pos', 1], ['recordId', 2], ['ref', 3], ['alt', 4]]) {
    assert.equal(one(store, record, property).value, row[column]);
  }
  const call = one(store, record, 'hasCall');
  assertType(store, call, 'VariantCall');
  for (const [property, column] of [['qual', 5], ['filter', 6], ['infoRaw', 7], ['formatRaw', 8]]) {
    assert.equal(one(store, call, property).value, row[column]);
  }
  let cells;
  if (profile === 'expanded') {
    assert.equal(instances(store, 'CohortCallMatrix').length, 0);
    assert.equal(instances(store, 'FormatValueVector').length, 0);
    const calls = objects(store, call, 'hasSampleCall');
    assert.equal(calls.length, 3);
    cells = samples.map(({ sample, name }) => {
      const matches = calls.filter(candidate => one(store, candidate, 'forSample').equals(sample));
      assert.equal(matches.length, 1);
      const sampleCall = matches[0];
      assertType(store, sampleCall, 'SampleCall');
      assert.equal(one(store, sampleCall, 'sampleId').value, name);
      const values = objects(store, sampleCall, 'hasFormatValue');
      assert.equal(values.length, keys.length);
      const fields = new Map(values.map(value => {
        assertType(store, value, 'FormatFieldValue');
        const raw = one(store, value, 'fieldValue');
        assert.equal(raw.datatype.value, raw.value === '.' ? V + 'Null' : X + 'string');
        const key = fieldKey(store, value);
        const typed = objects(store, value, 'fieldValueInteger');
        if (key === 'DP' && raw.value !== '.') {
          assert.equal(typed.length, 1);
          assert.equal(typed[0].datatype.value, X + 'integer');
          assert.equal(Number(typed[0].value), Number(raw.value));
        } else assert.equal(typed.length, 0);
        return [key, raw.value];
      }));
      assert.equal(fields.size, keys.length);
      return keys.map(key => fields.get(key));
    });
    assert.equal(instances(store, 'SampleCall').length, 3);
    assert.equal(instances(store, 'FormatFieldValue').length, 6);
  } else {
    assert.equal(instances(store, 'SampleCall').length, 0);
    assert.equal(instances(store, 'FormatFieldValue').length, 0);
    const matrix = one(store, call, 'hasCallMatrix');
    assertType(store, matrix, 'CohortCallMatrix');
    assert(one(store, matrix, 'appliesToSampleSet').equals(sampleSet));
    const vectors = objects(store, matrix, 'hasFormatValueVector');
    assert.equal(vectors.length, keys.length);
    const columns = new Map(vectors.map(vector => {
      assertType(store, vector, 'FormatValueVector');
      const encoding = one(store, vector, 'valueEncoding');
      assert.equal(encoding.value, V + 'VCFTextVector');
      assertType(store, encoding, 'VectorEncoding');
      const values = one(store, vector, 'encodedValues').value.split('\t');
      assert.equal(values.length, samples.length);
      return [fieldKey(store, vector), values];
    }));
    assert.equal(columns.size, keys.length);
    cells = samples.map(({ index }) => keys.map(key => columns.get(key)[index - 1]));
    assert.equal(cells.map(sample => sample.join(':')).join('\t'), one(store, matrix, 'sampleDataRaw').value);
    assert.equal(instances(store, 'CohortCallMatrix').length, 1);
    assert.equal(instances(store, 'FormatValueVector').length, 2);
  }
  assert.deepEqual(cells, sourceCells);
  assert.equal(cells[2][0], './.');
  assert.equal(cells[2][1], '.');
  results[profile] = {
    triples: store.size,
    rawFormatCellsRecovered: cells.flat().length,
    sampleCalls: instances(store, 'SampleCall').length,
    formatFieldValues: instances(store, 'FormatFieldValue').length,
    cohortCallMatrices: instances(store, 'CohortCallMatrix').length,
    formatValueVectors: instances(store, 'FormatValueVector').length,
    // Application-level check only; the separate SPARQL file is not executed here.
    applicationDepthAtLeast20: sampleNames.filter((_, i) => cells[i][1] !== '.' && Number(cells[i][1]) >= 20),
  };
  assert.deepEqual(results[profile].applicationDepthAtLeast20, ['SAMPLE1']);
}
const output = JSON.stringify({ status: 'passed', samples: sampleNames, ...results,
  scope: 'N3 parsing and fixture assertions; SPARQL and SHACL not executed' }, null, 2) + '\n';
const destination = new URL('generated/verification.json', import.meta.url);
if (process.argv.includes('--check')) {
  assert.equal(readFileSync(destination, 'utf8'), output, 'Recorded paper verification is stale; run npm run coverage:paper');
} else {
  mkdirSync(new URL('generated/', import.meta.url), { recursive: true });
  writeFileSync(destination, output);
}
console.log(output.trimEnd());
