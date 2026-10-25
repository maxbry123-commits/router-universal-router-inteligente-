FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir fastapi "uvicorn[standard]"
WORKDIR /app
COPY boot.sh /boot.sh
RUN chmod +x /boot.sh
EXPOSE 7860
CMD ["/boot.sh"]
