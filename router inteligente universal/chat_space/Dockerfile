FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    RIU_DATA_DIR=/data \
    RIU_CHAT_ALLOW_PROVIDER_LIVE=1

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

COPY riu /app/riu
RUN mkdir -p /data && chmod 777 /data

WORKDIR /app/riu
EXPOSE 7860
CMD ["uvicorn", "integration.chat_mvp.app:app", "--host", "0.0.0.0", "--port", "7860"]
