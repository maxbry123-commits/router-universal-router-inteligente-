# Ejemplos de uso

## 1. Ping a un satélite

```python
from router import send
r = send("openclaw", {"text": "ping"})
```

## 2. OCR de una imagen

```python
r = send("ocr", {"image_b64": "..."}, kind="image")
```

## 3. Multi-agente consensus

```python
from router import broadcast
resultados = broadcast({"text": "votación: ¿X?"}, satellites=["openclaw", "claude-code", "mimo-code"])
```

## 4. Stream SSE para respuesta larga

```python
from connectors import SSEConnector
sse = SSEConnector("http://95.111.232.89:7000")
for chunk in sse.stream(artifact):
    print(chunk)
```
