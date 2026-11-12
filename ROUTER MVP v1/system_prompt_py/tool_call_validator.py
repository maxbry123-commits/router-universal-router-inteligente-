import json
import ast

class ToolCallValidator:
    @staticmethod
    def validate(response_text: str) -> dict:
        stripped = response_text.strip()
        if stripped.startswith('```json'):
            stripped = stripped.split('```json')[1].split('```')[0].strip()
        elif stripped.startswith('```'):
            stripped = stripped.split('```')[1].split('```')[0].strip()
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            return {'type': 'text', 'content': response_text}

        if 'tool' in data and 'args' in data:
            return {'type': 'tool_call', 'tool': data['tool'], 'args': data['args']}
        if 'code' in data:
            try:
                ast.parse(data['code'])
                return {'type': 'code', 'code': data['code'], 'tests': data.get('tests', '')}
            except SyntaxError as e:
                return {'type': 'error', 'message': f'Sintaxis invalida: {e}'}
        return {'type': 'json', 'data': data}
