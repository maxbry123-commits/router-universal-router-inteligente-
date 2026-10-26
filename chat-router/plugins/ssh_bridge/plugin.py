"""ssh_bridge: transporte SSH del Router. Acciones: status (sin red), run, put, get.

Seguridad:
- Solo hosts/usuarios de config.json["hosts"] (lista blanca). Host desconocido -> denegado.
- run: solo comandos cuyo ejecutable este en allowed_commands del host y sin metacaracteres de shell;
  o cualquier comando si el host tiene allow_any_command=true EN config Y el payload trae allow_any=true.
- Credenciales SOLO por entorno: SSH_BRIDGE_KEY_<HOST> (PEM) o SSH_BRIDGE_PASSWORD_<HOST>. Nunca en archivos.
- Host key estricta (RejectPolicy) con SSH_BRIDGE_KNOWN_HOSTS (o known_hosts del sistema).
- Timeout y limite de salida; put/get solo archivos pequenos (max_file_bytes) bajo sftp_root.
- paramiko se importa de forma perezosa: si falta, status=degraded con motivo; el arranque no se rompe.
"""
from __future__ import annotations

import base64
import io
import json
import os
import posixpath
import re
import shlex
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
METACHARS = set(";|&$`<>(){}!*?") | {chr(10), chr(13)}


def _config() -> dict[str, Any]:
    try:
        cfg = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
        return cfg if isinstance(cfg, dict) else {}
    except (OSError, ValueError):
        return {}


def _paramiko():
    try:
        import paramiko  # noqa: PLC0415  (import perezoso)
        return paramiko, None
    except Exception as exc:
        return None, f"paramiko no disponible ({type(exc).__name__}); pip install paramiko"


def _env_name(host: str, kind: str) -> str:
    return f"SSH_BRIDGE_{kind}_" + re.sub(r"[^A-Za-z0-9]", "_", host).upper()


def _credential(host: str) -> tuple[str, str] | None:
    key = os.getenv(_env_name(host, "KEY"))
    if key:
        return "key", key
    pwd = os.getenv(_env_name(host, "PASSWORD"))
    if pwd:
        return "password", pwd
    return None


def _host_cfg(name: Any) -> tuple[dict[str, Any] | None, str | None]:
    hosts = _config().get("hosts") or {}
    if not isinstance(name, str) or name not in hosts or not isinstance(hosts[name], dict):
        return None, "host no esta en la lista blanca"
    cfg = hosts[name]
    if not cfg.get("host") or not cfg.get("user"):
        return None, "host mal configurado (falta host o user)"
    return cfg, None


def _connect(name: str, cfg: dict[str, Any]):
    """Devuelve (cliente paramiko conectado, error). Punto de inyeccion para pruebas."""
    pm, err = _paramiko()
    if pm is None:
        return None, err
    cred = _credential(name)
    if cred is None:
        return None, f"sin credencial: define {_env_name(name, 'KEY')} o {_env_name(name, 'PASSWORD')} en el entorno"
    client = pm.SSHClient()
    kh = os.getenv("SSH_BRIDGE_KNOWN_HOSTS")
    if kh:
        client.load_host_keys(kh)
    else:
        client.load_system_host_keys()
    client.set_missing_host_key_policy(pm.RejectPolicy())
    timeout = float(_config().get("timeout_s") or 20)
    kwargs: dict[str, Any] = {"hostname": cfg["host"], "port": int(cfg.get("port") or 22), "username": cfg["user"],
                              "timeout": timeout, "banner_timeout": timeout, "auth_timeout": timeout,
                              "allow_agent": False, "look_for_keys": False}
    if cred[0] == "key":
        pkey = None
        for cls in (pm.Ed25519Key, pm.RSAKey, pm.ECDSAKey):
            try:
                pkey = cls.from_private_key(io.StringIO(cred[1]))
                break
            except Exception:
                continue
        if pkey is None:
            return None, "clave privada en env no reconocida"
        kwargs["pkey"] = pkey
    else:
        kwargs["password"] = cred[1]
    try:
        client.connect(**kwargs)
    except Exception as exc:
        return None, f"conexion fallida: {type(exc).__name__}"
    return client, None


def _command_allowed(cmd: Any, cfg: dict[str, Any], want_any: bool) -> str | None:
    if not isinstance(cmd, str) or not cmd.strip():
        return "command vacio"
    if want_any:
        if cfg.get("allow_any_command") is True:
            return None
        return "allow_any pedido pero el host no lo habilita en config"
    if METACHARS & set(cmd):
        return "metacaracteres de shell no permitidos en modo lista"
    try:
        argv = shlex.split(cmd)
    except ValueError:
        return "comando mal formado"
    if not argv or argv[0] not in (cfg.get("allowed_commands") or []):
        return "comando fuera de la lista permitida"
    return None


