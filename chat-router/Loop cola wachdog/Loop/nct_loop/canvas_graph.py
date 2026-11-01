"""YAIWES Canvas: typed diagram contract, pure/offline, no dynamic execution.
It does not change the LOOP engine, copy code, access secrets or run skills.
"""
from __future__ import annotations
import hashlib
import json
import math
import re
from collections import defaultdict

_ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
_KINDS = {"root", "group", "task", "component", "source", "check", "note"}
_STATUSES = {"UNKNOWN", "DRAFT", "RUNNING", "PASS", "FLAGGED", "NOT_APPLICABLE", "BLOCKED", "OFF"}

class CanvasGraphError(ValueError):
    def __init__(self, code, detail=""):
        self.code = code
        super().__init__(code + (": " + str(detail) if detail else ""))

def stable_digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode("utf8")).hexdigest()

def valid_id(value, name):
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise CanvasGraphError("INVALID_ID", name)
    return value

def _text(v, maxlen=3000, name="text"):
    if not isinstance(v, str) or len(v) > maxlen:
        raise CanvasGraphError("INVALID_TEXT", name)
    return v

def _num(v):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or abs(v)>100000:
        raise CanvasGraphError("INVALID_COORDINATE")
    return float(v)

def normalize_graph(graph):
    if not isinstance(graph, dict):
        raise CanvasGraphError("INVALID_GRAPH")
    if set(graph) - {"schema_id", "graph_id", "project_id", "loop_id", "title", "mode", "nodes", "edges", "note"}:
        raise CanvasGraphError("UNKNOWN_FIELD")
    if graph.get("schema_id") != "yaiwes.canvas.graph.v1":
        raise CanvasGraphError("UNKNOWN_SCHEMA")
    graph_id = valid_id(graph.get("graph_id"), "graph_id")
    project_id = valid_id(graph.get("project_id"), "project_id")
    loop_id = graph.get("loop_id")
    if loop_id is not None:
        valid_id(loop_id, "loop_id")
    mode = graph.get("mode", "mindmap")
    if mode not in ("mindmap", "dag"):
        raise CanvasGraphError("INVALID_MODE")
    nodes, edges = graph.get("nodes"), graph.get("edges")
    if not isinstance(nodes, list) or not 1<=len(nodes)<=250:
        raise CanvasGraphError("INVALID_NODE_COUNT")
    if not isinstance(edges, list) or len(edges)>500:
        raise CanvasGraphError("INVALID_EDGE_COUNT")
    seen=set(); normalized=[]
    for n in nodes:
        if not isinstance(n,dict) or set(n)-{"id","title","kind","x","y","note","status","source_ref","checkpoint_ref","evidence_refs"}:
            raise CanvasGraphError("INVALID_NODE")
        nid=valid_id(n.get("id"), "node.id")
        if nid in seen:raise CanvasGraphError("DUPLICATE_NODE",nid)
        seen.add(nid)
        kind=n.get("kind","task");status=n.get("status","UNKNOWN")
        if kind not in _KINDS: raise CanvasGraphError("INVALID_KIND",kind)
        if status not in _STATUSES: raise CanvasGraphError("INVALID_STATUS",status)
        refs=n.get("evidence_refs",[])
        if not isinstance(refs,list) or len(refs)>20 or any(not isinstance(r,str) or len(r)>240 for r in refs):
            raise CanvasGraphError("INVALID_EVIDENCE")
        if status=="PASS" and not refs:
            raise CanvasGraphError("PASS_NEEDS_EVIDENCE",nid)
        normalized.append({"id":nid,"title":_text(n.get("title",nid),120,"node.title"),
          "kind":kind,"status":status,"note":_text(n.get("note",""),3000,"node.note"),
          "x":_num(n.get("x",0)),"y":_num(n.get("y",0)),
          "source_ref":_text(n.get("source_ref",""),500,"node.source_ref"),
          "checkpoint_ref":_text(n.get("checkpoint_ref",""),500,"node.checkpoint_ref"),
          "evidence_refs":refs})
    keys=set(); clean_edges=[]; succ=defaultdict(list)
    for edge in edges:
        if not isinstance(edge,dict) or set(edge)-{"id","source","target","title"}:
            raise CanvasGraphError("INVALID_EDGE")
        eid=valid_id(edge.get("id"), "edge.id")
        src=valid_id(edge.get("source"),"edge.source")
        dst=valid_id(edge.get("target"),"edge.target")
        if eid in keys:raise CanvasGraphError("DUPLICATE_EDGE",eid)
        if src not in seen or dst not in seen: raise CanvasGraphError("EDGE_TARGET_MISSING",eid)
        if src==dst: raise CanvasGraphError("SELF_LOOP",eid)
        keys.add(eid);succ[src].append(dst)
        clean_edges.append({"id":eid,"source":src,"target":dst,"title":_text(edge.get("title",""),120,"edge.title")})
    if mode=="dag":
        visiting=set();done=set()
        def visit(u):
            if u in visiting:raise CanvasGraphError("DAG_CYCLE",u)
            if u in done:return
            visiting.add(u)
            for v in succ[u]:visit(v)
            visiting.remove(u);done.add(u)
        for u in seen:visit(u)
    return {"schema_id":"yaiwes.canvas.graph.v1","graph_id":graph_id,"project_id":project_id,
      "loop_id":loop_id,"mode":mode,"title":_text(graph.get("title",graph_id),160,"graph.title"),
      "note":_text(graph.get("note",""),3000,"graph.note"),"nodes":normalized,"edges":clean_edges}

