FROM python:3.11-slim
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=user:user . .
RUN chmod +x entrypoint.sh
EXPOSE 7860
CMD ["bash", "entrypoint.sh"]
