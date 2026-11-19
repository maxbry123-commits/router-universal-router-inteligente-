"""prefijo_canonico.py — Prefijo de sistema FIJO por modo (para el KV prefix cache).

MEDIDO en el Space real (0.8B, 8 vCPU, 2026-11-19):
  · 1a llamada con el prefijo (frio):   3,95 s  (993 tokens de prompt)
  · 2a llamada con el MISMO prefijo:    0,29 s   -> 93 % de ahorro
  · 3a con otro prefijo (frio otra vez): 2,15 s
  · 4a con el prefijo A otra vez:        0,33 s   (la cache persiste)

llama-server reutiliza el KV del prefijo si los tokens son IDENTICOS byte a byte.
Por eso el prefijo debe ser canonico: mismo texto para el mismo modo, sin
timestamps, sin ids de peticion y sin datos variables.

Efecto en el chat: la primera peticion de cada modo paga el prefill; todas las
siguientes del mismo modo (el bucle agentico repite el contexto) van casi gratis.
"""

BASE = (
    "Eres el motor del router YAIWES: 3 modelos GGUF locales (0.5B, 350M, 0.8B) servidos "
    "por llama.cpp en CPU. Reglas fijas: responde en espanol salvo que pidan otro idioma; "
    "codigo Python con tipado, funciones pequenas y docstring; no inventes APIs ni ficheros "
    "que no hayan sido citados; si no sabes algo, dilo en una linea; no repitas la pregunta; "
    "cierra con un bloque de codigo copiable cuando la respuesta sea codigo."
)

MODOS = {
    "code_generate": BASE + " Ahora: escribe codigo nuevo que funcione, con un ejemplo de uso.",
    "code_debug": BASE + " Ahora: localiza la causa raiz del fallo antes de proponer el arreglo, y explica por que funciona.",
    "code_review": BASE + " Ahora: revisa el codigo dado, lista los problemas por gravedad y remata con el parche minimo.",
    "code_refactor": BASE + " Ahora: refactoriza sin cambiar el comportamiento y justifica cada cambio.",
    "verification": BASE + " Ahora: verifica con datos: di que se comprueba, como se comprueba y cual es el resultado esperado.",
    "architecture": BASE + " Ahora: propone la arquitectura con sus piezas, sus limites y el orden de construccion.",
    "docstring": BASE + " Ahora: documenta con docstring estilo Google: descripcion, argumentos, valor de retorno y excepciones.",
    "documentation": BASE + " Ahora: escribe la documentacion clara y breve, con un ejemplo.",
    "tool_call": BASE + " Ahora: responde solo con la llamada de herramienta en JSON valido, sin texto alrededor.",
    "agentic_tool": BASE + " Ahora: planifica en pasos cortos, eliges la herramienta y terminas con el resultado.",
    "planning": BASE + " Ahora: das el plan en pasos ordenados, con la dependencia entre ellos y el primer paso ejecutable.",
    "reasoning": BASE + " Ahora: razonas paso a paso, con la conclusion al final.",
    "3d_code": BASE + " Ahora: escribes el codigo de la escena 3D (geometria, materiales, camara y bucle de render).",
}

GENERICO = BASE


def prefijo_para(modo) -> str:
    """Texto canonico del modo (mismo string byte a byte para el mismo modo)."""
    if not modo:
        return GENERICO
    return MODOS.get(str(modo).strip().lower(), GENERICO)


def construir(mensajes, modo):
    """Devuelve los mensajes con el prefijo canonico delante (si el cliente no trae uno).

    No toca el orden del resto: el prefijo va SIEMPRE el primero para que el
    bloque de KV sea identico entre llamadas del mismo modo.
    """
    if not isinstance(mensajes, list) or not mensajes:
        return mensajes
    for m in mensajes:
        if isinstance(m, dict) and str(m.get("role") or "").lower() == "system":
            return mensajes          # el cliente manda su propio prefijo: no se toca
    prefijo = prefijo_para(modo)
    return [{"role": "system", "content": prefijo}] + list(mensajes)
