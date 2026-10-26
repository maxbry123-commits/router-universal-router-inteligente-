<!-- INPUT BLOCK VERBATIM de Antonio (23-oct-2026). No editar: es la fuente 1 a 1 del SDK QwenCloud Token Plan. -->

SDK QwenCloud Token Plan Standard — $18/mes

Los 23 modelos oficiales, con sus identificadores exactos y código Python para llamarlos.

Verifiqué el catálogo y los endpoints en la documentación oficial de QwenCloud. El plan Standard utiliza 45.000 Credits mensuales, una clave propia sk-sp- y un endpoint diferente al de la API de pago por consumo. 

1. Configuración de la SDK

Instalación:

pip install openai requests websockets

Configuración común:

import os
from openai import OpenAI

API_KEY = os.environ["QWENCLOUD_TOKEN_PLAN_API_KEY"]

BASE_URL = (
    "https://token-plan.maas.qwencloudapi.com"
)

client = OpenAI(
    api_key=API_KEY,
    base_url=f"{BASE_URL}/compatible-mode/v1"
)

Este es el endpoint oficial para el protocolo OpenAI compatible del Token Plan. 

2. Los 13 modelos de texto y razonamiento

Todos utilizan client.chat.completions.create().

def llamar_modelo(modelo, mensaje):
    response = client.chat.completions.create(
        model=modelo,
        messages=[
            {
                "role": "user",
                "content": mensaje
            }
        ]
    )

    return {
        "modelo_solicitado": modelo,
        "modelo_reportado": response.model,
        "respuesta": response.choices[0].message.content,
        "finish_reason": response.choices[0].finish_reason,
        "usage": response.usage.model_dump()
            if response.usage else None
    }

Código individual de los 13 modelos

# 1. Selector automático
llamar_modelo("auto", "Hola")

# 2. Qwen 3.8 Max
llamar_modelo("qwen3.8-max", "Hola")

# 3. Qwen 3.8 Flash
llamar_modelo("qwen3.8-flash", "Hola")

# 4. Qwen 3.7 Max
llamar_modelo("qwen3.7-max", "Hola")

# 5. Qwen 3.7 Plus
llamar_modelo("qwen3.7-plus", "Hola")

# 6. Qwen 3.6 Flash
llamar_modelo("qwen3.6-flash", "Hola")

# 7. GLM 5.3
llamar_modelo("glm-5.3", "Hola")

# 8. GLM 5.2
llamar_modelo("glm-5.2", "Hola")

# 9. DeepSeek V4 Pro
llamar_modelo("deepseek-v4-pro", "Hola")

# 10. DeepSeek V4 Pro 0813
llamar_modelo("deepseek-v4-pro-0813", "Hola")

# 11. DeepSeek V4 Flash 0731
llamar_modelo("deepseek-v4-flash-0731", "Hola")

# 12. DeepSeek V4.1 Flash
llamar_modelo("deepseek-v4.1-flash", "Hola")

# 13. DeepSeek V4.1 Flash 1017
llamar_modelo("deepseek-v4.1-flash-1017", "Hola")

Los 13 identificadores están en el catálogo oficial de la edición personal. 

Para activar explícitamente el razonamiento de los modelos Qwen compatibles:

response = client.chat.completions.create(
    model="qwen3.8-max",
    messages=[
        {
            "role": "user",
            "content": "Analiza este código Python."
        }
    ],
    extra_body={
        "enable_thinking": True
    }
)

La configuración enable_thinking está documentada para los modelos Qwen de texto del plan. 


---

3. Los 3 modelos de imágenes

Estos modelos necesitan un endpoint de generación multimodal.

import requests

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def generar_imagen(modelo, prompt):
    response = requests.post(
        BASE_URL +
        "/api/v1/services/aigc/multimodal-generation/generation",
        headers=HEADERS,
        json={
            "model": modelo,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"text": prompt}
                        ]
                    }
                ]
            },
            "parameters": {
                "size": "1024*1024",
                "n": 1
            }
        },
        timeout=180
    )

    response.raise_for_status()
    return response.json()

