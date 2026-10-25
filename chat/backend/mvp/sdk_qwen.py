"""SDK QwenCloud Token Plan Standard: el input block de Antonio 1 a 1 (INPUT_BLOCK_SDK_QWEN.md). Fuente unica de rutas, cuerpos y catalogo;
multimedia.py arma sus peticiones con estas funciones. Diferencias deliberadas: dos URL base (oficial y QwenCloud), User-Agent oficial, sin "auto",
`openai`/`websockets` solo se importan si se usan (el Router habla HTTP y no los exige)."""
import os

BASE_URL = "https://token-plan.maas.qwencloudapi.com"
BASE_URL_OFICIAL = "https://token-plan.ap-southeast-1.maas.aliyuncs.com"
API_KEY_ENV = "QWENCLOUD_TOKEN_PLAN_API_KEY"
CLAVES_ENV = ("QWENCLOUD_API_KEY", "QWEN_API_KEY", "DASHSCOPE_API_KEY", API_KEY_ENV)  # orden del SDK oficial + la del bloque
RUTAS = {"imagen": "/api/v1/services/aigc/multimodal-generation/generation", "asr": "/api/v1/services/aigc/multimodal-generation/generation",
         "voz": "/api/v1/services/audio/tts/SpeechSynthesizer", "video": "/api/v1/services/aigc/video-generation/video-synthesis",
         "tarea": "/api/v1/tasks/", "realtime": "/api-ws/v1/realtime"}
QWEN_TOKEN_PLAN = {
    "base_url": BASE_URL + "/compatible-mode/v1", "api_key_env": API_KEY_ENV,
    "text_models": ["qwen3.8-max", "qwen3.8-flash", "qwen3.7-max", "qwen3.7-plus", "qwen3.6-flash", "glm-5.3", "glm-5.2", "deepseek-v4-pro",
                    "deepseek-v4-pro-0813", "deepseek-v4-flash-0731", "deepseek-v4.1-flash", "deepseek-v4.1-flash-1017"],  # sin "auto" (decision de Antonio)
    "image_models": ["qwen-image-3.0-pro", "wan2.7-image", "wan2.7-image-pro"],
    "audio_models": ["qwen-audio-3.0-tts-plus", "qwen-audio-3.0-realtime-plus", "qwen-audio-3.0-asr-flash"],
    "video_models": ["wan3.0-video", "happyhorse-1.1-t2v", "happyhorse-1.1-i2v", "happyhorse-1.1-r2v"]}


def headers(api_key, extra=None):
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "qwencloud-skills", **(extra or {})}


def cuerpo_imagen(modelo, prompt):
    return {"model": modelo, "input": {"messages": [{"role": "user", "content": [{"text": prompt}]}]}, "parameters": {"size": "1024*1024", "n": 1}}


def cuerpo_voz(texto):
    return {"model": "qwen-audio-3.0-tts-plus", "input": {"text": texto, "voice": "longanlingxin", "format": "mp3", "sample_rate": 24000}}


def cuerpo_asr(audio_url):
    return {"model": "qwen-audio-3.0-asr-flash", "input": {"messages": [{"role": "user", "content": [{"type": "input_audio", "input_audio": {"data": audio_url}}]}]},
            "parameters": {"format": "wav", "sample_rate": "16000"}}


def cuerpo_video(modelo, prompt, media=None):
    entrada = {"prompt": prompt}
    if media:
        entrada["media"] = media
    return {"model": modelo, "input": entrada, "parameters": {"resolution": "720P", "duration": 5}}


def media_de(modelo, url):
    return [{"type": "reference_image" if modelo.endswith("r2v") else "first_frame", "url": url}]


def llamar_modelo(modelo, mensaje, api_key=None, base_url=None):
    from openai import OpenAI  # solo la SDK de referencia lo necesita
    client = OpenAI(api_key=api_key or next(os.environ[n] for n in CLAVES_ENV if os.environ.get(n)), base_url=(base_url or BASE_URL) + "/compatible-mode/v1")
    response = client.chat.completions.create(model=modelo, messages=[{"role": "user", "content": mensaje}])
    return {"modelo_solicitado": modelo, "modelo_reportado": response.model, "respuesta": response.choices[0].message.content,
            "finish_reason": response.choices[0].finish_reason, "usage": response.usage.model_dump() if response.usage else None}


def generar_imagen(modelo, prompt, api_key, base_url=BASE_URL):
    import requests
    r = requests.post(base_url + RUTAS["imagen"], headers=headers(api_key), json=cuerpo_imagen(modelo, prompt), timeout=180)
    r.raise_for_status()
    return r.json()


def generar_voz(texto, api_key, base_url=BASE_URL):
    import requests
    r = requests.post(base_url + RUTAS["voz"], headers=headers(api_key), json=cuerpo_voz(texto), timeout=180)
    r.raise_for_status()
    return r.content


def reconocer_audio(audio_url, api_key, base_url=BASE_URL):
    import requests
    r = requests.post(base_url + RUTAS["asr"], headers=headers(api_key), json=cuerpo_asr(audio_url), timeout=180)
    r.raise_for_status()
    return r.json()


def generar_video(modelo, prompt, api_key, media=None, base_url=BASE_URL):
    import requests
    r = requests.post(base_url + RUTAS["video"], headers=headers(api_key, {"X-DashScope-Async": "enable"}), json=cuerpo_video(modelo, prompt, media), timeout=60)
    r.raise_for_status()
    return r.json()


def consultar_video(task_id, api_key, base_url=BASE_URL):
    import requests
    r = requests.get(base_url + RUTAS["tarea"] + task_id, headers=headers(api_key), timeout=30)
    r.raise_for_status()
    return r.json()
