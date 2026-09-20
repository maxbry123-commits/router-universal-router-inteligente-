# ADENDA A LA ARQUITECTURA — RIU-0109 — HF Jobs como fallback de modelos sin proveedor + decisiones D1-D7 — 2026-09-20

Anclas: `../Claude notas/INPUT-BLOCK-07-VERBATIM.md` (mismo texto) · `../bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/RIU-0109-DECISIONES-Y-ANALISIS-HF-JOBS.md`.
No modifica `README.md` (arquitectura consolidada hasta RIU-0094); se añade aparte por el límite de reescribir archivos grandes.
Solicitud del Director en este mensaje: "Anota todo esto en los archivos de ➡️📂 readme arquitectura router inteligente universal. Md" y "Todo imput block verbartin 1 a 1".

## Input literal del Director (verbatim)

---INICIO---

Correcto: no necesitas guardar una copia de los pesos en un Storage Bucket de tu cuenta si el modelo ya vive en un repositorio del Hugging Face Hub. El Job puede montar directamente ese repositorio con hf://... en modo lectura y usarlo desde el runtime. 

Pero hay una precisión importante: el modelo no se ejecuta “sin pesos”. Durante la ejecución, los pesos necesarios terminan siendo leídos/cargados por la máquina del Job en su almacenamiento temporal/RAM/VRAM. Lo que evitas es mantener tú una segunda copia persistente de esos pesos.

El esquema sería:

HUGGING FACE HUB
modelo original
      ↓
hf://models/ORG/MODELO
      ↓
HF JOB
GPU + almacenamiento temporal
      ↓
vLLM / llama.cpp / SGLang
      ↓
API
      ↓
TU ROUTER

Sí, HF Jobs tiene costo adicional

Hugging Face cobra Jobs por el hardware mientras el Job está Starting o Running, calculado por minuto. No es un servicio gratuito incluido simplemente por tener los modelos en el Hub. 

Precios oficiales actuales, por ejemplo:

GPU HF Job	VRAM	Precio aproximado

T4 small	16 GB	$0.40/h
L4	24 GB	$0.80/h
A10G small	24 GB	$1.00/h
L40S	48 GB	$1.80/h
A100	80 GB	$2.50/h
RTX PRO 6000	96 GB	$2.75/h
H200	141 GB	$5.00/h




Además, si expones un puerto para convertirlo en API para tu router, actualmente Hugging Face cobra $0.01/h adicional por Job con puertos expuestos. 

Entonces para tu caso la diferencia clave es:

❌ NO necesitas:
Storage Bucket propio
↓
copiar 10/20/30/100 GB de pesos
↓
mantener esa copia

✅ PUEDES:
modelo público/privado existente en HF Hub
↓
hf://modelo
↓
montarlo directamente en HF Job
↓
pagar únicamente el cómputo mientras corre

Y hay otra ventaja importante para tu router: no necesariamente tienes que dejar el Job encendido todo el día. Puedes levantar el Job cuando necesitas uno de esos modelos, hacer las inferencias y detenerlo; la facturación de Jobs es por minuto de ejecución. 

Por ejemplo, una L4 de $0.80/h durante 15 minutos son aproximadamente $0.20 de GPU, más una cantidad mínima por el puerto expuesto.

Así que tu arquitectura podría usar Inference Providers primero cuando haya proveedor, y HF Jobs solo como fallback para los modelos que nadie sirve, evitando pagar GPU permanentemente.


Anota todo esto en los archivos de ➡️📂 readme arquitectura router inteligente universal. Md 

Todo imput block verbartin 1 a 1 

Repuesta 

1. Revisa  Claude WebUI, o
Claude.ai UI Clone
  la idea es que pase por el router inteligente universal revisa si sirve o si no lob chat
 o LibreChat o open WebUI 
Que sea más rápido menos trabajo de programación y de conecte al router inteligente universal y puedas incluso conectar MCp para intervenir en la conversión 

2. Almacenamiento en huggueface 

3. Sí. Para tu Secret Bank aprobaría AES-256-GCM + contraseña maestra como primera versión, y añadiría passkey/WebAuthn después.

4. Si 

5. Revisa a ver si está en el repo de agentes o fromtend o router inteligente universal esa información 

6. Ambas 

7. Ya te di la solución de modelos como se hace en huggueface dime si eso lo resolveria 

Analiza

---FIN---

