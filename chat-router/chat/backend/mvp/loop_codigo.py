from __future__ import annotations
import ast, asyncio, hashlib, inspect, json, os, re, time
from typing import Awaitable, Callable
LINEAS = re.compile(r"\b(\d{3,4})\s*lineas?", re.I)
CODIGO = re.compile(r"\b(?:codigo|c[oó]digo|python|programa|script|funciones|clases)\b", re.I)
REINTENTABLE = re.compile(r"(?:HTTP\s*)?(?:408|425|429|500|502|503|504)|timeout|temporar|rate.?limit|connection|reset", re.I)
RETRY_AFTER = re.compile(r"retry.?after\D{0,8}(\d{1,4})", re.I)
BLOQUE = 200
MAX_CONTINUACIONES = 12

def solicitado(mensaje: str, tipo: str = "", modo: str = "") -> int | None:
    m = LINEAS.search(mensaje)
    if m and CODIGO.search(mensaje) and 100 <= int(m.group(1)) <= 2000: return int(m.group(1))
    return 500 if tipo == "code_largo" and modo == "loop" else None

def _limpiar(s: str) -> str:
    s = re.sub(r"(?m)^\s*<<FIN_SECCION_\d+>>\s*$", "", str(s or "")); s = s.strip()
    if s.startswith("```"):
        a=s.splitlines()
        if a and a[0].strip() in ("```","```python","```py"):
            a.pop(0)
            if a and a[-1].strip()=="```": a.pop()
            s="\n".join(a)
    return s.strip("\n")

def _unir(piezas: list[str]) -> str:
    salida=[]
    for pieza in piezas:
        lineas=_limpiar(pieza).splitlines(); solape=0
        for n in range(min(50,len(salida),len(lineas)),0,-1):
            if salida[-n:]==lineas[:n]: solape=n; break
        salida.extend(lineas[solape:])
    return "\n".join(salida)

def _append(a: str,b: str) -> str: return _unir([a,b]) if a else _limpiar(b)

def _capacidad(modelo: str) -> int:
    try:
        from mvp import externos
        n=(getattr(externos,"LIMITES_MODELO",{}).get(modelo,{}) or {}).get("max_tokens")
        if isinstance(n,int) and n>0: return n
    except Exception: pass
    var="RIU_GROQ_MAX_COMPLETION_TOKENS" if modelo.startswith("groq/") else "RIU_NVIDIA_MAX_COMPLETION_TOKENS"
    try: return max(1024,int(os.environ.get(var,"8192")))
    except (TypeError,ValueError): return 8192

def _alterno(modelo: str) -> str | None:
    if modelo.startswith("groq/"): return "nvidia/minimaxai/minimax-m3.1-flash"
    if modelo.startswith("nvidia/"): return "groq/qwen/qwen3.8-27b"
    return None

async def _llamar(inferir,mensajes,tokens,modelo):
    try:
        ps=inspect.signature(inferir).parameters.values()
        toma_modelo=any(p.kind==p.VAR_POSITIONAL for p in ps) or len(inspect.signature(inferir).parameters)>=3
    except (TypeError,ValueError): toma_modelo=False
    r=inferir(mensajes,tokens,modelo) if toma_modelo else inferir(mensajes,tokens)
    return await r if inspect.isawaitable(r) else r

def _valida(parte: str,limite: int,hashes: set[str]) -> tuple[bool,str,int]:
    t=_limpiar(parte); n=len(t.splitlines())
    if not t or n<10 or n!=limite: return False,"CANTIDAD_LINEAS_INVALIDA",n
    if hashlib.sha256(t.encode()).hexdigest() in hashes: return False,"SEGMENTO_REPETIDO",n
    try: arbol=ast.parse(t); compile(arbol,"<coda-segmento>","exec")
    except (SyntaxError,ValueError): return False,"SINTAXIS_PYTHON_INVALIDA",n
    if not any(isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) for x in arbol.body): return False,"FALTAN_DEFINICIONES",n
    return True,t,n

