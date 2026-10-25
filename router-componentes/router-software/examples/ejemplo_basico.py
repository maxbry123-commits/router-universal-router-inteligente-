"""ejemplo_basico.py — uso del Router Universal."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "red"))
from router import send, broadcast, SATELLITES

# 1) Enviar a un satélite
r = send("openclaw", {"text": "hola desde el router"}, kind="text")
print("openclaw:", r)

# 2) Broadcast a varios
resultados = broadcast({"text": "broadcast test"}, satellites=["openclaw", "ocr"])
for name, r in zip(["openclaw", "ocr"], resultados):
    print(f"{name}: {r}")
