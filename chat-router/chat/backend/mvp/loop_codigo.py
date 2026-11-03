"""LOOP CODA de codigo largo: usa el chat/Harness y el checkpoint existentes.

No ejecuta codigo generado ni herramientas. Una parte solo cuenta si pasa AST,
y una tarea solo termina con exactamente N lineas y validacion del conjunto.
El 429 es pausa de cuota, no PASS ni motivo para borrar el cursor.
"""
from __future__ import annotations
import ast
import asyncio
import hashlib
import json
import re
import time
from typing import Awaitable, Callable

CODIGO = re.compile(r"\b(?:c[oó]digo|code|python|programa|script|\.py)\b", re.I)
LINEAS = re.compile(r"\b(\d{2,4})\s+l[ií]neas?\b", re.I)
REINTENTABLE = re.compile(r"(?:HTTP[_ ](?:408|425|429|500|502|503|504|529)|limite.temporal|timeout|timed.out|GROQ_NVIDIA_REINTENTOS)", re.I)
BLOQUE = 50


def solicitado(mensaje: str, tipo: str = "", modo: str = "") -> int | None:
    """Activacion explicita; nunca convierte consulta normal en bucle."""
    m = LINEAS.search(mensaje)
    if m and CODIGO.search(mensaje) and 100 <= int(m.group(1)) <= 2000:
        return int(m.group(1))
    return 500 if tipo == "code_largo" and modo == "loop" else None


