"""Fix 7: cola rapida separada, huerfanos cancelados y estado de cola (sin red)."""
import sys, threading, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "router inteligente universal"
sys.path.insert(0, str(ROOT))
from plugins.fichas_qwen import plugin as fq  # noqa: E402


def test_que_modelo_eres_va_a_cola_rapida():
    assert fq._es_fast_req({"ficha_qwen": "1", "message": "qué modelo eres", "task_type": "chat"})
    assert not fq._es_fast_req({"ficha_qwen": "1", "message": "qué modelo eres", "task_type": "code"})
    assert not fq._es_fast_req({"ficha_qwen": "2", "message": "qué modelo eres"})


def test_simple_no_espera_tras_4_pesadas(monkeypatch):
    stop = threading.Event()
    def lento(pid, p):
        if p.get("ficha_qwen") == "pesada":
            stop.wait(10)
            return {"reply": "x"}
        return {"reply": "rapido"}
    monkeypatch.setattr(fq, "_pool_run", lento)
    monkeypatch.setattr(fq, "_ck_guardar", lambda *a, **k: None)
    monkeypatch.setattr(fq, "_es_fast_req", lambda p: p.get("ficha_qwen") == "1")
    try:
        for _ in range(5):
            fq.handle("chat_async", {"ficha_qwen": "pesada", "message": "audita todo"})
        pid = fq.handle("chat_async", {"ficha_qwen": "1", "message": "qué modelo eres"})["proceso_id"]
        t0 = time.time()
        while time.time() - t0 < 3:
            r = fq.handle("resultado", {"proceso_id": pid})
            if r.get("estado") != "procesando":
                break
            time.sleep(0.05)
        assert r.get("reply") == "rapido"
        c = fq.handle("cola", {})
        assert c["corriendo"] >= 4 and c["en_cola"] >= 1
    finally:
        stop.set()


def test_huerfano_se_cancela(monkeypatch):
    stop = threading.Event()
    monkeypatch.setattr(fq, "_pool_run", lambda pid, p: stop.wait(10))
    monkeypatch.setattr(fq, "_ck_guardar", lambda *a, **k: None)
    try:
        pid = fq.handle("chat_async", {"ficha_qwen": "pesada", "message": "x"})["proceso_id"]
        fuera = fq._reap_huerfanos(time.time() + fq.HUERFANO_S + 1)
        assert pid in fuera and pid in fq._CANCEL
    finally:
        stop.set()
