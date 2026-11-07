from sentence_transformers import SentenceTransformer, util
class PerplexityMirrorEngine:
    def __init__(self):
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
    def search_and_context(self, task: str) -> str:
        chunks = []
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(task, max_results=3))
                chunks = [r.get("body", "") for r in results]
        except: pass

        if not chunks:
            return "### CONTEXTO VACÍO - NO INVENTES"

        # FIX (bug del DAG v7): este bloque estaba indentado dentro de `if not chunks:` y despues
        # del return, o sea era codigo muerto: con resultados de DDGS la funcion devolvia None.
        task_emb = self.embedder.encode(task, convert_to_tensor=True)
        chunk_embs = self.embedder.encode(chunks, convert_to_tensor=True)
        scores = util.cos_sim(task_emb, chunk_embs)[0]
        scored = sorted(zip(scores.tolist(), chunks), reverse=True)
        best = [c for score, c in scored[:2] if score > 0.3]

        context = "### CONTEXTO DE INVESTIGACIÓN\n\n"
        for i, c in enumerate(best, 1):
            context += f"**[Fuente {i}]**\n{c[:1000]}\n\n"
        return context
