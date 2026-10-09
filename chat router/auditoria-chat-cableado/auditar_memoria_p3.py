#!/usr/bin/env python3
"""PUNTO 3 — Auditar memoria + almacenamiento + harness del chat cableado (solo lectura/escritura de prueba, sin claves).

Instrucción (verbatim): "Verificar ruta completa: chat → puente_chat/harness → memory_runtime → memoria_yaiwes → store
Comprobar save/load/search y recuperación después de reinicio. Mejorarlo solo después de medir qué falla."

Entra por la misma puerta pública que usa la UI: LIVE_URL.json de main -> /plugins/puente_chat/call (chat_async/resultado)
y las rutas /memoria/* y /chat/history del Router. Escribe un JSON con PASS/FAIL por eslabón.
Para "recuperación después de reinicio": guarda las sesiones de prueba en --estado; al volver a correrlo después de un
cambio de Job comprueba que esos turnos siguen en /chat/history con un job_id distinto.
Con --sesiones-previas s1,s2 se mide ya, sin reiniciar nada: turnos de esas sesiones escritos ANTES de que naciera el Job
vivo (ts < creación del Job, leída del id del Job, y < LIVE_URL.updated) que hoy se leen en /chat/history del Job vivo.
Uso: python3 auditar_memoria_p3.py [--modelo groq-qwen-3-8] [--estado estado.json] [--salida informe.json] [--sesiones-previas a,b]
"""
import argparse, json, os, random, string, time, urllib.request

LIVE = "https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/LIVE_URL.json"


def http(method, url, body=None, timeout=60):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {}


