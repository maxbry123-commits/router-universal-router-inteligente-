import httpx
import os
import web_search_tool

class ToolExecutor:
    def __init__(self):
        self.agent_url = os.getenv('AGENT_HARNESS_URL')
        if not self.agent_url:
            raise RuntimeError('FATAL: AGENT_HARNESS_URL no configurada. El router no puede ejecutar herramientas sin el Harness.')

    async def execute(self, tool_name: str, args: dict) -> dict:
        if tool_name == 'buscar_web':
            return await self._buscar_web(args)
        payload = {'tool': tool_name, 'args': args}
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.agent_url, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {'error': str(e), 'status': 'failed'}

    async def _buscar_web(self, args: dict) -> dict:
        query = str(args.get('query', '')).strip()
        if not query:
            return {'status': 'failed', 'error': 'query vacia'}
        try:
            results = await web_search_tool.search(query, max_results=5)
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
        if not results:
            return {'status': 'ok', 'query': query, 'results': [], 'pages': []}
        pages = []
        for r in results[:2]:
            text = await web_search_tool.fetch_text(r['url'])
            pages.append({'url': r['url'], 'title': r['title'], 'text': text})
        return {'status': 'ok', 'query': query, 'results': results, 'pages': pages}
