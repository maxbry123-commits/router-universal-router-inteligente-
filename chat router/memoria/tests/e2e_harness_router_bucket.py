# E2E real (no pytest): MCP stdio (protocolo del harness) -> Router -> HF bucket -> Router nuevo restaura. Requiere HF_TOKEN y /vercel/start_router.sh equivalente.
import asyncio, os, subprocess, json, time, sqlite3, tempfile, uuid
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from huggingface_hub import HfFileSystem
REPO='/vercel/repo'
SRV=StdioServerParameters(command='python3', args=['chat router/harness plugins/memoria/memoria_mcp_server.py'], cwd=REPO,
    env={**os.environ, 'RIU_ROUTER_URL':'http://127.0.0.1:8000', 'RIU_API_KEY':'k-opus-test'})
def start(d):
    subprocess.run(['/vercel/start_router.sh'], env={**os.environ,'RIU_DATA_DIR':d}, check=True)
def text(r): return r.content[0].text if r.content else str(r)
async def tool(name,args={}):
    async with stdio_client(SRV) as (rd,wr):
        async with ClientSession(rd,wr) as s:
            await s.initialize()
            if name=='__list__': return [t.name for t in (await s.list_tools()).tools]
            return text(await s.call_tool(name,args))
async def main():
    marker='e2e-'+uuid.uuid4().hex[:8]
    os.system('rm -rf /tmp/riuA /tmp/riuB')
    start('/tmp/riuA')
    print('1 TOOLS', await tool('__list__'))
    print('2 RESTORE_PREVIO prueba/k1 ->', (await tool('memoria_load',{'scope':'prueba','key':'k1'}))[:160])
    print('3 SAVE', (await tool('memoria_save',{'scope':'e2e','key':marker,'data':{'via':'harness-mcp','t':time.time()}}))[:160])
    time.sleep(14)
    fs=HfFileSystem(token=os.environ['HF_TOKEN'])
    raw=fs.cat_file('buckets/COMAND-CENTER-1/yaiwes-memoria-storage/riu-chat/riu_chat.sqlite3')
    p=tempfile.mktemp(); open(p,'wb').write(raw)
    n=sqlite3.connect(p).execute('select count(*) from memoria_yaiwes where key=?',(marker,)).fetchone()[0]
    print('4 AUTOSYNC_EN_BUCKET', marker, 'filas=',n, 'bytes=',len(raw))
    start('/tmp/riuB')
    print('5 ROUTER_NUEVO_VACIO_RESTAURA ->', (await tool('memoria_load',{'scope':'e2e','key':marker}))[:200])
    print('6 STORAGE', (await tool('almacenamiento_estado'))[:300])
    print('7 SYNC_MANUAL', (await tool('almacenamiento_sync'))[:150])
asyncio.run(main())
