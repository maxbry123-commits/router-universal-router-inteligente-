import { node } from "./api.js";

export async function mount(root, { api, tell }) {
  try {
    const [graph, queue, bitacora] = await Promise.all([
      api("/chat/org/graph"), api("/chat/org/queue"), api("/chat/org/bitacora?limit=30")
    ]);
    const train = root.querySelector("#train");
    for (const agent of graph.data.graph.nodes || []) {
      train.append(node("div", `${agent.id} · ${agent.rol}`, "item"));
    }
    if (!train.children.length) train.append(node("p", "Sin agentes registrados", "muted"));
    const work = root.querySelector("#queue");
    for (const task of queue.data.tasks || []) work.append(node("div", JSON.stringify(task), "item"));
    if (!work.children.length) work.append(node("p", "Sin tareas en cola", "muted"));
    const events = root.querySelector("#events");
    for (const item of (bitacora.data.events || []).toReversed()) {
      const row = node("div", `${item.task} · ${item.status} · ${item.phase || ""} · ${item.summary || ""}`, "item");
      events.append(row);
    }
  } catch (error) { tell(error.message); }
  root.querySelector("#run-load").addEventListener("click", async () => {
    const id = root.querySelector("#run-id").value.trim();
    if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/.test(id)) { tell("ID de run inválido"); return; }
    try { const result = await api(`/chat/org/dag/${encodeURIComponent(id)}`);
      root.querySelector("#ledger").textContent = JSON.stringify(result.data.run.ledger || [], null, 2); }
    catch (error) { tell(error.message); }
  });
}
