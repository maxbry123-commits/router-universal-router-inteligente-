# UI YAIWES interface — Backend

Owner for this root: `➡️ Astra plan fábrica UI YAIWES` as UI-side backend staging/integration.
Task: `T2_INTERFACE_YAIWES`.

Purpose: collect backend-facing code, adapters, contracts and OSS donor capabilities required by the UI.

Boundary:
- this is not the productive backend root owned by Sol;
- no writes into Sol-owned backend paths without explicit handoff;
- promote only through API/MCP/contract boundaries;
- secrets remain runtime references only (`secret_ref`), never raw values;
- every donor requires source URL/ref/license/capability/destination/test/read-back.