Llamadas individuales

# 14. Qwen Image 3.0 Pro
generar_imagen(
    "qwen-image-3.0-pro",
    "Un robot futurista"
)

# 15. Wan 2.7 Image
generar_imagen(
    "wan2.7-image",
    "Una ciudad futurista"
)

# 16. Wan 2.7 Image Pro
generar_imagen(
    "wan2.7-image-pro",
    "Una estación espacial"
)

La documentación del Token Plan proporciona el endpoint multimodal y confirma que los modelos de imágenes no deben llamarse mediante Chat Completions. 


---

4. Los 3 modelos de audio

17. Qwen Audio 3.0 TTS Plus

Generación de voz:

def generar_voz(texto):
    response = requests.post(
        BASE_URL +
        "/api/v1/services/audio/tts/SpeechSynthesizer",
        headers=HEADERS,
        json={
            "model": "qwen-audio-3.0-tts-plus",
            "input": {
                "text": texto,
                "voice": "longanlingxin",
                "format": "mp3",
                "sample_rate": 24000
            }
        },
        timeout=180
    )

    response.raise_for_status()
    return response.content


audio = generar_voz("Hola, soy Qwen")

with open("respuesta.mp3", "wb") as archivo:
    archivo.write(audio)

Esta ruta corresponde al ejemplo HTTP de síntesis de voz publicado para Token Plan. 

18. Qwen Audio 3.0 ASR Flash

Reconocimiento de voz:

def reconocer_audio(audio_url):
    response = requests.post(
        BASE_URL +
        "/api/v1/services/aigc/multimodal-generation/generation",
        headers=HEADERS,
        json={
            "model": "qwen-audio-3.0-asr-flash",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_audio",
                                "input_audio": {
                                    "data": audio_url
                                }
                            }
                        ]
                    }
                ]
            },
            "parameters": {
                "format": "wav",
                "sample_rate": "16000"
            }
        },
        timeout=180
    )

    response.raise_for_status()
    return response.json()


reconocer_audio(
    "https://example.com/audio.wav"
)

El formato de entrada procede de la API HTTP oficial de reconocimiento de voz. 

19. Qwen Audio 3.0 Realtime Plus

Este modelo utiliza WebSocket.

import asyncio
import json
import websockets

async def conectar_audio_realtime():

    url = (
        "wss://token-plan.maas.qwencloudapi.com"
        "/api-ws/v1/realtime"
        "?model=qwen-audio-3.0-realtime-plus"
    )

    async with websockets.connect(
        url,
        additional_headers={
            "Authorization": f"Bearer {API_KEY}"
        }
    ) as ws:

        await ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "voice": "longanqian",
                "turn_detection": {
                    "type": "server_vad"
                }
            }
        }))

        print(await ws.recv())


asyncio.run(conectar_audio_realtime())

Importante: este ejemplo inicia la conexión y configura la sesión; todavía no transmite audio. La documentación confirma que Token Plan soporta WebSocket, pero no he verificado en vivo la ruta específica construida con el dominio del plan. 


---

5. Los 4 modelos de vídeo

Los vídeos se generan mediante tareas asíncronas.

def generar_video(
    modelo,
    prompt,
    media=None
):
    entrada = {
        "prompt": prompt
    }

    if media:
        entrada["media"] = media

    response = requests.post(
        BASE_URL +
        "/api/v1/services/aigc/video-generation/video-synthesis",
        headers={
            **HEADERS,
            "X-DashScope-Async": "enable"
        },
        json={
            "model": modelo,
            "input": entrada,
            "parameters": {
                "resolution": "720P",
                "duration": 5
            }
        },
        timeout=60
    )

    response.raise_for_status()
    return response.json()

Llamadas individuales

# 20. Wan 3.0 Video
generar_video(
    "wan3.0-video",
    "Un automóvil futurista avanzando por una ciudad"
)

