# schema_validator.py
import json
from pydantic import BaseModel, ValidationError, Field
from typing import List, Optional

class LLMOutputSchema(BaseModel):
    """
    Contrato estricto de lo que el LLM debe devolver.
    Si falta un campo o el tipo es incorrecto, falla.
    """
    status: str = Field(..., description="Debe ser 'ok', 'completed' o 'success'")
    code: Optional[str] = Field(None, description="El código generado")
    tests: List[str] = Field(default_factory=list, description="Tests generados")
    reasoning: Optional[str] = Field(None, description="Explicación del modelo")

class SchemaValidationError(Exception):
    """Se lanza cuando el JSON del LLM no cumple el contrato."""
    pass

def validate_llm_output(raw_output: str) -> LLMOutputSchema:
    """
    Toma el string del LLM, limpia los bloques de Markdown y valida con Pydantic.
    """
    # 1. Limpieza de bloques Markdown
    stripped = raw_output.strip()
    if stripped.startswith("```"):
        parts = stripped.split("\n", 1)
        if len(parts) > 1:
            stripped = parts[1]
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()

    # 2. Parseo JSON
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError as e:
        raise SchemaValidationError(f"JSON malformado: {e}")

    # 3. Validación Pydantic
    try:
        validated = LLMOutputSchema(**parsed)
        if validated.status not in ("ok", "completed", "success"):
            raise SchemaValidationError(f"Status inválido: {validated.status}")
        return validated
    except ValidationError as e:
        raise SchemaValidationError(f"Esquema inválido: {e.json()}")