def _read_capped(stream, cap: int, deadline: float) -> tuple[bytes, bool]:
    buf, truncated = b"", False
    while time.monotonic() < deadline:
        chunk = stream.read(min(4096, cap + 1 - len(buf)))
        if not chunk:
            break
        buf += chunk
        if len(buf) > cap:
            return buf[:cap], True
    return buf, truncated


def _run(p: dict[str, Any]) -> dict[str, Any]:
    cfg, err = _host_cfg(p.get("host"))
    if cfg is None:
        return {"status": "denied", "reason": err}
    why = _command_allowed(p.get("command"), cfg, p.get("allow_any") is True)
    if why:
        return {"status": "denied", "reason": why}
    client, err = _connect(p["host"], cfg)
    if client is None:
        return {"status": "degraded", "reason": err}
    timeout = float(_config().get("timeout_s") or 20)
    cap = int(_config().get("max_output_bytes") or 65536)
    try:
        _in, out, errs = client.exec_command(p["command"], timeout=timeout)
        deadline = time.monotonic() + timeout
        o, ot = _read_capped(out, cap, deadline)
        e, et = _read_capped(errs, cap, deadline)
        code = out.channel.recv_exit_status() if out.channel.exit_status_ready() else None
        return {"status": "ok" if code == 0 else "degraded", "exit_code": code,
                "stdout": o.decode("utf-8", "replace"), "stderr": e.decode("utf-8", "replace"),
                "truncated": ot or et}
    except Exception as exc:
        return {"status": "degraded", "reason": f"ejecucion fallida: {type(exc).__name__}"}
    finally:
        client.close()


def _safe_path(path: Any, cfg: dict[str, Any]) -> tuple[str | None, str | None]:
    root = cfg.get("sftp_root")
    if not root:
        return None, "host sin sftp_root: put/get deshabilitado"
    if not isinstance(path, str) or not path:
        return None, "path vacio"
    full = posixpath.normpath(posixpath.join(root, path))
    if full != posixpath.normpath(root) and not full.startswith(posixpath.normpath(root) + "/"):
        return None, "path fuera de sftp_root"
    return full, None


def _transfer(action: str, p: dict[str, Any]) -> dict[str, Any]:
    cfg, err = _host_cfg(p.get("host"))
    if cfg is None:
        return {"status": "denied", "reason": err}
    full, err = _safe_path(p.get("path"), cfg)
    if full is None:
        return {"status": "denied", "reason": err}
    limit = int(_config().get("max_file_bytes") or 65536)
    data = b""
    if action == "put":
        try:
            data = base64.b64decode(p.get("content_b64") or "", validate=True)
        except Exception:
            return {"status": "denied", "reason": "content_b64 invalido"}
        if len(data) > limit:
            return {"status": "denied", "reason": f"archivo > {limit} bytes"}
    client, err = _connect(p["host"], cfg)
    if client is None:
        return {"status": "degraded", "reason": err}
    try:
        sftp = client.open_sftp()
        if action == "put":
            with sftp.file(full, "wb") as fh:
                fh.write(data)
            return {"status": "ok", "bytes": len(data), "path": full}
        if sftp.stat(full).st_size > limit:
            return {"status": "denied", "reason": f"archivo remoto > {limit} bytes"}
        with sftp.file(full, "rb") as fh:
            data = fh.read(limit + 1)
        return {"status": "ok", "bytes": len(data), "path": full, "content_b64": base64.b64encode(data).decode()}
    except Exception as exc:
        return {"status": "degraded", "reason": f"sftp fallido: {type(exc).__name__}"}
    finally:
        client.close()


def status() -> dict[str, Any]:
    """Sin red: configuracion + disponibilidad de paramiko + credenciales presentes."""
    hosts = _config().get("hosts") or {}
    if not hosts:
        return {"status": "off", "reason": "sin hosts en la lista blanca", "hosts": {}}
    pm, err = _paramiko()
    detail = {h: {"credencial": bool(_credential(h)), "sftp": bool((c or {}).get("sftp_root"))} for h, c in hosts.items()}
    if pm is None:
        return {"status": "degraded", "reason": err, "hosts": detail}
    missing = [h for h, d in detail.items() if not d["credencial"]]
    if missing:
        return {"status": "degraded", "reason": "sin credencial en env para: " + ", ".join(missing), "hosts": detail}
    return {"status": "ok", "hosts": detail}


def handle(action: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    p = payload if isinstance(payload, dict) else {}
    if action == "status":
        return status()
    if action == "run":
        return _run(p)
    if action in ("put", "get"):
        return _transfer(action, p)
    return {"status": "degraded", "reason": "accion desconocida"}
