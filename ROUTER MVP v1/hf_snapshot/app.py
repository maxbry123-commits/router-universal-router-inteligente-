import os, uuid
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from search_engine import PerplexityMirrorEngine
from ecc_engine import ECCEngine
from agent_skills_engine import AgentSkillsEngine
from parallel_agent import run_parallel_agents
from rsi_controller import RSIController

app = FastAPI(title="Router v7 - Full Continuous System")

PLUGINS = {
    "groq": {"base_url": "https://api.groq.com/openai/v1", "api_key": os.getenv("GROQ_API_KEY", ""), "model": "llama3-70b-8192"},
    "nvidia": {"base_url": "https://integrate.api.nvidia.com/v1", "api_key": os.getenv("NVIDIA_API_KEY", ""), "model": "meta/llama3-70b-instruct"},
}

search_eng = PerplexityMirrorEngine()
ecc_eng = ECCEngine()
agent_eng = AgentSkillsEngine()

def require_auth(authorization: str = Header(None)):
    # FIX (bug del DAG v7): leia la cabecera `auth` en vez de `authorization` -> 401 siempre.
    if authorization != f"Bearer {os.getenv('ROUTER_API_KEY', 'dev')}": raise HTTPException(401, "Unauthorized")

class TaskRequest(BaseModel):
    task: str
    code_block: str = ""
    mode_hint: str = ""

@app.post("/v1/route")
async def route(req: TaskRequest, authorization: str = Header(None)):
    require_auth(authorization)
    session_id = uuid.uuid4().hex

    # 1. Investigación Pre-LLM
    context = search_eng.search_and_context(req.task)
    
    # 2. Anclaje de Skills
    combined_input = req.task + " " + req.code_block
    ecc_rules = ecc_eng.load_skills_for_input(combined_input)
    agent_rules = agent_eng.get_cascade_skills("codificacion")

    # 3. Prompt Inicial
    initial_prompt = f"""
    [REGLAS ECC]
    {ecc_rules}
    
    [REGLAS AGENTE]
    {agent_rules}
    
    {context}
    
    [CÓDIGO DEL USUARIO]
    {req.code_block}
    
    [TAREA]
    {req.task}
    """

    # 4. Configurar el Agente Paralelo como función de llamada
    plugins_to_race = {"groq": PLUGINS["groq"], "nvidia": PLUGINS["nvidia"]}
    
    async def call_parallel(prompt_text):
        winner, result = await run_parallel_agents(plugins_to_race, prompt_text)
        return result

    # 5. Iniciar Bucle de Trabajo Continuo (RSI)
    rsi = RSIController(max_iterations=5)
    final_output = await rsi.run_loop(call_parallel, initial_prompt)

    return {"session_id": session_id, "output": final_output}

@app.get("/health")
def health():
    return {"status": "ok", "engines": ["search", "ecc", "agent", "parallel", "rsi"]}
