import { button, el, openWindow } from "../dom.js";
import { executeAction } from "../bridge.js";
import { t } from "../i18n.js";

// GitHub real del Router: accounts → repos → file (con adjuntar) → commit.
// Nada se simula: cada botón llama al endpoint y muestra la respuesta o el error real.
export function openGithub(context) {
  const status = el("p", { role: "status", class: "muted", "aria-live": "polite" });
  const out = el("div", { class: "panel-results" });
  const account = el("select", { "aria-label": t(context, "ghAccount") });
  const repo = el("input", { class: "setting-input", placeholder: "owner/repo", "aria-label": "repo" });
  const path = el("input", { class: "setting-input", placeholder: "ruta/archivo", "aria-label": "path" });
  const ref = el("input", { class: "setting-input", placeholder: "ref (opcional)", "aria-label": "ref" });
  const content = el("textarea", { class: "setting-input", placeholder: "contenido del archivo", "aria-label": "content", rows: "4" });
  const message = el("input", { class: "setting-input", placeholder: "mensaje de commit", "aria-label": "commit message" });
  const branch = el("input", { class: "setting-input", placeholder: "rama (opcional)", "aria-label": "branch" });
  const attach = el("input", { type: "checkbox", id: "gh-attach" });

  async function run(fn, okText) {
    status.className = "muted"; status.textContent = t(context, "backendLoading");
    try {
      const text = await fn();
      status.className = ""; status.textContent = okText(text);
    } catch (error) {
      status.className = "error"; status.textContent = error.message;
    }
  }

  const dialog = openWindow(t(context, "github"), el("div", { class: "window-body" },
    el("div", { class: "setting-field" }, el("span", { text: t(context, "ghAccount") }), account),
    el("div", { class: "chip-row" },
      button(t(context, "ghRepos"), () => run(async () => {
        const r = await executeAction("chat.github.repos", { account: account.value });
        out.replaceChildren(el("pre", { text: JSON.stringify(r.repos, null, 2) }));
        return r.repos.length;
      }, n => t(context, "ghReposLoaded", { n }))),
      button(t(context, "ghReadFile"), () => run(async () => {
        const r = await executeAction("chat.github.file", { account: account.value, repo: repo.value, path: path.value, ref: ref.value || undefined, attach: attach.checked });
        out.replaceChildren(el("pre", { text: r.file.text.slice(0, 4000) }),
          el("p", { class: "muted", text: "sha " + r.file.sha + " · " + r.file.size + "B" + (r.document ? " · document " + r.document.id : "") }));
        return r.file.path;
      }, p => t(context, "ghFileLoaded", { p }))),
      button(t(context, "ghCommit"), () => run(async () => {
        const r = await executeAction("chat.github.commit", { account: account.value, repo: repo.value, path: path.value, content: content.value, message: message.value, branch: branch.value || undefined });
        out.replaceChildren(el("pre", { text: JSON.stringify(r.commit, null, 2) }));
        return true;
      }, () => t(context, "ghCommitDone")), "primary")),
    el("div", { class: "setting-field" }, repo, path, ref,
      el("label", { class: "typo-toggle" }, attach, el("span", { text: t(context, "ghAttach") })),
      content, message, branch),
    status, out), t(context, "closeWindow"));

  run(async () => {
    const r = await executeAction("chat.github.accounts", {});
    account.replaceChildren(...r.items.map(item => {
      const o = el("option", { value: item.id, text: item.id + " · " + item.description });
      if (item.description === "NOT_CONFIGURED") o.disabled = true;
      return o;
    }));
    return r.items.length;
  }, n => t(context, "ghAccountsLoaded", { n }));
  return dialog;
}