# 21. HappyHorse 1.1 Text to Video
generar_video(
    "happyhorse-1.1-t2v",
    "Un robot caminando por Marte"
)

# 22. HappyHorse 1.1 Image to Video
generar_video(
    "happyhorse-1.1-i2v",
    "El robot empieza a caminar",
    media=[
        {
            "type": "first_frame",
            "url": "https://example.com/robot.png"
        }
    ]
)

# 23. HappyHorse 1.1 Reference to Video
generar_video(
    "happyhorse-1.1-r2v",
    "El robot de [Image 1] camina por la ciudad",
    media=[
        {
            "type": "reference_image",
            "url": "https://example.com/robot.png"
        }
    ]
)

Los parámetros first_frame y reference_image, así como el endpoint asíncrono, están documentados oficialmente. 

Para consultar el resultado del vídeo:

def consultar_video(task_id):
    response = requests.get(
        BASE_URL + f"/api/v1/tasks/{task_id}",
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()
    return response.json()

El resultado tendrá un video_url cuando la tarea alcance el estado SUCCEEDED.


---

6. Configuración para tu Router multimodelo

Este catálogo agrupa exactamente los 23 modelos del plan Standard.

QWEN_TOKEN_PLAN = {

    "base_url": (
        "https://token-plan.maas.qwencloudapi.com"
        "/compatible-mode/v1"
    ),

    "api_key_env": "QWENCLOUD_TOKEN_PLAN_API_KEY",

    "text_models": [
        "auto",
        "qwen3.8-max",
        "qwen3.8-flash",
        "qwen3.7-max",
        "qwen3.7-plus",
        "qwen3.6-flash",
        "glm-5.3",
        "glm-5.2",
        "deepseek-v4-pro",
        "deepseek-v4-pro-0813",
        "deepseek-v4-flash-0731",
        "deepseek-v4.1-flash",
        "deepseek-v4.1-flash-1017"
    ],

    "image_models": [
        "qwen-image-3.0-pro",
        "wan2.7-image",
        "wan2.7-image-pro"
    ],

    "audio_models": [
        "qwen-audio-3.0-tts-plus",
        "qwen-audio-3.0-realtime-plus",
        "qwen-audio-3.0-asr-flash"
    ],

    "video_models": [
        "wan3.0-video",
        "happyhorse-1.1-t2v",
        "happyhorse-1.1-i2v",
        "happyhorse-1.1-r2v"
    ]
}

Para integrar los modelos en tu Router:

Tipo	Protocolo

Texto y razonamiento	OpenAI Chat Completions
Imágenes	HTTP multimodal
Voz TTS	HTTP especializado
Reconocimiento ASR	HTTP multimodal
Audio Realtime	WebSocket
Vídeo	HTTP asíncrono


Estado: 23 identificadores contrastados con el catálogo oficial. Los ejemplos están preparados a partir de la documentación, pero no he ejecutado llamadas autenticadas con tu clave; por tanto, no los presento como pruebas de funcionamiento completadas..

Entre los recursos clave de código y SDK para agentes con QwenCloud destacan:

- Repositorio **Qwen Code** (TypeScript, 28.6k★): agente AI de codificación por QwenLM – https://github.com/QwenLM/qwen-code  
- Repositorio **Qwen Live Harness** (TypeScript, 232★): infraestructura de agente multimedia para Qwen Omni – https://github.com/QwenLM/Qwen-Live-Harness  
- Repositorio **Qwen MM Plugins** (Python, 3.1k★): plugins multimodales de Qwen – https://github.com/QwenLM/Qwen-MM-Plugins  
- Repositorio **QwenCloud AI Skills** (Node.js, 16★): colección oficial de “skills” para integrar QwenCloud en agentes – https://github.com/qwencloud/qwencloud-ai  

<!-- Decisiones de Antonio sobre este bloque: "auto" se quita; WebSocket solo en la SDK (el Router usa HTTP); se usan las 2 URL base (oficial primero, QwenCloud como alterna). -->
