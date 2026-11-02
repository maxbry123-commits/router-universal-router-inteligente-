"""Fase 8: decisiones de recuperación; no reintenta operaciones no idempotentes ciegamente."""

def decide_repair(failures:int, *, retryable:bool, has_checkpoint:bool, authorized_fallback:bool=False) -> dict:
    if not retryable:return {'action':'BLOCK','reason':'acción no repetible sin reconciliación'}
    if failures<=2:return {'action':'RETRY_SAME','reason':'fallo transitorio, requiere nuevo recibo'}
    if failures==3:return {'action':'COMPACT_CONTEXT','reason':'comprensión del fallo y reducción de contexto'}
    if failures==4 and authorized_fallback:return {'action':'FALLBACK_AUTHORIZED','reason':'fallback expresamente permitido'}
    if has_checkpoint:return {'action':'RESTORE_CHECKPOINT','reason':'requiere restauración aprobada, no destructiva'}
    return {'action':'ESCALATE','reason':'replanificar o solicitar decisión del usuario'}

# MECÁNICO deterministic GAP evidence and bounded read-only research.
# Approved source IDs exactly match config/investigation_sources.json.
RESEARCH_SITES=(("github","https://github.com/search?q={q}&type=code"),
("huggingface","https://huggingface.co/models?search={q}"),
("stackoverflow","https://stackoverflow.com/search?q={q}"),
("python_docs","https://docs.python.org/3/search.html?q={q}"),
("mdn","https://developer.mozilla.org/en-US/search?q={q}"),
("fastapi","https://fastapi.tiangolo.com/"),
("pytest","https://docs.pytest.org/en/stable/"),
("pypi","https://pypi.org/search/?q={q}"),
("owasp","https://owasp.org/"),
("sqlite_docs","https://sqlite.org/search.html"))

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
            page=data.decode("utf8","replace")
            title=re.search(r"<title[^>]*>(.*?)</title>",page,re.I|re.S)
            title=html.unescape(re.sub(r"<[^>]+>","",title.group(1))).strip()[:140] if title else ""
            clean=re.sub(r"<(script|style)[^>]*>.*?</\\1>"," ",page,flags=re.I|re.S)
            excerpt=html.unescape(re.sub(r"<[^>]+>"," ",clean))
            excerpt=re.sub(r"\\s+"," ",excerpt).strip()[:1000]
            digest=hashlib.sha256(data).hexdigest()
            if not title or not excerpt:
                return {"site":name,"source_id":name,"url":url,
                        "status":"NO_EXTRACTABLE_EVIDENCE"}
            return {"site":name,"source_id":name,"url":url,
                    "status":"SOURCE_FOUND_UNVERIFIED","title":title,
                    "excerpt":excerpt,"retrieved_ref":"http-sha256:"+digest,
                    "sha256":digest}
        except Exception as e:
            code=getattr(e,"code",None)
            return {"site":name,"url":url,"status":"UNAVAILABLE",
                    "http_status":code if isinstance(code,int) else None}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(one,RESEARCH_SITES))

def safe_research_open(url, espera=5):
    """Read only fixed HTTPS hosts; no redirects, private DNS or credentials."""
    import ipaddress,socket,urllib.parse,urllib.request
    from .gap_mechanic import SOURCE_DOMAINS
    u=urllib.parse.urlsplit(url)
    hosts=set(SOURCE_DOMAINS.values())
    if (u.scheme!="https" or u.username is not None or u.password is not None
            or u.port not in (None,443) or u.hostname not in hosts):
        raise ValueError("RESEARCH_HOST_DENIED")
    resolved=socket.getaddrinfo(u.hostname,443,type=socket.SOCK_STREAM)
    if not resolved or any(not ipaddress.ip_address(x[4][0]).is_global for x in resolved):
        raise ValueError("RESEARCH_DNS_DENIED")
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,req,fp,code,msg,headers,newurl):
            return None
    client=urllib.request.build_opener(NoRedirect())
    req=urllib.request.Request(url,headers={"User-Agent":"YAIWES-ReadOnly-Research/1"})
    return client.open(req,timeout=min(float(espera),6.0))
