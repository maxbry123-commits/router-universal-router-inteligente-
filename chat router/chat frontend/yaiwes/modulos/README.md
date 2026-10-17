# UI YAIWES interface — Fromtend

Owner: `➡️ Astra plan fábrica UI YAIWES`
Task: `T2_INTERFACE_YAIWES`
Gate: `T1_FACTORY_FRONTEND=VERIFIED_CLOSED`

Purpose: productive frontend root for UI YAIWES interface, built with the verified UI Factory.

Rules:
- analyze the physical inventory of 39 windows and project backend before module implementation; canonical inventory is `Ui Yaiwes interface beta/02-fromted/INDEX.json` (8 RUN + 16 WALL + 1 GBOT + 14 FOTO);
- REUSE > COPY > PATCH > ADAPT > GENERATE;
- every module/work unit gets its own project-memory destination, owner, node, SHA, evidence and status;
- preserve V+ reversible versions;
- no raw secrets in frontend;
- consume backend through contracts/adapters/API/MCP boundaries.