def chat(puente, modelo, sesion, texto, tope=240):
    s, env = http("POST", puente + "/chat_async", {"model": modelo, "sesion": sesion, "max_tokens": 256,
                                                   "messages": [{"role": "user", "content": texto}]})
    r = (env or {}).get("result") or {}
    fin = time.time() + tope
    while r.get("estado") == "procesando" and time.time() < fin:
        time.sleep(1.5)
        s, env = http("POST", puente + "/resultado", {"proceso_id": r["proceso_id"]})
        r = (env or {}).get("result") or {}
    txt = ((r.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    return {"http": s, "texto": txt, "memoria_guardada": r.get("memoria_guardada"), "error": r.get("error")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="groq-qwen-3-8")
    ap.add_argument("--estado", default="estado-auditoria-p3.json")
    ap.add_argument("--salida", default="informe-auditoria-p3.json")
    ap.add_argument("--sesiones-previas", default="", help="sesiones escritas en un Job anterior, separadas por coma")
    a = ap.parse_args()
    _, live = http("GET", LIVE + "?t=%d" % time.time())
    base, job = live["LIVE_URL"], live.get("job_id")
    puente = base + "/plugins/puente_chat/call"
    filas = []

    def check(eslabon, ok, evidencia):
        filas.append({"eslabon": eslabon, "resultado": "PASS" if ok else "FAIL", "evidencia": evidencia})

    s, h = http("GET", base + "/health")
    check("Router /health", s == 200 and h.get("status") == "ok", {"http": s, "job_id": job})
    s, st = http("POST", puente + "/status", {})
    check("puente_chat/harness status", s == 200 and (st.get("result") or {}).get("ok") is True, {"http": s, "long_context": (st.get("result") or {}).get("long_context")})
    s, mh = http("GET", base + "/memoria/health")
    ad = (mh or {}).get("adapters") or {}
    check("memoria_yaiwes -> store (SQLite + grafo)", ad.get("sqlite", {}).get("status") == "CONNECTED" and ad.get("graph", {}).get("status") == "CONNECTED",
          {"sqlite": ad.get("sqlite"), "graph": ad.get("graph")})

    s, sto = http("GET", base + "/chat/storage")
    hb = (sto or {}).get("hf_bucket") or {}
    check("almacenamiento persistente: bucket HF configurado con escritura", s == 200 and hb.get("configured") is True and hb.get("write_token") is True,
          {"http": s, "hf_bucket": hb, "sqlite": (sto or {}).get("sql", {}).get("path")})

    palabra = "AUD-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    sesion = "audit-p3-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    t1 = chat(puente, a.modelo, sesion, "Palabra de auditoría: %s. Responde solo: OK" % palabra)
    check("chat -> puente_chat -> memory_runtime: turno guardado (memoria_guardada)", t1["memoria_guardada"] is True and bool(t1["texto"]), t1)
    s, hist = http("GET", base + "/chat/history/" + sesion)
    msgs = (hist or {}).get("messages") or []
    check("store -> /chat/history devuelve el turno (scope %s)" % (hist or {}).get("scope"), s == 200 and any(palabra in m.get("content", "") for m in msgs), {"http": s, "turns": (hist or {}).get("turns")})
    t2 = chat(puente, a.modelo, sesion, "¿Cuál es la palabra de auditoría que te di? Responde solo la palabra.")
    check("recuperación de contexto desde memoria (la UI envía solo el último mensaje)", palabra in t2["texto"], t2)
    otra = sesion + "-x"
    t3 = chat(puente, a.modelo, otra, "¿Cuál es la palabra de auditoría que te di? Si no la conoces responde exactamente: NO-LA-SE")
    check("aislamiento: otra sesión no ve esa memoria", palabra not in t3["texto"], t3)

    scope, key = "auditoria-p3", "k-" + palabra
    s1, sv = http("POST", base + "/memoria/save", {"scope": scope, "key": key, "data": {"palabra": palabra}})
    check("/memoria/save", s1 == 200, {"http": s1, "resp": sv})
    s2, ld = http("GET", base + "/memoria/load?scope=%s&key=%s" % (scope, key))
    check("/memoria/load", s2 == 200 and palabra in json.dumps(ld), {"http": s2, "resp": ld})
    s3, se = http("GET", base + "/memoria/search?scope=%s&query=%s&k=5" % (scope, palabra))
    check("/memoria/search", s3 == 200 and palabra in json.dumps(se), {"http": s3})

    nacido = min(float(live.get("updated") or 9e18), int(str(job)[:8], 16) if job else 9e18)  # ObjectId: 8 hex = segundos
    medidas_previas = 0
    for sp in [x.strip() for x in a.sesiones_previas.split(",") if x.strip()]:
        s, hp = http("GET", base + "/chat/history/" + sp + "?limit=1000")
        viejos = [m for m in (hp or {}).get("messages") or [] if m.get("ts") and m["ts"] < nacido]
        medidas_previas += 1
        check("recuperación después de reinicio: sesión %s escrita antes del Job %s y leída en él" % (sp, job), s == 200 and len(viejos) > 0,
              {"sesion": sp, "http": s, "turnos_total": (hp or {}).get("turns"), "mensajes_anteriores_al_job": len(viejos),
               "primer_ts": time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime(min(m["ts"] for m in viejos))) if viejos else None,
               "job_nacio": time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime(nacido))})

    previo = json.load(open(a.estado)) if os.path.exists(a.estado) else []
    for p in previo:
        if p.get("job_id") == job:
            continue
        s, hp = http("GET", base + "/chat/history/" + p["sesion"])
        ok = s == 200 and any(p["palabra"] in m.get("content", "") for m in (hp or {}).get("messages") or [])
        check("recuperación después de reinicio (sesión del Job %s leída en Job %s)" % (p["job_id"], job), ok, {"sesion": p["sesion"], "http": s})
    if not medidas_previas and not any(p.get("job_id") != job for p in previo):
        filas.append({"eslabon": "recuperación después de reinicio", "resultado": "PENDIENTE",
                      "evidencia": "no hay sesiones de un Job anterior en %s; volver a correr tras el próximo cambio de Job" % a.estado})
    json.dump(previo + [{"sesion": sesion, "palabra": palabra, "job_id": job, "ts": time.time()}], open(a.estado, "w"), indent=1)
    informe = {"job_id": job, "live_url": base, "ts": time.strftime("%Y-%m-%d %H:%M:%S %z"), "modelo": a.modelo, "filas": filas}
    json.dump(informe, open(a.salida, "w"), indent=1, ensure_ascii=False)
    for f in filas:
        print("%-9s %s" % (f["resultado"], f["eslabon"]))


if __name__ == "__main__":
    main()
