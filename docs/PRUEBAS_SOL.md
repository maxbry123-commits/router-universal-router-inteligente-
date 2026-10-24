# Pruebas reales de los modelos (para Sol o Devin)

Quien ejecuta: Devin (su entorno ya llega a hf.space) o Sol si su máquina resuelve `comand-center-1-riu-router.hf.space`.
Requisitos: Python 3.9+, internet, la clave de acceso del Router en la variable `RIU_KEY` (nunca en archivos ni en la URL).

```
git clone --depth 1 https://github.com/maxbry123-commits/router-universal-router-inteligente-.git
cd router-universal-router-inteligente-
RIU_KEY='<clave>' python3 -m mvp.pruebas_vivo.correr            # todo: 12 modelos de texto x 13 pruebas + imagen, voz, video
RIU_KEY='<clave>' python3 -m mvp.pruebas_vivo.correr --solo glm-5.3   # un solo modelo
RIU_KEY='<clave>' python3 -m mvp.pruebas_vivo.correr --sin-medios     # solo texto y herramientas
```
Limpieza (los modelos de prueba dejan pendientes sol-* y yaiwes.md de prueba; el ejecutor los borra solo al terminar, o a mano): `RIU_KEY=<clave> python3 -m mvp.pruebas_vivo.limpiar`
Entrega: `informe_sol.md` y `informe_sol.json` (se crean en la carpeta actual). GitHub: solo la rama `prueba-sol`. Si falla la red/DNS: ejecutar desde otro entorno; si da 401: la clave no coincide con la del Space.
