"""Runner del SDK OpenHands (openhands-software-agent-sdk): se ejecuta SOLO como subproceso por openhands.py con el Python que tiene el SDK.
Lee JSON por stdin {modelo, base_url, prompt, directorio, escritura, ejecucion}; la clave llega por RIU_AGENTE_LLM_KEY. Imprime una ultima linea JSON.
API segun el README del SDK: LLM, Agent, Conversation, Tool, TerminalTool, FileEditorTool, TaskTrackerTool."""
import json
import os
import sys


def main():
    datos = json.loads(sys.stdin.read())
    try:
        from openhands.sdk import LLM, Agent, Conversation, Tool
        from openhands.sdk.conversation.response_utils import get_agent_final_response
        from openhands.tools.file_editor import FileEditorTool
        from openhands.tools.task_tracker import TaskTrackerTool
        from openhands.tools.terminal import TerminalTool
        llm = LLM(model=datos["modelo"], base_url=datos["base_url"], api_key=os.environ["RIU_AGENTE_LLM_KEY"])
        herramientas = [Tool(name=TaskTrackerTool.name)]
        if datos.get("escritura"):
            herramientas.append(Tool(name=FileEditorTool.name))
        if datos.get("ejecucion"):
            herramientas.append(Tool(name=TerminalTool.name))
        conversacion = Conversation(agent=Agent(llm=llm, tools=herramientas), workspace=datos["directorio"])
        conversacion.send_message(datos["prompt"])
        conversacion.run()
        estado = getattr(conversacion.state.execution_status, "value", str(conversacion.state.execution_status))
        eventos = list(conversacion.state.events)
        usadas = sorted({getattr(e, "tool_name", None) for e in eventos if getattr(e, "tool_name", None)})
        if estado != "finished":
            print(json.dumps({"ok": False, "codigo": "OPENHANDS_ESTADO", "error": "la conversacion termino en estado " + estado, "estado": estado}))
            return 0
        print(json.dumps({"ok": True, "resultado": get_agent_final_response(eventos), "estado": estado, "herramientas": usadas, "eventos": len(eventos)}))
        return 0
    except Exception as exc:  # noqa: BLE001 - se informa el tipo, no el contenido (puede traer claves)
        print(json.dumps({"ok": False, "codigo": "OPENHANDS_EXCEPCION", "error": type(exc).__name__}))
        return 0


if __name__ == "__main__":
    sys.exit(main())
