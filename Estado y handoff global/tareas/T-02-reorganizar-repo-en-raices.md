# T-02 — Reorganizar el repo en las raíces que pediste
**Estado:** PASS · **Depende de:** T-01 · **Nodo:** N-02 · **Commit:** 93c70073

## Cómo quedó `main` (16 entradas, todo movido, ningún componente borrado)
| Raíz | Qué tiene |
|---|---|
| `router inteligente universal/` | El Router, los agentes, `Banco de claves/` (antes "Chat Mvp"), `Componentes del Router/` (software, api, control plane, dataset, hermes-agent), `scripts/` y los componentes de código abierto (submódulos intactos) |
| `chat router/` | El chat, el plan, los agentes del chat, `chat_orders/` |
| `Motores descarga extracción búsquedas/` | Motores de descarga y extracción, motores de búsqueda, `Download code…` |
| `Readme router inteligente universal/` | El índice y los readmes de componentes |
| `Readme arquitectura router inteligente universal/` | La arquitectura (no se tocó) |
| `Claude notas/` | Solo lo en curso (hoy: KIT-EQUIPO-NVIDIA) |
| `Estado y handoff global/` | Crazy Wall, bitácora, estado (JSON), handoff global y una ficha por tarea (esta carpeta) |
| `Huggingface/` | Todo lo de Hugging Face y GitHub (conexiones, rutas, handoff) |
| `Vercel/` | El chat de Vercel y su handoff |
| `Documentos del proyecto/` | Tus archivos markdown subidos, notas del Director, documentos, orquestador |
Sueltos en la raíz: `CLAUDE.md`, `vercel.json` (Vercel lo lee desde la raíz; se queda hasta el deploy final), `.github`, `.gitmodules`, `.gitignore`, `.devcontainer`.

## Rutas que se corrigieron junto con el movimiento
8 workflows (banco de claves, motores, `chat_orders`, `scripts`, búsqueda web), 2 archivos del agente 11 y 1 de memoria. Se borró `replicar-motores.yml` (ruido). El Router NO se movió: sus rutas no cambian.

## Pendiente de esta tarea
- El loop de agentes (repo `agentes`, `plan_opus_loop.py` línea ~110) todavía baja el banco de la ruta vieja `Chat%20Mvp/…`. Se arregla en T-04 (ahí se reemplaza por el Router).
- Los archivos `readme` viejos mencionan rutas anteriores en su texto (solo prosa; no rompen nada).
- Falta probar en vivo los workflows tocados (solo se revisó que el texto quedó bien).

## Cómo se comprobó
Ensayo en seco (run 36520932226) y aplicación (run 36521041442): raíz verificada por el listado del árbol; las ediciones de rutas se leyeron después de subirse.

## Para mover la raíz del Router a otro repo
Copiar la carpeta `router inteligente universal/` completa; el workflow que la lanza es `.github/workflows/riu-router-job-central.yml`.
