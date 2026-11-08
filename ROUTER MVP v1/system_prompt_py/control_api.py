from fastapi import FastAPI, HTTPException
from huggingface_hub import HfApi
import os
app = FastAPI()
api = HfApi(token=os.getenv("HF_TOKEN"))
@app.post("/control/{space_id}/pause")
async def pause_space(space_id: str):
    try:
        api.pause_space(repo_id=f"COMAND-CENTER-1/{space_id}")
        return {"status": "PAUSED", "space": space_id}
    except Exception as e: raise HTTPException(500, str(e))
@app.post("/control/{space_id}/restart")
async def restart_space(space_id: str):
    try:
        api.restart_space(repo_id=f"COMAND-CENTER-1/{space_id}", factory_reboot=False)
        return {"status": "RESTARTED", "space": space_id}
    except Exception as e: raise HTTPException(500, str(e))
@app.post("/control/{space_id}/sleep-time")
async def set_sleep_time(space_id: str, seconds: int = 900):
    try:
        api.set_space_sleep_time(repo_id=f"COMAND-CENTER-1/{space_id}", sleep_time=seconds)
        return {"status": "SLEEP_TIME_SET", "seconds": seconds}
    except Exception as e: raise HTTPException(500, str(e))
