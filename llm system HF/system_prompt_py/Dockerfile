# Dockerfile — Proxy OpenAI-compatible para HF Spaces (cpu-basic)
FROM python:3.11-slim

# 1. Variables de entorno para HF Spaces
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    HF_HOME=/tmp/hf_cache \
    TRANSFORMERS_CACHE=/tmp/hf_cache \
    XDG_CACHE_HOME=/tmp/.cache

# 2. Crear usuario no-root (UID 1000 es OBLIGATORIO en HF Spaces)
RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app

# 3. Instalar uv (gestor rápido de dependencias)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 4. Copiar requirements primero (cache de capas)
COPY --chown=user:user requirements.txt .

# 5. Instalar dependencias con cache de uv
RUN --mount=type=cache,target=/home/user/.cache/uv \
    uv pip install --system --no-cache -r requirements.txt

# 6. Copiar el código de la aplicación
COPY --chown=user:user . .

# 7. HF Spaces SOLO expone el puerto 7860
EXPOSE 7860

# 8. Arrancar FastAPI
CMD ["uvicorn", "openai_compatible_proxy:app", "--host", "0.0.0.0", "--port", "7860"]
