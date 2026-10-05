import { node } from "./api.js";

export async function mount(root, { api, tell }) {
  let files = [];
  const render = () => {
    const list = root.querySelector("#file-list");
    list.replaceChildren();
    const query = root.querySelector("#file-search").value.toLowerCase();
    for (const file of files.filter(item => item.name.toLowerCase().includes(query))) {
      const entry = node("div", `${file.name} · ${file.mime} · ${file.size} bytes`, "item");
      entry.append(node("span", ` ${file.id}`, "badge"));
      list.append(entry);
    }
    if (!list.children.length) list.append(node("p", "Sin archivos registrados.", "muted"));
  };
  const reload = async () => { files = (await api("/chat/org/files")).data.files; render(); };
  root.querySelector("#file-search").addEventListener("input", render);
  root.querySelector("#reload").addEventListener("click", () => reload().catch(error => tell(error.message)));
  try { await reload(); } catch (error) { tell(error.message); }
  root.querySelector("#upload").addEventListener("submit", async event => {
    event.preventDefault();
    const file = root.querySelector("#file-input").files[0];
    if (!file || file.size > 10 * 1024 * 1024) { tell("Archivo vacío o superior a 10 MB"); return; }
    try {
      const bytes = new Uint8Array(await file.arrayBuffer());
      const parts = [];
      for (let i = 0; i < bytes.length; i += 8192) parts.push(String.fromCharCode(...bytes.subarray(i, i + 8192)));
      const result = await api("/chat/documents", { method: "POST", body: { name: file.name,
        mime: file.type || "application/octet-stream", data_b64: btoa(parts.join("")) } });
      tell(`Guardado en Router: ${result.document.id}. Sin sincronización HF confirmada.`);
      await reload();
    } catch (error) { tell(error.message); }
  });
}
