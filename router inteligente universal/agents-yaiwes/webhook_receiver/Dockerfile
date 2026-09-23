FROM python:3.12-slim
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" requests huggingface_hub
WORKDIR /app
COPY app.py .
EXPOSE 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
