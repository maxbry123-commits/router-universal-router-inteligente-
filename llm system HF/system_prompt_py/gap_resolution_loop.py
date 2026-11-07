# gap_resolution_loop.py
import re
from typing import Callable, Optional
from web_search_tool import WebSearchTool

class GapBlockedError(Exception):
    """Se lanza cuando el gap es bloqueante (no se puede resolver con búsqueda)."""
    pass

class GapResolutionLoop:
    """
    Bucle de resolución de gaps.
    Recibe el gap del modelo, busca en la web (sin LLM) y devuelve el contexto.
    Repite hasta resolver o agotar max_rounds.
    """
    # Palabras que indican un gap bloqueante (no se resuelve buscando en web)
    BLOCKING_KEYWORDS = ["API_KEY_MISSING", "PERMISSION_DENIED", "BILLING_REQUIRED", "NO_INTERNET"]

    def __init__(self, max_rounds: int = 5, search_tool: Optional[WebSearchTool] = None):
        self.max_rounds = max_rounds
        self.search_tool = search_tool or WebSearchTool()
        self.history = []

    def detect_gap(self, model_output: str) -> Optional[str]:
        """
        Extrae el gap de la respuesta del modelo.
        Soporta formatos: 'GAP_DETECTADO: <motivo>' o 'GAP: <motivo>'.
        """
        match = re.search(r"GAP(?:_DETECTADO)?:\s*(.+)", model_output, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def is_blocking(self, gap: str) -> bool:
        """Determina si el gap es bloqueante (no se resuelve con búsqueda)."""
        return any(kw in gap.upper() for kw in self.BLOCKING_KEYWORDS)

    def resolve(self, gap: str) -> str:
        """
        Resuelve un gap buscando en la web.
        Devuelve el contexto en Markdown.
        """
        self.history.append({"gap": gap, "round": len(self.history) + 1})
        return self.search_tool.search(gap)

    def run_with_loop(self, model_call_fn: Callable[[str], str], initial_prompt: str) -> str:
        """
        Bucle completo:
        1. Llama al modelo con el prompt actual.
        2. Si hay gap, busca contexto y añade al prompt.
        3. Repite hasta max_rounds o hasta que no haya gap.
        """
        current_prompt = initial_prompt

        for round_num in range(1, self.max_rounds + 1):
            print(f"🔄 Ronda {round_num}/{self.max_rounds}")
            model_output = model_call_fn(current_prompt)

            gap = self.detect_gap(model_output)
            if not gap:
                print("✅ No hay gap. Fin del bucle.")
                return model_output

            if self.is_blocking(gap):
                raise GapBlockedError(f"Gap bloqueante detectado: {gap}")

            print(f"🔍 Gap detectado: {gap}. Buscando contexto...")
            context = self.resolve(gap)

            # Inyectar el contexto recuperado en el prompt para la siguiente ronda
            current_prompt = f"""
[CONTEXTO RECUPERADO PARA RESOLVER EL GAP]
{context}

[INSTRUCCIÓN]
Usa el contexto anterior para resolver el gap: "{gap}".
Si aún falta información, reporta otro GAP_DETECTADO. Si no, termina con TERMINADO.
"""

        # Si agotamos las rondas, devolvemos el último output con advertencia
        return f"[ADVERTENCIA: MÁXIMO DE RONDAS ALCANZADO]\n{model_output}"
