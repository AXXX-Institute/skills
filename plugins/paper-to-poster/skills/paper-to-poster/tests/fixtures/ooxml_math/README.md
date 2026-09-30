# OOXML math schema (test fixture)

Used only by `tests/test_aij_export_pptx.py` to validate the Office equations
(OMML) that `aij/export_pptx.py` writes into the AIJ `.pptx` export
(docs/adr/0012). Not shipped to posters.

- `shared-math.xsd`, `shared-commonSimpleTypes.xsd` — from **ECMA-376 5th
  edition, Part 4 (Transitional Migration Features)**,
  `OfficeOpenXML-XMLSchema-Transitional.zip`
  (https://ecma-international.org/publications-and-standards/standards/ecma-376/).
  The only edits: the `schemaLocation`s of the WordprocessingML and `xml:`
  imports point at the two stubs below.
- `wml-stub.xsd`, `xml-stub.xsd` — minimal stand-ins written for this test (see
  their header comments).

The ECMA-376 schemas are © Ecma International and are reproduced under Ecma's
copyright notice, which permits copying and distribution of the standard in
whole or in part provided the notice is included:

> © Ecma International. This document may be copied, published and distributed
> to others, and certain derivative works of it may be prepared, copied,
> published, and distributed, in whole or in part, provided that the above
> copyright notice and this Copyright License and Disclaimer are included on all
> such copies and derivative works.

They are test data, not part of the AGPL-licensed skill code.
