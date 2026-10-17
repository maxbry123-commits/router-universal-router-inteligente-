# Empaque · Run en dispositivo

**Web:** abrir `02-fromted/HOST.html` o zip estático (PWA).
**Linux/Windows:** Tauri stub → `npx tauri build` (repo Tauri-2 ya en fábrica).
**Android/iOS:** Capacitor `npx cap add android|ios` + `npx cap run`.
Auto-instalable: PWA “Añadir a pantalla de inicio” / TWA (PWABuilder) / instalador Tauri `.deb/.msi`.

Conexión: el usuario elige en HOST `local | web | github | huggingface | gdrive | database`.
Tokens solo en kernel nativo.
