import httpx
import os

class ToolExecutor:
    def __init__(self):
        self.agent_url = os.getenv('AGENT_HARNESS_URL')
        if not self.agent_url:
            raise RuntimeError('FATAL: AGENT_HARNESS_URL no configurada. El router no puede ejecutar herramientas sin el Harness.')

    async def execute(self, tool_name: str, args: dict) -> dict:
        payload = {'tool': tool_name, 'args': args}
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.agent_url, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {'error': str(e), 'status': 'failed'}
