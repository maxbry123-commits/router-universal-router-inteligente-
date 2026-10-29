"""X-RAY Chatbot Prototype v1.0
Contrato: crear_sesion | agregar_mensaje | fijar_ancla | activar_toggles | agregar_checklist | marcar_checklist | construir_payload | serializar
Stack: Python 3 stdlib. Estado en memoria. Serialización JSON. Validación defensiva.
"""
import json
import time
import uuid
from typing import List, Dict, Any, Optional

# ---------------------------------------------------------------------------
# Gestión de Estado Interno (Memoria única para el prototipo)
# ---------------------------------------------------------------------------
_state_registry: Dict[str, Dict[str, Any]] = {}
_current_sid: str = "init_default"

def _ensure_session(sid: str) -> Dict[str, Any]:
    """Valida tipo y crea estructura base si no existe."""
    if not isinstance(sid, str) or len(sid.strip()) < 1:
        raise ValueError("ID de sesión debe ser cadena no vacía.")
    sid = sid.strip()
    if sid not in _state_registry:
        _state_registry[sid] = {
            "msgs": [],
            "anc": [],       # {"id": str, "txt": str, "on": bool}
            "chk": [],       # {"id": str, "txt": str, "done": bool}
            "tog": {
                "tools": False,
                "agente_tool": False,
                "llm_tool": False
            }
        }
    return _state_registry[sid]

def get_current() -> Dict[str, Any]:
    """Retorna estado actual o inicializa por defecto."""
    if _current_sid not in _state_registry:
        crear_sesion(_current_sid)
    return _state_registry[_current_sid]

# ---------------------------------------------------------------------------
# Contrato Público (Backend API)
# ---------------------------------------------------------------------------
def crear_sesion(sid: str) -> Dict[str, Any]:
    """Inicializa o reinicia una sesión. Retorna snapshot."""
    global _current_sid
    _current_sid = sid
    st = _ensure_session(sid)
    return {
        "sid": _current_sid,
        "status": "ready",
        "ts": time.time()
    }

def agregar_mensaje(contenido: str, remitente: str = "user") -> Dict[str, Any]:
    """Añade mensaje validando longitud y tipo. Refleja al instante."""
    if not isinstance(contenido, str):
        raise TypeError("El contenido debe ser string.")
    txt = contenido.strip()
    if len(txt) == 0:
        raise ValueError("El mensaje no puede estar vacío.")
    
    st = get_current()
    entry = {
        "uid": uuid.uuid4().hex[:8],
        "role": "system" if remitente.lower() in ("admin", "bot") else "user",
        "text": txt,
        "ts": time.time()
    }
    st["msgs"].append(entry)
    return entry

def fijar_ancla(ancla_id: str, texto: str, activo: bool) -> None:
    """Activa/desactiva o crea un ancla. Sincronización inmediata."""
    if not ancla_id or not isinstance(texto, str):
        raise ValueError("ID y texto requeridos para ancla.")
    st = get_current()
    for idx, anc in enumerate(st["anc"]):
        if anc["id"] == ancla_id:
            st["anc"][idx]["on"] = bool(activo)
            return
    st["anc"].append({"id": ancla_id, "txt": texto, "on": bool(activo)})

def activar_toggles(tools: bool = False, agente_tool: bool = False, llm_tool: bool = False) -> None:
    """Banderas independientes. Solo booleans permitidos."""
    st = get_current()
    st["tog"]["tools"] = bool(tools)
    st["tog"]["agente_tool"] = bool(agente_tool)
    st["tog"]["llm_tool"] = bool(llm_tool)

def agregar_checklist_item(texto: str) -> None:
    """Agrega tarea pendiente con ID auto-generado."""
    if not texto.strip():
        raise ValueError("Texto de tarea obligatorio.")
    st = get_current()
    st["chk"].append({
        "id": f"t_{uuid.uuid4().hex[:6]}",
        "txt": texto.strip(),
        "done": False
    })

def marcar_checklist(item_id: str, hecho: bool = False) -> None:
    """Cambia estado 'done' de una tarea específica."""
    st = get_current()
    found = False
    for item in st["chk"]:
        if item["id"] == item_id:
            item["done"] = bool(hecho)
            found = True
            break
    if not found:
        raise KeyError(f"Checkpoint '{item_id}' no encontrado.")

def construir_payload() -> str:
    """
    Serializa estado final respetando contrato:
    - Excluye anclas OFF.
    - Conserva historial completo.
    - Incluye tareas pendientes (no hechas).
    - Banderas actualizadas.
    """
    st = get_current()
    
    # Filtro defensivo de anclas activas
    activos = [a for a in st["anc"] if a.get("on", False)]
    # Filtro defensivo de checklist pendientes
    pendientes = [{"id": i["id"], "texto": i["txt"]} for i in st["chk"] if not i.get("done", False)]
    
    esquema_valido = {
        "session": _current_sid,
        "history_len": len(st["msgs"]),
        "history": st["msgs"],
        "anchora_activo": activos,
        "pendientes": pendientes,
        "flags": {k: bool(v) for k, v in st["tog"].items()}
    }
    
    try:
        raw = json.dumps(esquema_valido, ensure_ascii=False, indent=2)
        # Validación cruzada de round-trip
        json.loads(raw)
        return raw
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Serialización fallida: {e}")

def serializar_estado(salida: str = "json") -> str:
    """Wrapper para exportar estado crudo si fuera necesario."""
    return construir_payload()

# ---------------------------------------------------------------------------
# Tests Manuales Embebidos (Ejecutar con python xray_chatbot.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("[INIT] Creando sesión prueba_xray...")
    assert isinstance(crear_sesion("prueba_xray"), dict)
    
    print("[MSG] Agregando mensajes...")
    agregar_mensaje("Inicio de chat X-Ray", "admin")
    agregar_mensaje("Validando filtros defensivos.", "user")
    
    print([ANCHOR] Configurando contextos...")
    fijar_ancla("ctx_db", "Query SQL Optimizada", True)
    fijar_ancla("ctx_api", "Endpoint RESTv2", False)
    fijar_ancla("ctx_mem", "Buffer Cache Activo", True)
    
    print("[TOG] Activando herramientas...")
    activar_toggles(tools=True, agente_tool=True, llm_tool=False)
    
    print("[CHK] Lista de verificación...")
    agregar_checklist_item("Depurar lógica de anclas")
    agregar_checklist_item("Verificar serialización JSON")
    marcar_checklist("t_*", False) # Demostración de paso
    
    print("[PAYLOAD] Construyendo respuesta final...")
    pay = construir_payload()
    datos = json.loads(pay)
    
    # Validaciones críticas post-construcción
    assert len(datos["anchora_activo"]) == 2, "Deben quedarse solo las ON"
    assert any(x["txt"] == "Query SQL Optimizada" for x in datos["anchora_activo"])
    assert datos["flags"]["tools"] is True
    assert datos["flags"]["llm_tool"] is False
    assert datos["history_len"] == 2
    
    print(f"[OK] Payload válido:\n{pay}")
    print(">>> PRUEBAS AUTOMÁTAS COMPLETADAS <<<")