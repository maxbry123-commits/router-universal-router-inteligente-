from fastapi import FastAPI, HTTPException, Header
from huggingface_hub import HfApi
import os

app = FastAPI()
api = HfApi(token=os.getenv("HF_TOKEN"))
ROUTER_API_KEY = os.getenv("ROUTER_API_KEY", "dev_key")

def verify_key(x_api_key: str = Header(None)):
    if x_api_key != ROUTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

@app.post("/control/{space_id}/pause")
async def pause_space(space_id: str, x_api_key: str = Header(None)):
    verify_key(x_api_key)
    api.pause_space(repo_id=f"COMAND-CENTER-1/{space_id}")
    return {"status": "PAUSED"}

@app.post("/control/{space_id}/restart")
async def restart_space(space_id: str, x_api_key: str = Header(None)):
    verify_key(x_api_key)
    api.restart_space(repo_id=f"COMAND-CENTER-1/{space_id}", factory_reboot=False)
    return {"status": "RESTARTED"}

@app.post("/control/{space_id}/sleep-time")
async def set_sleep_time(space_id: str, seconds: int = 900, x_api_key: str = Header(None)):
    verify_key(x_api_key)
    api.set_space_sleep_time(repo_id=f"COMAND-CENTER-1/{space_id}", sleep_time=seconds)
    return {"status": "SLEEP_TIME_SET"}
