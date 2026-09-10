# Source-serialization fixtures

VCF 4.5 sections 1–1.2 constrain a file's bytes: UTF-8, no byte order mark, and
LF or CR+LF line separators. Those are requirements on the source stream rather
than on the logical model, so the vocabulary mints **no** term for them — an RDF
property would record a claim about the source without showing the source was
read. `coverage/vcf45-inventory/check_serialization.py` reads the actual bytes instead, and
`coverage/vcf45-inventory/report.py` reports the outcome as an axis separate from
logical-model coverage.

These two files hold identical logical content under the two permitted line
terminators. `tests/test_serialization.py` asserts that both satisfy the byte
requirements and that both materialize to the *same* RDF graph, which is the
evidence that the line-ending convention does not leak into the model.

They are deliberately outside `examples/vcf-versions/`, so the fixture
materializer does not emit a redundant pair of RDF files for them.
