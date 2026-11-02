"""Fase 8: decisiones de recuperación; no reintenta operaciones no idempotentes ciegamente."""

def decide_repair(failures:int, *, retryable:bool, has_checkpoint:bool, authorized_fallback:bool=False) -> dict:
    if not retryable:return {'action':'BLOCK','reason':'acción no repetible sin reconciliación'}
    if failures<=2:return {'action':'RETRY_SAME','reason':'fallo transitorio, requiere nuevo recibo'}
    if failures==3:return {'action':'COMPACT_CONTEXT','reason':'comprensión del fallo y reducción de contexto'}
    if failures==4 and authorized_fallback:return {'action':'FALLBACK_AUTHORIZED','reason':'fallback expresamente permitido'}
    if has_checkpoint:return {'action':'RESTORE_CHECKPOINT','reason':'requiere restauración aprobada, no destructiva'}
    return {'action':'ESCALATE','reason':'replanificar o solicitar decisión del usuario'}

# MECÁNICO deterministic GAP evidence and bounded read-only research.
RESEARCH_SITES=(("GitHub","https://github.com/search?q={q}&type=code"),
("HuggingFace","https://huggingface.co/models?search={q}"),
("StackOverflow","https://stackoverflow.com/search?q={q}"),
("Python","https://docs.python.org/3/search.html?q={q}"),
("MDN","https://developer.mozilla.org/en-US/search?q={q}"),
("GitHubDocs","https://docs.github.com/en/search?query={q}"),
("PyPI","https://pypi.org/search/?q={q}"),
("FastAPI","https://fastapi.tiangolo.com/"),
("Pytest","https://docs.pytest.org/en/stable/"),
("PythonDiscuss","https://discuss.python.org/search?q={q}"))

def gap_events(project,loop,contracts,checkpoints,queue):
    import re
    from .trigger_contract import canonical,sha256
    if not isinstance(queue,dict) or not isinstance(checkpoints,dict):
        raise ValueError("GAP_EVIDENCE_MISSING")
    tasks={x["id"]:x for x in queue.get("tasks",[]) if isinstance(x,dict) and x.get("id")}
    out=[]
    for contract in contracts:
        tid=contract["id"];receipt=checkpoints.get(tid) or {};task=tasks.get(tid) or {}
        code=receipt.get("error")
        if not isinstance(code,str) or not re.fullmatch(r"[A-Z][A-Z0-9_]{2,90}",code):
            code="QUEUE_"+str(task.get("status")).upper() if task.get("status") in (
                "failed","cancelled","needs_reconciliation") else None
        if not code:continue
        sha=sha256(canonical(contract))
        if receipt.get("contract_sha256") not in (None,sha):code="STALE_RECEIPT_SHA"
        row={"project_id":project,"loop_id":loop,"trigger_id":tid,"code":code,
             "contract_sha256":sha,"queue_id":queue.get("queue_id"),
             "queue_status":task.get("status"),"receipt_ref":receipt.get("queue_receipt_ref")}
        row["gap_id"]="gap:"+sha256(canonical(row))[:24]
        out.append(row)
    return out

def research_sources(query, opener):
    import urllib.parse,hashlib,re,html,concurrent.futures
    if not isinstance(query,str) or not 3<=len(query)<=180:
        raise ValueError("BAD_RESEARCH_QUERY")
    q=urllib.parse.quote(query,safe="")
    def one(row):
        name,template=row;url=template.format(q=q)
        try:
            with opener(url,espera=5) as response:
                status=int(getattr(response,"status",200))
                mime=str(response.headers.get("Content-Type","")).lower()
                if status!=200 or not any(x in mime for x in ("text/html","text/plain")):
                    return {"site":name,"url":url,"status":"NO_EVIDENCE","http_status":status}
                data=response.read(16001)
            if len(data)>16000:return {"site":name,"url":url,"status":"TOO_LARGE"}
            title=re.search(r"<title[^>]*>(.*?)</title>",data.decode("utf8","replace"),re.I|re.S)
            title=html.unescape(re.sub(r"<[^>]+>","",title.group(1))).strip()[:140] if title else ""
            return {"site":name,"url":url,"status":"SOURCE_FOUND_UNVERIFIED",
                    "title":title,"sha256":hashlib.sha256(data).hexdigest()}
        except Exception as e:
            code=getattr(e,"code",None)
            return {"site":name,"url":url,"status":"UNAVAILABLE",
                    "http_status":code if isinstance(code,int) else None}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(one,RESEARCH_SITES))
