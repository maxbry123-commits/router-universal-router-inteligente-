import json
import re
from typing import List, Dict

class ModelFormatAdapter:
    @staticmethod
    def parse(model: str, text: str) -> List[Dict]:
        if not text:
            return []
        m = model.lower()
        if "qwen2.5" in m or "qwen2" in m:
            return ModelFormatAdapter._parse_qwen25(text)
        elif "qwen3.5" in m or "qwen3" in m:
            return ModelFormatAdapter._parse_qwen35(text)
        elif "lfm2.5" in m or "lfm2" in m:
            return ModelFormatAdapter._parse_lfm25(text)
        return []

    @staticmethod
    def _parse_qwen25(text: str) -> List[Dict]:
        matches = re.findall(r'<tool_call>\s*(.*?)\s*</tool_call>', text, re.DOTALL)
        results = []
        for m in matches:
            try:
                data = json.loads(m)
                results.append({"name": data.get("name"), "arguments": json.dumps(data.get("arguments", {}))})
            except json.JSONDecodeError:
                pass
        return results

    @staticmethod
    def _parse_qwen35(text: str) -> List[Dict]:
        results = []
        for match in re.finditer(r'<tool_call>\s*<function=(\w+)>\s*(.*?)\s*</function>\s*</tool_call>', text, re.DOTALL):
            name = match.group(1)
            args_str = match.group(2)
            args = {}
            for param in re.finditer(r'<parameter=(\w+)>\s*(.*?)\s*</parameter>', args_str, re.DOTALL):
                args[param.group(1)] = param.group(2).strip()
            results.append({"name": name, "arguments": json.dumps(args)})
        return results

    @staticmethod
    def _parse_lfm25(text: str) -> List[Dict]:
        results = []
        for match in re.finditer(r'<\|tool_call_start\|>\s*(.*?)\s*<\|tool_call_end\|>', text, re.DOTALL):
            code = match.group(1).strip()
            fn_match = re.search(r'(\w+)\((.*)\)', code)
            if fn_match:
                name = fn_match.group(1)
                results.append({"name": name, "arguments": json.dumps({"raw_pythonic": fn_match.group(2)})})
        return results
