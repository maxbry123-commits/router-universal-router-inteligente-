#!/usr/bin/env python3
"""Puente al banco de claves de Groq/NVIDIA, sin variables de Hugging Face y sin tocar el Router MVP.
- LEE (solo lectura) el banco del Router (chat/backend/mvp/data/banco.bin, o RIU_BANCO_ROUTER) con la clave de acceso RIU_API_KEY.
- GUARDA las claves que le pegan al bridge en un banco PROPIO cifrado igual (BRIDGE_STATE_DIR/banco-swe.bin; esa carpeta ya se respalda en /data).
Reutiliza mvp.bank (misma cifra Fernet). Uso: claves_banco.py leer  |  claves_banco.py guardar  (JSON por stdin {groq, nvidia})  |  claves_banco.py borrar  (vacia el banco PROPIO; el del Router no se toca)."""
import json, re
import os, sys
from pathlib import Path


def _preparar_rutas():
    """El script se basta solo (no depende de PYTHONPATH): ubica `mvp` en router-mvp y en chat-router/chat/backend subiendo desde __file__ (o desde RIU_REPO_ROOT)."""
    aqui = Path(__file__).resolve()
    raices = [Path(os.environ["RIU_REPO_ROOT"])] if os.environ.get("RIU_REPO_ROOT") else [p for p in aqui.parents[:5]]
    for raiz in raices:
        for rel in (("router-mvp",), ("chat-router", "chat", "backend")):
            ruta = raiz.joinpath(*rel)
            if ruta.is_dir() and str(ruta) not in sys.path:
                sys.path.append(str(ruta))


_preparar_rutas()
from mvp import bank

PATRON = re.compile(r"(GROQ|NVIDIA)_API_KEY(_\d{1,2})?")
MAX = 20


def _acceso():
    return next((os.environ[v] for v in bank.ACCESO if os.environ.get(v)), "")


def _ruta_router():
    return os.environ.get("RIU_BANCO_ROUTER") or str(Path(__file__).resolve().parents[2] / "chat" / "backend" / "mvp" / "data" / "banco.bin")


def _ruta_propia():
    return os.path.join(os.environ.get("BRIDGE_STATE_DIR") or "./state", "banco-swe.bin")


def _candidatas():
    """Todas las variables de acceso definidas, sin repetir y en el orden de bank.ACCESO (el banco puede estar cifrado con cualquiera de ellas)."""
    return list(dict.fromkeys(os.environ[v] for v in bank.ACCESO if os.environ.get(v)))


def _abrir_con(ruta, crear=False):
    """(banco, clave con la que abrio) | (None, None). Cada candidata se prueba; si ninguna sirve, simplemente no aporta."""
    candidatas = _candidatas()
    if not candidatas or not (crear or os.path.exists(ruta)):
        return None, None
    for clave in candidatas:
        try:
            return bank.abrir(ruta, clave), clave
        except (ValueError, OSError):
            continue  # banco ilegible o clave distinta: se prueba la siguiente
    return None, None


def _abrir(ruta, crear=False):
    return _abrir_con(ruta, crear)[0]


def leer():
    out = {"groq": [], "nvidia": []}
    for ruta in (_ruta_router(), _ruta_propia()):
        b = _abrir(ruta)
        if not b:
            continue
        for nombre in b.nombres():
            m = PATRON.fullmatch(nombre)
            if m:
                lista = out[m.group(1).lower()]
                v = b.leer(nombre)
                if v and v not in lista and len(lista) < MAX:
                    lista.append(v)
    return out


def diagnostico():
    """Solo estado (existe, bytes, con que variable de acceso abre, cuantas claves): sirve para saber por que un banco no aporta, nunca devuelve valores."""
    out = {}
    for etiqueta, ruta in (("router", _ruta_router()), ("propio", _ruta_propia())):
        d = {"existe": os.path.exists(ruta), "bytes": os.path.getsize(ruta) if os.path.exists(ruta) else 0, "abre_con": None}
        if d["existe"]:
            for i, clave in enumerate(_candidatas()):
                try:
                    b = bank.abrir(ruta, clave)
                except (ValueError, OSError) as exc:
                    d["error"] = str(exc)[:60]
                    continue
                d["abre_con"] = i; d.pop("error", None)
                d["groq"] = sum(1 for n in b.nombres() if (m := PATRON.fullmatch(n)) and m.group(1) == "GROQ")
                d["nvidia"] = sum(1 for n in b.nombres() if (m := PATRON.fullmatch(n)) and m.group(1) == "NVIDIA")
                break
        out[etiqueta] = d
    out["accesos"] = len(_candidatas())
    return out


def guardar(claves):
    """Deja en el banco propio EXACTAMENTE las claves recibidas de cada proveedor presente en `claves`: las que ya no vienen se borran (no reaparecen).
    Un proveedor ausente no se toca; una lista vacia borra todas las de ese proveedor. Si hay algo que quitar, el banco se reescribe entero
    (archivo nuevo + os.replace, con la MISMA clave de acceso que lo cifro): bank.Banco no tiene borrar."""
    b, clave = _abrir_con(_ruta_propia(), crear=True)
    if not b:
        raise RuntimeError("sin clave de acceso (RIU_API_KEY): no se puede cifrar el banco propio")
    actual = {n: b.leer(n) for n in b.nombres()}
    queda = dict(actual)
    for prov, var in (("groq", "GROQ_API_KEY"), ("nvidia", "NVIDIA_API_KEY")):
        if prov not in (claves or {}):
            continue
        v = claves.get(prov)
        lista = [x.strip() for x in ([v] if isinstance(v, str) else v or []) if isinstance(x, str) and x.strip()][:MAX]
        for n in [n for n in queda if (m := PATRON.fullmatch(n)) and m.group(1) == prov.upper()]:
            del queda[n]
        for i, k in enumerate(lista):
            queda[var if i == 0 else "%s_%d" % (var, i)] = k
    if any(n not in queda for n in actual):  # algo se quita: reescritura completa
        nuevo = _ruta_propia() + ".nuevo-%d" % os.getpid()
        try:
            nb = bank.abrir(nuevo, clave)
            for n, v in queda.items():
                nb.guardar(n, v)
            os.replace(nuevo, _ruta_propia())
        finally:
            if os.path.lexists(nuevo):
                os.unlink(nuevo)
        return True
    for n, v in queda.items():
        if actual.get(n) != v:
            b.guardar(n, v)
    return True


