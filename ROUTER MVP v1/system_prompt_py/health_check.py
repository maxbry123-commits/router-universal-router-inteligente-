import httpx
import asyncio

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

try:
    from external.core.space_inventory import all_spaces
    SPACES = list(all_spaces())
except ImportError:  # pragma: no cover
    SPACES = [
        "local-llm-router", "local-llm-router-v2", "local-llm-router-v7",
        "swe-code-s1", "swe-code-s2", "swe-code-s3",
    ]

async def check_space(space_name):
    url = f"https://comand-center-1-{space_name}.hf.space/health"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url)
            return space_name, r.status_code == 200
    except:
        return space_name, False

async def run_healthcheck():
    results = await asyncio.gather(*(check_space(s) for s in SPACES))
    for name, status in results:
        print(f"[{name}] {'ONLINE' if status else 'OFFLINE'}")
    return all(status for _, status in results)

if __name__ == "__main__":
    asyncio.run(run_healthcheck())
