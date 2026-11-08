FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y -qq curl ca-certificates python3 python3-pip tar gzip libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --break-system-packages -q huggingface_hub hf_transfer

ARG LLAMA_URL=https://github.com/ggerganov/llama.cpp/releases/download/b12000/llama-b12000-bin-ubuntu-x64.tar.gz
RUN mkdir -p /opt/llama /app /data/models \
    && curl -fsSL "$LLAMA_URL" -o /tmp/llama.tgz \
    && tar -xzf /tmp/llama.tgz -C /opt/llama \
    && rm /tmp/llama.tgz \
    && BIN=$(find /opt/llama -type f -name llama-server | head -1) \
    && test -n "$BIN" \
    && ln -sf "$BIN" /usr/local/bin/llama-server

COPY manager.py /app/manager.py
ENV PYTHONPATH=/app
WORKDIR /app
EXPOSE 7860
CMD ["python3", "/app/manager.py"]
