# R-004 PDF extraction audit

Contract: `tel.workflow/v3`  
Mode: `FAIL_CLOSED_LOOP`

## Scope
Single 1x1 delta: recover the canonical source declared for C19/R-004 from `Documentos proyectos router inteligente universal/lote 1 documentos proyecto/respaldo.py.pdf` without generating substitute code.

## Canonical evidence
- PDF path: `Documentos proyectos router inteligente universal/lote 1 documentos proyecto/respaldo.py.pdf`
- Git blob: `2ee8d937493d1923b2c1e5d6cc294a1513df3c91`
- Size recorded by CHECKPOINT: 27576 bytes.
- Origin commit for the PDF path: `7db4e349ff3ea22be5f1b8c10a1efc46b73418aa` (`Documentos proyectos router inteligente universal`).
- Architecture contract recovered from the same commit: R-004 is `infrastructure/backup/respaldo.py`, REUSE exact, approximately 40 LOC, public functions `empaquetar()` and `verificar()`, zip + SHA-256 manifest; mandatory tests include round-trip and broken-file detection.

## StrategyDelta attempts
1. GitHub `fetch_file(..., encoding=base64)` proved the binary is retrievable as base64 and begins with a valid PDF header, but the connector response is paginated/truncated for direct local materialization.
2. GitHub blob UTF-8 fetch failed closed with `UnicodeDecodeError`; binary was not treated as source text.
3. Raw GitHub/web retrieval returned cache/fetch failure; container-side network retrieval failed with temporary DNS resolution failure.
4. No `.py` substitute was generated and no R-004 runtime PASS is claimed.

## Decision
`GAP-R004-EXTRACTION-001` remains OPEN. Evidence improved from `PDF located` to `PDF identity/origin/contract verified; binary materialization unavailable in this runtime`. Because the exact source cannot be reconstructed byte-for-byte from verified evidence, `REUSE > PATCH > ADAPT > GENERATE` forbids writing `infrastructure/backup/respaldo.py` now.

## Council12
1 objective PASS; 2 INPUT PASS; 3 destination PASS; 4 state PASS; 5 evidence PASS; 6 reusable FOUND_PDF/BLOCKED_EXTRACTION; 7 architecture PASS; 8 concurrency PASS; 9 dependency BLOCKED_BINARY_PATH; 10 test NOT_RUN_BY_DESIGN; 11 rollback N/A; 12 closure PASS_FOR_AUDIT_ONLY.

## Three refutations
1. Base64-visible PDF != exact Python source recovered.
2. Function names/behavior contract != permission to regenerate the implementation.
3. Audit PASS != R-004 runtime PASS != P02 closed != E2E P03.

## Cross-check / CODA / verify_final
Handoff C19, PLAN, CHECKPOINT, RECOVERY and PDF commit history agree on identity and intended behavior. CODA selects no-code fail-closed over speculative generation. `verify_final = PASS_AUDIT_ONLY`.

## Next safe action
Keep R-004 flagged and audit the next independent P02 architecture-backed component with sufficient source/contract evidence before any implementation.
