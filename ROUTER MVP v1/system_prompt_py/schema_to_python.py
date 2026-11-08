import json
import hashlib
import subprocess
import os
import ast
import tempfile

class SchemaToPython:
    def __init__(self, output_dir="generated_code"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _hash(self, data: str) -> str:
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def _trace(self, input_hash: str, output_path: str, method: str):
        with open(output_path, "r", encoding="utf-8") as f:
            output_hash = self._hash(f.read())
        trace = {
            "input_hash": input_hash,
            "output_path": output_path,
            "output_hash": output_hash,
            "method": method
        }
        trace_path = output_path + ".trace.json"
        with open(trace_path, "w", encoding="utf-8") as f:
            json.dump(trace, f, indent=2)
        return trace_path

    def _safe_name(self, filename: str) -> str:
        base = os.path.basename(filename)
        if not base or base != filename or base.startswith("."):
            raise ValueError(f"Nombre de salida invalido: {filename}")
        return base

    def from_json_or_yaml(self, data_str: str, filename: str):
        name = self._safe_name(filename)
        input_hash = self._hash(data_str)
        output_path = os.path.join(self.output_dir, f"{name}.py")
        try:
            import yaml
            parsed = yaml.safe_load(data_str)
        except ImportError:
            parsed = json.loads(data_str)
        if not isinstance(parsed, (dict, list)):
            raise ValueError("La entrada debe ser un objeto o lista JSON/YAML")
        fd, temp_schema = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(parsed, f)
            subprocess.run([
                "datamodel-codegen",
                "--input", temp_schema,
                "--input-file-type", "json",
                "--output", output_path,
                "--output-model-type", "pydantic_v2.BaseModel"
            ], check=True)
        finally:
            os.unlink(temp_schema)
        return self._trace(input_hash, output_path, "datamodel-codegen:json")

    async def from_prose(self, prose: str, filename: str, llm_adapter):
        name = self._safe_name(filename)
        input_hash = self._hash(prose)
        prompt = (
            "[INSTRUCCIÓN]\n"
            "Convierte la siguiente descripción en código Python funcional.\n"
            'Responde ÚNICAMENTE con un JSON con la clave "code".\n'
            f"Descripción: {prose}\n"
        )
        response = await llm_adapter.generate_raw(prompt)
        code = json.loads(response, strict=False).get("code", "")
        try:
            ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Código generado inválido: {e}")
        output_path = os.path.join(self.output_dir, f"{name}.py")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(code)
        return self._trace(input_hash, output_path, "llm_prose")
