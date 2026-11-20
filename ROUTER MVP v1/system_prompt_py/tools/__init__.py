from workflow_tools import TOOL_SCHEMAS as WORKFLOW_SCHEMAS
import motor_descarga as _md

BUSCAR_WEB = {"type": "function", "function": {"name": "buscar_web", "description": "Busca en la web y devuelve fuentes fiables con su contenido.",
    "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}

DESCARGAR = {"type": "function", "function": {"name": "descargar_componente", "description": "Descarga un repositorio público a componentes (solo descarga, nunca ejecuta).",
    "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "tipo": {"type": "string", "enum": ["skills", "componentes"]}}, "required": ["url", "tipo"]}}}

BUSCAR_COMPONENTES = {"type": "function", "function": {"name": "buscar_componentes", "description": "Busca candidatos en GitHub o Hugging Face sin LLM.",
    "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "fuente": {"type": "string", "enum": ["github", "huggingface"]}}, "required": ["query", "fuente"]}}}

def esquemas() -> list:
    from agentes import TOOL_SCHEMA as AGENTE
    return [BUSCAR_WEB, BUSCAR_COMPONENTES, DESCARGAR, AGENTE, *WORKFLOW_SCHEMAS]

def nombres() -> set:
    return {e["function"]["name"] for e in esquemas()}
