"""ROOM CONFERENCIAS: un turno en el que cada agente o modelo de la sala lee la conversacion y responde en el mismo chat."""
from mvp import modelos

MAX_POR_TURNO = 8
VENTANA = 20


def _tipo(control, nombre):
    if nombre in control.d["agentes"]:
        return "agente"
    try:
        modelos.validar(nombre)
        return "llm"
    except (ValueError, TypeError):
        return None


def _pedido(sala, nombre):
    charla = "\n".join(m["de"] + ": " + m["texto"] for m in sala["mensajes"][-VENTANA:])
    return ("Sala de conferencias '" + sala["nombre"] + "'. Eres " + nombre + ".\nContexto: " + (sala["contexto"] or "(ninguno)")
            + "\nConversacion:\n" + charla + "\n\nResponde con tu aporte, breve y sin repetir lo ya dicho.")


async def turno(control, delegar, banco, cuerpo):
    """Pide una respuesta a cada participante con escritura que sea agente o modelo; respeta los interruptores IA y Agentes del servidor."""
    sala = (await control.aplicar("salas", {"accion": "leer", "id": cuerpo.get("id")}, banco))["sala"]
    habladas, saltadas = [], []
    for nombre, nivel in list(sala["participantes"].items())[:MAX_POR_TURNO + 1]:
        tipo = _tipo(control, nombre)
        if nivel == "lectura" or not tipo:
            continue
        permitido, motivo = control.decidir(tipo)
        if not permitido:
            saltadas.append({"participante": nombre, "motivo": motivo}); continue
        args = {"nombre": nombre, "mensaje": _pedido(sala, nombre)} if tipo == "agente" else {"modelo": nombre, "mensaje": _pedido(sala, nombre)}
        texto = (await delegar(tipo, args))["texto"]
        await control.aplicar("salas", {"accion": "enviar", "id": sala["id"], "de": nombre, "texto": texto[:4000]}, banco)
        sala["mensajes"].append({"de": nombre, "texto": texto[:4000]})
        habladas.append(nombre)
    return {**await control.aplicar("salas", {"accion": "leer", "id": sala["id"]}, banco), "hablaron": habladas, "saltadas": saltadas}
