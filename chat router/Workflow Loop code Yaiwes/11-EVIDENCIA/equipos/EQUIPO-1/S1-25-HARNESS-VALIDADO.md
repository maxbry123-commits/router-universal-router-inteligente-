# S1-25 Harness de DeepSeek validado
Fuente: deepseek-ai/deepseek-harness commit 639ed01 (14090 archivos), ya descargado en chat router/deepseek-harness-chat/code.
- pnpm 11.7.0 + node 24: pnpm install --frozen-lockfile OK (15.7 s).
- pnpm build:lib (host + client): BUILD_EXIT=0 con 4 vCPU/8 GB, corrido solo y con --max-old-space-size=6144. Antes fallaba exit 137 por memoria.
- dsh --version: 0.2.0-rc.2. dsh --help y dsh --profile headless --help responden (modo headless: una tarea, respuesta por stdout, --json eventos).
- No ejecutado: una tarea real con modelo (requiere clave de proveedor). Router no tocado.