## Análisis: ¿HF Jobs resuelve los modelos que ningún proveedor sirve? — SÍ, con condiciones
Evidencia (motor de búsqueda del repo, sin LLM; `ws-35495171232`, `ws-35495174728`, y verificación de permisos run `35493843251`):
- Documentación oficial "Serve Models on Jobs" y blog "Run a vLLM Server on HF Jobs in One Command" (2026-06-26): `hf jobs run --flavor <hardware> --expose 8000 --timeout 2h vllm/vllm-openai:latest vllm serve <repo> --host 0.0.0.0 --port 8000 …`. Timeout por defecto 30 minutos; la facturación termina al cancelar o vencer el timeout.
- `huggingface/hf-mount`: monta buckets y repos como sistema de archivos; lectura/escritura para buckets, solo lectura para modelos y datasets.
- Inference Endpoints: dedicados, autoscaling, escala a cero, motores vLLM/SGLang/llama.cpp/TEI y contenedor propio; hay casos reportados de arranque en frío colgado en "Initializing".
- `HF_TOKEN_1` tiene `job.write` y `inference.endpoints.write`.
- Las tarifas de la tabla pegada NO las verifiqué (página oficial: huggingface.co/docs/hub/en/jobs-pricing).

Qué resuelve: cada modelo sin proveedor es un repo del Hub, así que un Job puede ejecutar `vllm serve <repo>` (o llama.cpp con GGUF oficial) bajo demanda. No hay copia persistente de pesos y encaja con "no instalarlos, llamarlos remotos"; "duplicarse" = más Jobs.

Condiciones:
1. CONTRATO. La `truth_rule` de `model_registry.json` prohíbe descargar pesos; un Job los carga de forma efímera. Hay que ampliar el contrato con una clase de runtime nueva, `HF_JOB_EPHEMERAL_SERVING`: pesos leídos desde `hf://` en solo lectura, `persistent_weights=0`, `mirrors=0`. Se registra como decisión del Director.
2. ESTADOS. No es instantáneo. La cola del Router necesita COLD → STARTING → READY → DRAINING → STOPPED; el primer token llega en minutos. Sirve para ráfagas y lotes, no para una conversación interactiva en frío.
3. SEGURIDAD. `--expose` publica un puerto: exigir `--api-key` (del Secret Bank), timeout explícito, tope de gasto y un vigilante (reutilizar `hf_scheduler.py`, RIU-0074).
4. DIMENSIONAMIENTO (estimación propia, no verificada): 0.5–3B caben en CPU o T4; 7–9B en bf16 necesitan ~16–24 GB (L4/A10G); 30–33B necesitan 48–80 GB en bf16 (L40S/A100) o cuantización 4-bit (~20 GB) para L4/A10G. Un servidor vLLM atiende muchas peticiones concurrentes: para 50+ agentes se comparte un servidor por modelo, no uno por agente.
5. ALCANCE. No cubre imagen ni vídeo (FLUX, Qwen-Image, Wan, LTX, Hunyuan no se sirven con vLLM), ni el requisito "≤26 GB de RAM local" si el Director aún quiere ejecución en su máquina.
Alternativa: Inference Endpoints (URL HTTPS privada, escala a cero, más simple de consumir; coste por hora de hardware).

Cascada resultante del Router para modelos sin proveedor serverless: Inference Providers → Job ya en caliente → arrancar Job → (grupo 2) DeepSeek V4 Flash.
Prueba pendiente (S7.3, requiere aprobar un gasto de céntimos): lanzar un modelo pequeño en un Job con `HF_TOKEN_1`, llamar `/v1/chat/completions`, medir arranque en frío y coste, cancelar.

## Decisiones del Director en este mensaje
| # | Respuesta | Efecto |
|---|---|---|
| 1 | Chat OSS rápido, conectado al Router, con MCP para intervenir en la conversación | Open WebUI (evaluado; ver bitácora RIU-0109) |
| 2 | "Almacenamiento en huggueface" | Space Docker + Storage Bucket como volumen |
| 3 | Aprobado | Secret Bank: AES-256-GCM + contraseña maestra; passkey/WebAuthn después |
| 4 | "Si" | `HF_TOKEN_1` permanece en GitHub solo para el despliegue (CI) |
| 5 | Buscar los logins en agentes/frontend/router | No encontrados (ver bitácora); hace falta el login público de cada cuenta |
| 6 | "Ambas" | Se registran `LiquidAI/LFM2-2.6B` y `LiquidAI/LFM2.5-2.6B` |
| 7 | HF Jobs como solución | Análisis arriba: SÍ con condiciones |
