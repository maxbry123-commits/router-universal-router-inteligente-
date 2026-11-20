"""patch_loop_resume.py - Añade /v1/loop/resume y resumeLoop. Idempotente."""
import os, re

PROXY = "ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py"
LOOP = "chat-router/chat/ui/loop.js"

ENDPOINT = '''

@app.get("/v1/loop/resume")
async def loop_resume(taskId: str):
    import json
    from router_llm_hf.checkpoint_manager import CheckpointManager
    cm = CheckpointManager()
    try:
        if taskId not in cm.list_checkpoints():
            return {"ok": False, "reason": "not_found"}
        state = json.loads(open(f"state/checkpoints/{taskId}.json").read())
        return {"ok": True, "state": state,
                "next_iteration": state.get("iteration", 0)}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}:{e}"}
'''

JS_BLOCK = '''

export async function resumeLoop(taskId) {
    try {
        const r = await fetch(`/v1/loop/resume?taskId=${encodeURIComponent(taskId)}`);
        if (!r.ok) return { ok: false };
        const d = await r.json();
        return d.ok ? { ok: true, next: d.next_iteration || 0 } : { ok: false };
    } catch (_) { return { ok: false }; }
}
'''


def main():
    changed = []
    if os.path.exists(PROXY):
        s = open(PROXY, "r", encoding="utf-8").read()
        if "/v1/loop/resume" not in s:
            m = re.search(r"^if __name__", s, re.MULTILINE)
            s = (s[:m.start()] + ENDPOINT + "\n\n" + s[m.start():]) if m else s + ENDPOINT
            open(PROXY, "w", encoding="utf-8").write(s)
            changed.append("proxy")
    if os.path.exists(LOOP):
        s = open(LOOP, "r", encoding="utf-8").read()
        if "resumeLoop" not in s:
            open(LOOP, "w", encoding="utf-8").write(s + JS_BLOCK)
            changed.append("loop.js")
    print(f"PATCH_LOOP_OK:{changed or 'idempotent'}")


if __name__ == "__main__":
    main()
