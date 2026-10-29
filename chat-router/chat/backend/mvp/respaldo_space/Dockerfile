FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
ENV HF_BUCKET_ID=COMAND-CENTER-1/yaiwes-memoria-storage     RIU_DATA_DIR=/data     RIU_VAULT_PATH=/data/riu_vault.db     RIU_VAULT_SOURCE=buckets/COMAND-CENTER-1/yaiwes-memoria-storage/router-inteligente-universal/banco/vault.db.gz.b64     RIU_VAULT_PROVIDERS_SOURCE=buckets/COMAND-CENTER-1/yaiwes-memoria-storage/router-inteligente-universal/banco/providers.json     RIU_CORS_ORIGINS=*     HF_HUB_DISABLE_PROGRESS_BARS=1
RUN pip install --no-cache-dir --upgrade pip &&     pip install --no-cache-dir huggingface_hub cryptography httpx "uvicorn[standard]" fastapi pydantic psutil mcp beautifulsoup4 pyyaml requests
RUN mkdir -p /data
WORKDIR /app
COPY boot.sh /boot.sh
RUN chmod +x /boot.sh
EXPOSE 7860
CMD ["/boot.sh"]
