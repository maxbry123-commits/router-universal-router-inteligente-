# Seguridad UI cerrada

1. Producto **sin** Factory (otro origen / otro binario).
2. Tokens: Keychain/Keystore. Nunca en HTML. Web no guarda secretos.
3. `wire.json` cifrado AES-256-GCM + PBKDF2 150k (`_shared/security.js`).
4. CSP en cada ventana.
5. iframe sandbox para code interno.
6. Tauri `fs:deny-default`.
7. Privacy screen / FLAG_SECURE en fábrica.
8. ABS fail-closed.
9. Connector user-picked: la ventana solo guarda `kind` + `url` pública, no OAuth token.
