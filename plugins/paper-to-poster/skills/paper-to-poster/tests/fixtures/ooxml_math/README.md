# OOXML math schema (test fixture)

Used only by `tests/test_aij_export_pptx.py` to validate the Office equations
(OMML) that `aij/export_pptx.py` writes into the AIJ `.pptx` export
(docs/adr/0012). Not shipped to posters.

- `shared-math.xsd`, `shared-commonSimpleTypes.xsd` — **unmodified** copies from
  **ECMA-376 5th edition, Part 4 (Transitional Migration Features)**,
  `OfficeOpenXML-XMLSchema-Transitional.zip`
  (https://ecma-international.org/publications-and-standards/standards/ecma-376/).
  `shared-math.xsd` imports WordprocessingML (`wml.xsd`) and the `xml:`
  namespace; the test points those two imports at the stubs below **in memory,
  at load time** — the Ecma files themselves are not edited.
- `wml-stub.xsd`, `xml-stub.xsd` — minimal stand-ins written for this test (see
  their header comments). They are not part of ECMA-376.

The two Ecma files are reproduced under Ecma International's default copyright
notice, included here in full as that notice requires:

> COPYRIGHT NOTICE
>
> © Ecma International
>
> By obtaining and/or copying this work, you (the licensee) agree that you have
> read, understood, and will comply with the following terms and conditions.
>
> This document may be copied, published and distributed to others, and certain
> derivative works of it may be prepared, copied, published, and distributed, in
> whole or in part, provided that the above copyright notice and this Copyright
> License and Disclaimer are included on all such copies and derivative works.
> The only derivative works that are permissible under this Copyright License
> and Disclaimer are:
>
> (i) works which incorporate all or portion of this document for the purpose of
> providing commentary or explanation (such as an annotated version of the
> document),
>
> (ii) works which incorporate all or portion of this document for the purpose
> of incorporating features that provide accessibility,
>
> (iii) translations of this document into languages other than English and into
> different formats and
>
> (iv) works by making use of this specification in standard conformant products
> by implementing (e.g. by copy and paste wholly or partly) the functionality
> therein.
>
> However, the content of this document itself may not be modified in any way,
> including by removing the copyright notice or references to Ecma
> International, except as required to translate it into languages other than
> English or into a different format.
>
> The official version of an Ecma International document is the English language
> version on the Ecma International website. In the event of discrepancies
> between a translated version and the official version, the official version
> shall govern.
>
> The limited permissions granted above are perpetual and will not be revoked by
> Ecma International or its successors or assigns.
>
> This document and the information contained herein is provided on an "AS IS"
> basis and ECMA INTERNATIONAL DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED,
> INCLUDING BUT NOT LIMITED TO ANY WARRANTY THAT THE USE OF THE INFORMATION
> HEREIN WILL NOT INFRINGE ANY OWNERSHIP RIGHTS OR ANY IMPLIED WARRANTIES OF
> MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.

(Source of the notice text:
https://ecma-international.org/policies/by-ipr/ecma-text-copyright-policy/ —
"Default copyright notice".)

These files are test data, not part of the AGPL-licensed skill code.