# Registro extensible de claves para los DOS routers. El usuario solo agrega credenciales;
# usar un proveedor desconocido para inferencia requiere un adaptador, nunca se inventa.
_ID = re.compile(r"^[a-z][a-z0-9_-]{1,31}$")


def _resolver_proveedor(proveedor, secreto):
    p = str(proveedor or "auto").strip().lower()
    if p == "auto":
        p = "groq" if secreto.startswith("gsk_") else "nvidia" if secreto.startswith("nvapi-") else ""
    if not _ID.fullmatch(p):
        raise ValueError("PROVEEDOR_REQUERIDO")
    return p


def _reconstruir(queda, clave):
    """Actualizar de forma atomica el banco propio cifrado (sin tocar el Router ni HF)."""
    ruta = _ruta_propia()
    os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
    temporal = ruta + ".nuevo-%d" % os.getpid()
    try:
        nb = bank.abrir(temporal, clave)
        for n, v in queda.items():
            nb.guardar(n, v)
        os.replace(temporal, ruta)
    finally:
        if os.path.lexists(temporal):
            os.unlink(temporal)


def anadir(registro):
    secreto = registro.get("secret")
    if not isinstance(secreto, str) or not 8 <= len(secreto) <= 300 or any(x.isspace() for x in secreto):
        raise ValueError("CLAVE_INVALIDA")
    prov = _resolver_proveedor(registro.get("proveedor"), secreto)
    tipo = str(registro.get("tipo") or "api_key").lower()
    if tipo not in ("api_key", "sdk"):
        raise ValueError("TIPO_INVALIDO")
    b, cifrado = _abrir_con(_ruta_propia(), crear=True)
    if not b:
        raise RuntimeError("BANCO_NO_DISPONIBLE")
    datos = {k: b.leer(k) for k in b.nombres()}
    prefijo = (prov.upper() + "_API_KEY") if prov in ("groq", "nvidia") else ("SDK_" + prov.replace("-", "_").upper() + "_KEY")
    candidatos = [prefijo] + [prefijo + "_" + str(i) for i in range(1, MAX + 1)]
    actuales = [datos[n] for n in candidatos if n in datos]
    if secreto not in actuales:
        libre = next((n for n in candidatos if n not in datos), None)
        if libre is None:
            raise ValueError("MAXIMO_CLAVES")
        datos[libre] = secreto
        _reconstruir(datos, cifrado)
    return {"ok": True, "proveedor": prov, "tipo": tipo, "cantidad": len(set(actuales + [secreto])),
            "compatible": prov in ("groq", "nvidia")}


def catalogo():
    propios = _abrir(_ruta_propia())
    router = _abrir(_ruta_router())
    bancos = [b for b in (router, propios) if b]
    provs = {"groq": set(), "nvidia": set()}
    for b in bancos:
        for n in b.nombres():
            m = PATRON.fullmatch(n)
            if m and b.leer(n):
                provs[m.group(1).lower()].add(b.leer(n))
            elif n.startswith("SDK_") and "_KEY" in n:
                k = re.fullmatch(r"SDK_([A-Z][A-Z0-9_]*)_KEY(?:_\d{1,2})?", n)
                if k and b.leer(n):
                    provs.setdefault(k.group(1).lower(), set()).add(b.leer(n))
    return {"ok": True, "proveedores": [
        {"id": k, "cantidad": len(v), "compatible": k in ("groq", "nvidia"),
         "estado": "CONFIGURADO" if v else "SIN_CLAVES"}
        for k, v in sorted(provs.items())]}


def borrar():
    """Vacia el banco PROPIO (lo deja cifrado y vacio, para poder publicarlo asi); el banco del Router MVP nunca se toca."""
    ruta = _ruta_propia()
    if not _acceso():
        raise RuntimeError("sin clave de acceso (RIU_API_KEY): no se puede cifrar el banco propio")
    if os.path.lexists(ruta):
        os.unlink(ruta)
    return _abrir(ruta, crear=True) is not None


if __name__ == "__main__":
    try:
        if sys.argv[1:2] == ["leer"]:
            print(json.dumps(leer()))
        elif sys.argv[1:2] == ["guardar"]:
            guardar(json.loads(sys.stdin.read() or "{}")); print(json.dumps({"ok": True}))
        elif sys.argv[1:2] == ["diagnostico"]:
            print(json.dumps(diagnostico()))
        elif sys.argv[1:2] == ["catalogo"]:
            print(json.dumps(catalogo()))
        elif sys.argv[1:2] == ["anadir"]:
            print(json.dumps(anadir(json.loads(sys.stdin.read() or "{}"))))
        elif sys.argv[1:2] == ["borrar"]:
            borrar(); print(json.dumps({"ok": True}))
        else:
            sys.exit("uso: claves_banco.py leer | guardar | borrar")
    except Exception as exc:  # noqa: BLE001 - salida corta, sin valores
        print(json.dumps({"ok": False, "error": type(exc).__name__})); sys.exit(1)
