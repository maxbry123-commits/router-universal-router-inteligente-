from pydantic import BaseModel, ValidationError
from typing import Dict, Any

class ToolArgumentValidator:
    def __init__(self, schemas: Dict[str, type[BaseModel]]):
        self.schemas = schemas

    def validate(self, tool_name: str, arguments: Dict[str, Any]) -> tuple[bool, str]:
        schema = self.schemas.get(tool_name)
        if not schema:
            return False, f'Herramienta desconocida: {tool_name}'
        try:
            schema(**arguments)
            return True, ''
        except ValidationError as e:
            return False, e.json()
