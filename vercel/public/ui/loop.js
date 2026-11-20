/**
 * loop.js — Loop del frontend con lock por sessionStorage.
 * Endpoints alineados con Salida 2A: /v1/loop/config|start|step|error
 * 4 bugs corregidos: (1) lock doble-dueño, (2) headers JSON,
 * (3) rotura en maxIter, (4) manejo explícito de error-state.
 */
export async function runLoop(taskId) {
    const lockKey = `loop_lock_${taskId}`;
    if (sessionStorage.getItem(lockKey) === 'true') {
        console.warn(`[Loop] ${taskId} ya corre. Ignorado.`);
        return { ok: false, reason: 'locked' };
    }
    sessionStorage.setItem(lockKey, 'true');
    try {
        const cfgRes = await fetch('/v1/loop/config');
        if (!cfgRes.ok) throw new Error(`config HTTP ${cfgRes.status}`);
        const cfg = await cfgRes.json();
        const maxIter = cfg.max_iterations || 8;

        const startRes = await fetch('/v1/loop/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ taskId })
        });
        if (!startRes.ok) throw new Error(`start HTTP ${startRes.status}`);

        for (let i = 0; i < maxIter; i++) {
            const stepRes = await fetch('/v1/loop/step', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ taskId, iteration: i })
            });
            if (!stepRes.ok) throw new Error(`step ${i} HTTP ${stepRes.status}`);
            const stepData = await stepRes.json();
            const st = stepData?.state?.status;
            if (st === 'error') throw new Error(`loop error state at iter ${i}`);
            if (st === 'done') break;
        }
        return { ok: true };
    } catch (e) {
        console.error('[Loop Error]', e);
        try {
            await fetch('/v1/loop/error', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ taskId, error: String(e.message || e) })
            });
        } catch (_) { /* fail-soft */ }
        return { ok: false, error: String(e.message || e) };
    } finally {
        sessionStorage.setItem(lockKey, 'false');
    }
}


export async function resumeLoop(taskId) {
    try {
        const r = await fetch(`/v1/loop/resume?taskId=${encodeURIComponent(taskId)}`);
        if (!r.ok) return { ok: false };
        const d = await r.json();
        return d.ok ? { ok: true, next: d.next_iteration || 0 } : { ok: false };
    } catch (_) { return { ok: false }; }
}