def _limpiar(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        a = s.splitlines()
        if a and a[0].strip() in ("```", "```python", "```py"):
            a.pop(0)
            if a and a[-1].strip() == "```":
                a.pop()
            s = "\n".join(a)
    return s.strip("\n")


def _valida(parte: str, limite: int, hashes: set[str]) -> tuple[bool, str, int]:
    t = _limpiar(parte)
    n = len(t.splitlines())
    if not t or n < 10 or n > limite:
        return False, "CANTIDAD_LINEAS_INVALIDA", n
    if hashlib.sha256(t.encode()).hexdigest() in hashes:
        return False, "SEGMENTO_REPETIDO", n
    try:
        arbol = ast.parse(t)
    except SyntaxError:
        return False, "SINTAXIS_PYTHON_INVALIDA", n
    if not any(isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for x in arbol.body):
        return False, "FALTAN_DEFINICIONES", n
    return True, t, n


async def generar(*, mensajes: list[dict], modelo: str, pid: str, n_lineas: int,
                  inferir: Callable[[list[dict], int], Awaitable[dict]],
                  cargar: Callable[[], Awaitable[dict | None]],
                  guardar: Callable[[dict], Awaitable[bool]],
                  progreso: Callable[[str, str], None] = lambda _n, _t: None,
                  cancelado: Callable[[], bool] = lambda: False,
                  horas: float = 4.0,
                  dormir: Callable[[float], Awaitable[None]] = asyncio.sleep,
                  reloj: Callable[[], float] = time.time) -> dict:
    if not (100 <= n_lineas <= 2000) or not (0 < horas <= 4):
        raise ValueError("CODA_LIMITE_INVALIDO")
    entrada = json.dumps([modelo, mensajes, n_lineas], ensure_ascii=False, sort_keys=True)
    huella = hashlib.sha256(entrada.encode()).hexdigest()
    estado = await cargar()
    if estado and (estado.get("tipo") != "coda-codigo-v1" or estado.get("huella") != huella):
        raise ValueError("CODA_CHECKPOINT_OTRA_TAREA")
    if not estado:
        estado = dict(tipo="coda-codigo-v1", huella=huella, modelo=modelo,
                      n_lineas=n_lineas, piezas=[], creado=reloj(), intentos=0,
                      siguiente_llamada=0, validacion="PENDIENTE")
        if not await guardar(estado):
            raise RuntimeError("CODA_CHECKPOINT_NO_PERSISTIDO")
    piezas = list(estado["piezas"])
    hashes = {hashlib.sha256(t.encode()).hexdigest() for t in piezas}
    if estado.get("validacion") == "PASS" and sum(len(x.splitlines()) for x in piezas) == n_lineas:
        return {"texto": "\n".join(piezas) + "\n", "lineas": n_lineas, "partes": len(piezas), "desde_checkpoint": True}
    vencimiento = min(float(estado["creado"]) + horas * 3600, reloj() + horas * 3600)
    fallos = 0
    while sum(len(t.splitlines()) for t in piezas) < n_lineas:
        if cancelado():
            raise RuntimeError("CODA_CANCELADO_CHECKPOINT_CONSERVADO")
        if reloj() >= vencimiento:
            raise RuntimeError("CODA_TIEMPO_AGOTADO_CHECKPOINT_CONSERVADO")
        faltan = n_lineas - sum(len(t.splitlines()) for t in piezas)
        pedir_lineas = min(BLOQUE, faltan)
        definiciones = []
        for t in piezas:
            arbol = ast.parse(t)
            definiciones += [x.name for x in arbol.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        cabecera = (
            f"TAREA CODA DE CODIGO PYTHON. Archivo total: {n_lineas} lineas; "
            f"ya validadas: {n_lineas - faltan}; parte {len(piezas)+1}.\n"
            f"Genera EXACTAMENTE {pedir_lineas} lineas FISICAS de codigo nuevas en ESTA parte. "
            "Solo Python sintacticamente valido, sin markdown ni explicaciones. "
            "Este segmento debe poder analizarse solo con ast.parse: "
            "funciones o clases completas, no fragmentos con sangria abierta. "
            "No repitas definiciones anteriores. Solo biblioteca estandar. "
            "Sin llamadas a herramientas, sin afirmar commits. "
            "No uses from __future__ ni nombres de funciones anteriores. "
            "Esta parte debe poder agregarse despues de las otras partes.\n"
            f"Definiciones ya usadas: {', '.join(definiciones[-35:]) or '(ninguna)'}.\n"
            "Requisitos originales del usuario, sin reinterpretar:\n"
            + (("CORRIGE EL ERROR ANTERIOR SIN REPETIR CODIGO: " + str(estado.get("ultimo_gap"))[:130] + "\n")
               if str(estado.get("ultimo_gap") or "").startswith("CODA_") else "")
        )
        user = next((str(m.get("content") or "") for m in reversed(mensajes) if m.get("role") == "user"), "")
        peticion = [{"role": "user", "content":
            cabecera + "[INSTRUCCIONES ORIGINALES VERBATIM: objetivo global, NO son la cantidad de lineas de ESTA parte]\n"
            + user
            + "\n[FIN DEL INPUT ORIGINAL]\n"
            + ("CORRECCION DEL ULTIMO INTENTO: " + str(estado.get("ultimo_gap") or "")[:180] + "\n"
               if str(estado.get("ultimo_gap") or "").startswith("CODA_") else "")
            + f"ORDEN ACTUAL DE ESTA PARTE: escribe SOLO {pedir_lineas} lineas de Python; "
              "no 500 lineas ahora. Sin markdown, sin explicaciones, sin comentarios de relleno. "
              "Cierra todas las funciones y clases. Codigo solo."}]
        espera = max(0., float(estado.get("siguiente_llamada", 0)) - reloj())
        if espera:
            progreso(str(sum(len(x.splitlines()) for x in piezas)), "cuota: espera %.0fs" % espera)
            await dormir(espera)
        estado["intentos"] += 1
        if not await guardar(estado):
            raise RuntimeError("CODA_CHECKPOINT_NO_PERSISTIDO")
        progreso(str(sum(len(x.splitlines()) for x in piezas)), "generando parte %d" % (len(piezas) + 1))
        try:
            r = await inferir(peticion, min(1900, 550 + pedir_lineas * 17))
            texto = str(r.get("texto") or "")
            if r.get("tool_calls"):
                raise ValueError("CODA_TOOLS_INESPERADAS")
            ok, resultado, cuenta = _valida(texto, pedir_lineas, hashes)
            if not ok:
                raise ValueError("CODA_" + resultado + ": recibidas=" + str(cuenta)
                                 + " limite=" + str(pedir_lineas))
        except Exception as e:
            fallos += 1
            error = str(e)
            if not REINTENTABLE.search(error) and not error.startswith(("CODA_CANTIDAD", "CODA_SINTAXIS", "CODA_SEGMENTO", "CODA_FALTAN")):
                raise
            transitorio = bool(REINTENTABLE.search(error))
            # 429/503 pueden durar minutos: el horizonte de 1-4h pertenece
            # al motor, no a los tres reintentos de una llamada del proveedor.
            # No reintentar indefinidamente codigo rechazado sin variar entrada.
            if not transitorio and fallos >= 4:
                raise RuntimeError("CODA_CODIGO_INVALIDO_REPETIDO_CHECKPOINT_CONSERVADO: " + error[:150]) from None
            espera = (65 if modelo.startswith("groq/") else min(120, 10 * min(fallos, 12))) if transitorio else 4
            estado["siguiente_llamada"] = reloj() + espera
            estado["ultimo_gap"] = error[:150]
            if not await guardar(estado):
                raise RuntimeError("CODA_CHECKPOINT_NO_PERSISTIDO")
            continue
        fallos = 0
        piezas.append(resultado)
        hashes.add(hashlib.sha256(resultado.encode()).hexdigest())
        estado["piezas"] = piezas
        estado["siguiente_llamada"] = reloj() + (65 if modelo.startswith("groq/") else 0)
        estado["ultimo_gap"] = ""
        if not await guardar(estado):
            raise RuntimeError("CODA_CHECKPOINT_NO_PERSISTIDO")
        progreso(str(sum(len(x.splitlines()) for x in piezas)), "parte %d verificada por AST" % len(piezas))
    codigo = "\n".join(piezas) + "\n"
    try:
        ast.parse(codigo)
    except SyntaxError as e:
        raise RuntimeError("CODA_VALIDACION_GLOBAL_FALLO_CHECKPOINT_CONSERVADO") from e
    if len(codigo.splitlines()) != n_lineas:
        raise RuntimeError("CODA_LINEAS_INCORRECTAS_CHECKPOINT_CONSERVADO")
    estado["validacion"] = "PASS"
    if not await guardar(estado):
        raise RuntimeError("CODA_CHECKPOINT_NO_PERSISTIDO")
    return {"texto": codigo, "lineas": n_lineas, "partes": len(piezas), "desde_checkpoint": False,
            "sha256": hashlib.sha256(codigo.encode()).hexdigest()}