def validate_graph(graph):
    val=normalize_graph(graph)
    return {"ok":True,"graph":val,"sha256":stable_digest(val),
            "stats":{"nodes":len(val["nodes"]),"edges":len(val["edges"]),"mode":val["mode"]}}

def from_loop_dag(payload):
    """Only transforms an *already supplied* DAG. No extraction, synthesis or interpretation."""
    if not isinstance(payload,dict):raise CanvasGraphError("INVALID_INPUT")
    project_id=valid_id(payload.get("project_id"),"project_id")
    graph_id=valid_id(payload.get("graph_id"),"graph_id")
    raw=payload.get("dag_nodes")
    if not isinstance(raw,list) or not 1<=len(raw)<=100:
        raise CanvasGraphError("INVALID_DAG_NODES")
    ids=[];nodes=[]
    for i,item in enumerate(raw):
        if not isinstance(item,dict):raise CanvasGraphError("INVALID_DAG_NODE")
        nid=valid_id(item.get("node_id") or item.get("id"),"node_id")
        if nid in ids:raise CanvasGraphError("DUPLICATE_NODE",nid)
        ids.append(nid)
        status=item.get("status","UNKNOWN")
        # Never transfer a textual PASS without verifiable evidence refs.
        evid=item.get("evidence_refs") or []
        if status=="PASS" and not evid:status="UNKNOWN"
        nodes.append({"id":nid,"title":str(item.get("name") or item.get("title") or nid)[:120],
          "x":80+(i%5)*250,"y":75+(i//5)*135,"kind":"task","status":status,
          "note":str(item.get("note") or "")[:3000],"evidence_refs":evid,
          "source_ref":str(item.get("source_ref") or "")[:500],
          "checkpoint_ref":str(item.get("checkpoint_ref") or "")[:500]})
    edges=[];count=0
    for item,nid in zip(raw,ids):
        deps=item.get("depends_on") or []
        if not isinstance(deps,list):raise CanvasGraphError("INVALID_DEPENDENCIES")
        for dep in deps:
            count+=1;edges.append({"id":f"e{count}","source":dep,"target":nid})
    graph={"schema_id":"yaiwes.canvas.graph.v1","graph_id":graph_id,
      "project_id":project_id,"loop_id":payload.get("loop_id"),"mode":"dag",
      "title":str(payload.get("title") or "LOOP DAG")[:160],"nodes":nodes,"edges":edges}
    return validate_graph(graph)
