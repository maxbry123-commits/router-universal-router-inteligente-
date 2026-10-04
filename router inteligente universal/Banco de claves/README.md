# Banco de claves

Código del banco cifrado del Router (`secret_bank/`: SQLite + AES-256-GCM, la clave sale de la clave maestra del Director con scrypt y nunca se guarda).

**Todo lo que necesitas saber del banco (dónde vive, qué tiene, cómo se agregan claves): [`HANDOFF-BANCO.md`](HANDOFF-BANCO.md).**

Reglas: ninguna clave en este repo; agregar, rotar o importar claves exige la clave del Director.
