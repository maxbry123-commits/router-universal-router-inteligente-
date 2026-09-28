import asyncio,importlib,os,sys
from pathlib import Path
os.environ["SIMULADO"]="1"
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import action_registry,council,rewind,compact,archify_cmd,work,rutas

def test_registry():
 assert action_registry.ejecutar("watchdog.start",{})["status"]=="PASS"
 assert action_registry.traducir_comando("/rewind x")=="rewind"
def test_rewind():
 rewind.guardar("c",{"n":1});rewind.guardar("c",{"n":2});assert rewind.volver("c",1)=={"n":1}
def test_compact():
 r=compact.compactar([{"content":"objetivo"}]);assert r["estado"]=="compactado" and r["mensajes"]==1
def test_archify():assert archify_cmd.archify("hacer tarea").startswith("flowchart")
def test_work():
 work.crear("w");assert work.pausar("w")["status"]=="PAUSED";assert work.aprobar("w")["progress"]==100
def test_council():
 r=asyncio.run(council.ask_council("hola",3));assert len(r["respuestas"])==3 and r["sintesis"]
def test_routes_declared():
 paths={r.path for r in rutas.build_router().routes};assert {"/acciones/{action_id}","/council","/rewind","/compact","/archify","/work"}<=paths