async def generar(*,mensajes: list[dict],modelo: str,pid: str,n_lineas: int,inferir: Callable,
                  cargar: Callable[[],Awaitable[dict|None]],guardar: Callable[[dict],Awaitable[bool]],
                  progreso: Callable[[str,str],None]=lambda _n,_t:None,cancelado: Callable[[],bool]=lambda:False,
                  horas: float=4.0,dormir: Callable[[float],Awaitable[None]]=asyncio.sleep,reloj: Callable[[],float]=time.time) -> dict:
    if not (100<=n_lineas<=2000) or not (0<horas<=4): raise ValueError("CODA_LIMITE_INVALIDO")
    huella=hashlib.sha256(json.dumps([modelo,mensajes,n_lineas],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    estado=await cargar()
    if estado and (estado.get("tipo") not in ("coda-codigo-v1","coda-codigo-v2") or estado.get("huella")!=huella): raise ValueError("CODA_CHECKPOINT_OTRA_TAREA")
    indice=[f"{i}. Sección {i}: líneas {(i-1)*BLOQUE+1}–{min(i*BLOQUE,n_lineas)}" for i in range(1,(n_lineas+BLOQUE-1)//BLOQUE+1)]
    if not estado:
        estado=dict(tipo="coda-codigo-v2",huella=huella,modelo=modelo,modelo_actual=modelo,n_lineas=n_lineas,indice=indice,
                    piezas=[],write_chunks=[],parcial="",seccion_actual=1,creado=reloj(),intentos=0,tam_bloque=BLOQUE,
                    fallos_segmento=0,fallos_transitorios=0,siguiente_llamada=0,validacion="PENDIENTE")
        if not await guardar(estado): raise RuntimeError("CODA_CHECKPOINT_NO_PERSISTIDO")
    else:
        estado.update(tipo="coda-codigo-v2",indice=estado.get("indice") or indice,modelo_actual=estado.get("modelo_actual") or estado.get("modelo") or modelo,
                     write_chunks=estado.get("write_chunks",[]),parcial=estado.get("parcial",""),seccion_actual=estado.get("seccion_actual",len(estado.get("piezas",[]))+1))
    piezas=list(estado.get("piezas",[])); hashes={hashlib.sha256(t.encode()).hexdigest() for t in piezas}
    vencimiento=min(float(estado["creado"])+horas*3600,reloj()+horas*3600); fallos_seccion=0; fallos_globales=0
    usuario=next((str(m.get("content") or "") for m in reversed(mensajes) if m.get("role")=="user"),"")
    while True:
        if cancelado(): raise RuntimeError("CODA_CANCELADO_CHECKPOINT_CONSERVADO")
        if reloj()>=vencimiento: raise RuntimeError("CODA_TIEMPO_AGOTADO_CHECKPOINT_CONSERVADO")
        actual=_unir(piezas); lineas=len(actual.splitlines())
        if lineas>=n_lineas:
            codigo=actual+"\n"
            try: ast.parse(codigo); compile(codigo,"<coda-final>","exec")
            except (SyntaxError,ValueError):
                fallos_globales+=1
                if fallos_globales>3 or not piezas: raise RuntimeError("CODA_VALIDACION_GLOBAL_FALLO_CHECKPOINT_CONSERVADO")
                piezas.pop(); estado["piezas"]=piezas; estado["write_chunks"]=estado.get("write_chunks",[])[:-1]
                estado["seccion_actual"]=max(1,int(estado.get("seccion_actual",2))-1); estado["validacion"]="PENDIENTE"
                estado["ultimo_gap"]="CODA_VALIDACION_GLOBAL_FALLO; regenerar sólo la última sección"
                if not await guardar(estado): raise RuntimeError("CODA_CHECKPOINT_NO_PERSISTIDO")
                continue
            if len(codigo.splitlines())!=n_lineas: raise RuntimeError("CODA_LINEAS_INCORRECTAS_CHECKPOINT_CONSERVADO")
            estado["validacion"]="PASS"
            if not await guardar(estado): raise RuntimeError("CODA_CHECKPOINT_NO_PERSISTIDO")
            return {"texto":codigo,"lineas":n_lineas,"partes":len(piezas),"desde_checkpoint":False,"sha256":hashlib.sha256(codigo.encode()).hexdigest(),
                    "modelo_final":estado.get("modelo_actual",modelo),"validacion_tipo":"PASS_SINTAXIS","ejecucion_real":False,"publicacion_confirmada":False}
        pedir=min(max(10,min(int(estado.get("tam_bloque") or BLOQUE),BLOQUE)),n_lineas-lineas)
        seccion=int(estado.get("seccion_actual") or len(piezas)+1); modelo_actual=str(estado.get("modelo_actual") or modelo)
        parcial=str(estado.get("parcial") or ""); restantes=max(0,pedir-len(parcial.splitlines()))
        defs=[]
        for t in piezas:
            try: defs += [x.name for x in ast.parse(t).body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
            except SyntaxError: pass
        cabecera=(f"TAREA CODA PYTHON. Archivo {n_lineas} líneas; validadas {lineas}; sección {seccion}.\n"
          +"ÍNDICE NUMERADO, guardado antes de generar secciones:\n"+"\n".join(estado["indice"])+"\n"
          +f"Genera exactamente {restantes} líneas nuevas de código Python. Centinela obligatorio al final: <<FIN_SECCION_{seccion}>>.\n"
          +f"Funciones/clases previas: {', '.join(defs[-35:]) or '(ninguna)'}.\n"
          +( "Resumen: continúa el archivo; conserva lo validado.\n" if piezas else "Resumen: inicia el archivo según el índice.\n")
          +( "Corrige el intento anterior: "+str(estado.get("ultimo_gap") or "")[:160]+"\n" if estado.get("ultimo_gap") else "")
          +"Requisitos originales verbatim:\n"+usuario+"\nSin markdown, relleno, herramientas ni afirmar ejecución/publicación. Cada sección debe pasar ast.parse.")
        if parcial:
            peticion=[{"role":"assistant","content":"\n".join(parcial.splitlines()[-50:])},
                      {"role":"user","content":cabecera+f"\nSigue desde la línea {lineas+len(parcial.splitlines())+1}; no reinicies, termina sólo esta sección."}]
        else: peticion=[{"role":"user","content":cabecera}]
        espera=max(0.,float(estado.get("siguiente_llamada",0))-reloj())
        if espera: progreso(str(lineas),"cuota: espera %.0fs"%espera); await dormir(espera)
        estado["intentos"]=int(estado.get("intentos",0))+1
        if not await guardar(estado): raise RuntimeError("CODA_CHECKPOINT_NO_PERSISTIDO")
        progreso(str(lineas),"sección %d · %s · %d líneas"%(seccion,modelo_actual,restantes))
        tokens=min(_capacidad(modelo_actual),max(2048,650+restantes*35))
        try:
            r=await _llamar(inferir,peticion,tokens,modelo_actual); frag=str(r.get("texto") or "")
            if r.get("tool_calls"): raise ValueError("CODA_TOOLS_INESPERADAS")
            marca=f"<<FIN_SECCION_{seccion}>>"; cerrado=marca in frag; frag=frag.replace(marca,"")
            if not cerrado:
                if frag.strip(): estado["parcial"]=_append(parcial,frag)
                estado["finish_reason"]=str(r.get("finish_reason") or ""); estado["ultimo_gap"]="CODA_FIN_SECCION_AUSENTE"
                estado["fallos_transitorios"]=int(estado.get("fallos_transitorios",0))+1
                alt=_alterno(modelo_actual)
                if estado["fallos_transitorios"]>=2 and alt: estado["modelo_actual"]=alt; estado["fallos_transitorios"]=0
                if not await guardar(estado): raise RuntimeError("CODA_CHECKPOINT_NO_PERSISTIDO")
                continue
            texto=_append(parcial,frag); ok,resultado,cuenta=_valida(texto,pedir,hashes)
            if not ok:
                fallos_seccion+=1; estado["parcial"]=""; estado["ultimo_gap"]="CODA_"+resultado
                estado["fallos_segmento"]=int(estado.get("fallos_segmento",0))+1
                if estado["fallos_segmento"]>=2: estado["tam_bloque"]=max(10,int(estado.get("tam_bloque") or BLOQUE)//2); estado["fallos_segmento"]=0
                if fallos_seccion>=7: raise RuntimeError("CODA_CODIGO_INVALIDO_REPETIDO_CHECKPOINT_CONSERVADO: "+resultado)
                if not await guardar(estado): raise RuntimeError("CODA_CHECKPOINT_NO_PERSISTIDO")
                continue
        except Exception as e:
            error=str(e)
            if error.startswith("CODA_"): raise
            if not REINTENTABLE.search(error): raise
            estado["fallos_transitorios"]=int(estado.get("fallos_transitorios",0))+1; alt=_alterno(modelo_actual)
            if estado["fallos_transitorios"]>=2 and alt: estado["modelo_actual"]=alt; estado["fallos_transitorios"]=0; estado["parcial"]=""
            m=RETRY_AFTER.search(error); demora=min(int(m.group(1)),600) if m else 0
            estado["siguiente_llamada"]=reloj()+max(65 if modelo_actual.startswith("groq/") else 10,demora); estado["ultimo_gap"]=error[:150]
            if not await guardar(estado): raise RuntimeError("CODA_CHECKPOINT_NO_PERSISTIDO")
            continue
        # write_chunk: persistir sólo después de validar la sección con parser/AST.
        piezas.append(resultado); hashes.add(hashlib.sha256(resultado.encode()).hexdigest())
        estado["piezas"]=piezas; estado["parcial"]=""; estado["ultimo_gap"]=""; estado["fallos_transitorios"]=0
        estado["modelo_actual"]=modelo_actual; estado["seccion_actual"]=seccion+1
        estado["write_chunks"]=list(estado.get("write_chunks",[]))+[{"seccion":seccion,"lineas":cuenta,"validacion":"PASS_AST","sha256":hashlib.sha256(resultado.encode()).hexdigest()}]
        estado["siguiente_llamada"]=reloj()+(65 if modelo_actual.startswith("groq/") else 0)
        if not await guardar(estado): raise RuntimeError("CODA_CHECKPOINT_NO_PERSISTIDO")
        progreso(str(len(_unir(piezas).splitlines())),"sección %d validada · checkpoint"%seccion); fallos_seccion=0
