import httpx
import asyncio

SPACES = [
    "swe-code-s1", "swe-code-s2", "swe-code-s3",
    "riu-router", "claude-github-mcp-backup", "swe-code-web"
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
