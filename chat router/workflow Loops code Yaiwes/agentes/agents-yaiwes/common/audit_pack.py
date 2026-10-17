"""Builds the auditor's evidence packs (deterministic, no LLM) for the 4 LENS passes over ALL of the Director's literal words:
  lens-chat.md      pass 1: every detail of the chat (UI, panels, providers, accounts, documents, history, agents in the chat, publishing);
  lens-storage.md   pass 2: storage for agents, documents, memory, caches, Crazy Wall / handoff; wiring the agents to the chat and to the documents;
  lens-models.md    pass 3: local AI models, weights, quantization, accelerators, HF Jobs / nodes / RAM, mirror = shared weights;
  lens-cross.md     pass 4: agents, DSL DAG, sheriff, routes, watchdog (cross-check and refutation of what the agents did against what was asked).
Each pack = the Director's paragraphs (verbatim, cut only at the end) from every `Claude notas/INPUT-VERBATIM-*.md`, `INPUT-BLOCK*-VERBATIM.md` and
`INPUT-BLOCKS-*-VERBATIM.md`, chosen by keywords, tagged with their source file. Also packs/agents_state.md: what each agent's Crazy Wall says.
Run (from anywhere): python audit_pack.py"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]  # agents-yaiwes
REPO = HERE.parents[1]
NOTES = REPO / "Claude notas"
OUT = HERE / "agent-5-auditor" / "packs"
PER_FILE, PER_PARA, PER_PACK = 7000, 700, 13500
GLOBS = ("INPUT-VERBATIM-2026-09-2*.md", "INPUT-BLOCK*-VERBATIM.md", "INPUT-BLOCKS-*-VERBATIM.md")
LENSES = {
    "chat": ("chat", "interfaz", "panel", "selector", "pestaña", "historial", "conversaci", "cuenta", "github", "documento", "adjunt", "claves", "banco", "vercel", "space",
             "publica", "url", "navegador", "ui", "agente con", "sin agente", "costos", "cach"),
    "storage": ("almacen", "storage", "sql", "grafo", "graphiti", "cach", "bucket", "documento", "memoria", "base de datos", "persist", "crazy wall", "handoff", "notas",
                "sesion", "sección", "historial", "guard", "agente"),
    "models": ("modelo", "qwen", "lfm", "gemma", "nanbeige", "nanojev", "decider", "smol", "k2", "gguf", "llama", "acelera", "cuantiz", "kv", "ram", "slot", "ranura", "job",
               "procesador", "openvino", "onnx", "especulativ", "espejo", "peso", "local", "token", "hf ", "hugging"),
    "cross": ("agente", "enjambre", "wordflow", "pocketflow", "smolagents", "smolange", "auditor", "sheriff", "watchdog", "router", "dsl", "dag", "delega", "loop", "ruta", "deepsek",
              "mínimax", "minimax", "verificaci", "refut", "prioridad", "instrucci"),
}


def director_text(path: Path) -> str:
    t = path.read_text(encoding="utf-8", errors="ignore")
    if path.name.startswith("INPUT-VERBATIM-2026-09-2"):
        a, b = t.find("\n---\n"), t.find("\n## Cola")
        t = t[a + 5: b if b > a else None] if a >= 0 else t
        m = re.search(r"\n## (Documento|Adjunto)", t)
        if m:
            t = t[: m.start()]
    return t.strip()[:PER_FILE]


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.strip()) >= 30]


def build_pack(lens: str, files: list[Path]) -> str:
    kws, out, total = LENSES[lens], [], 0
    for f in files:
        picked = []
        for p in paragraphs(director_text(f)):
            low = p.lower()
            hits = sum(1 for k in kws if k in low)
            if hits >= (2 if lens == "cross" else 1):
                picked.append(p[:PER_PARA])
        if not picked:
            continue
        block = f"=== ARCHIVO: Claude notas/{f.name} ===\n" + "\n\n".join(picked) + "\n"
        if total + len(block) > PER_PACK:
            block = block[: max(0, PER_PACK - total)]
        out.append(block)
        total += len(block)
        if total >= PER_PACK:
            break
    return "\n".join(out) or "(sin párrafos)"


def agents_state() -> str:
    rows = []
    for d in sorted(HERE.glob("agent-*")):
        if not d.is_dir() or d.name == "agent-5-auditor":
            continue
        top = json.loads((d / "crazy_wall.state.json").read_text(encoding="utf-8")) if (d / "crazy_wall.state.json").exists() else {}
        rows.append(f"## {d.name}: estado={top.get('status', '?')} marco={top.get('framework', '?')} pasos_cerrados={top.get('completed', [])}")
        for s in sorted((d / "steps").glob("*/crazy_wall.state.json")) if (d / "steps").exists() else []:
            st = json.loads(s.read_text(encoding="utf-8"))
            files = [str(f.relative_to(REPO)) for f in sorted((s.parent / "results").glob("*")) if f.name != "output.txt"] if (s.parent / "results").exists() else []
            rows.append(f"- paso {s.parent.name}: {st.get('status')} modelo={st.get('model', '-')} entregables={files} gaps={'; '.join(st.get('gaps', []))[:120] or '-'}")
    return "\n".join(rows) or "(sin agentes)"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    for g in GLOBS:
        files += sorted(NOTES.glob(g))
    files = sorted(dict.fromkeys(files), key=lambda p: p.name)
    sizes = {}
    for lens in LENSES:
        text = build_pack(lens, files)
        (OUT / f"lens-{lens}.md").write_text(text, encoding="utf-8")
        sizes[lens] = len(text)
    (OUT / "agents_state.md").write_text(agents_state()[:9000], encoding="utf-8")
    print(f"archivos fuente: {len(files)}; paquetes por lente (caracteres): {sizes}")


if __name__ == "__main__":
    main()
