import { button, el } from "../dom.js";
import { openModels } from "../windows/models.js";
import { openModes } from "../windows/modes.js";
import { openActions } from "../windows/actions.js";
import { openSkills } from "../windows/skills.js";
import { openConnectors } from "../windows/connectors.js";
import { openSelector1 } from "../windows/selector-1.js";
import { openSelector2 } from "../windows/selector-2.js";
import { openSelector3 } from "../windows/selector-3.js";
import { openSelector4 } from "../windows/selector-4.js";
import { openSelector5 } from "../windows/selector-5.js";
import { sendMessage } from "../actions/send-message.js";
import { toggleRecording } from "../actions/record-voice.js";
import { attachments } from "../components/attachments.js";
import { messageStream } from "../components/message-stream.js";
import { namedButton } from "../components/named-button.js";

const selectors = [openSelector1, openSelector2, openSelector3, openSelector4, openSelector5];

export function renderChat(context) {
  const root = el("section", { class: "chat-panel panel", "aria-label": "Chat" });
  const top = el("header", { class: "topbar" },
    el("div", { class: "brand" }, el("span", { class: "brand-mark", "aria-hidden": "true", text: "✳" }),
      el("div", {}, el("h1", { text: context.config.title }), el("span", { class: "muted", text: "Wordflow · Chat" }))),
    namedButton(context, "configure", () => context.showSettings(), "ghost"));
  const mode = context.config.modes.find(item => item.id === context.selection.modeId);
  const model = context.config.models.find(item => item.id === context.selection.modelId);
  const controls = el("nav", { class: "control-row", "aria-label": "Modelos y modos" },
    namedButton(context, "models", () => openModels(context), "pill", model?.label || context.config.labels.models),
    namedButton(context, "modes", () => openModes(context), "pill", mode?.label || context.config.labels.modes));
  const selectorBar = el("div", { class: "selector-row", "aria-label": "Selectores configurables" });
  context.config.selectors.forEach((slot, i) => {
    const node = button(slot.label, () => selectors[i](context), "chip");
    if (slot.description) node.title = slot.description;
    selectorBar.append(node);
  });
  const toggleBar = el("div", { class: "toggle-row", "aria-label": "Ocho controles configurables" });
  context.config.toggles.forEach(slot => {
    const node = button(slot.label, async () => {
      const enabled = !context.selection.toggles[slot.id];
      node.disabled = true;
      try {
        await context.execute(slot.actionId, { controlId: slot.id, enabled });
        context.selection.toggles[slot.id] = enabled;
        node.setAttribute("aria-pressed", String(enabled));
        context.notice(`${slot.label}: ${enabled ? "encendido" : "apagado"} confirmado.`);
      } catch (error) { context.notice(error.message, true); }
      finally { node.disabled = false; }
    }, "toggle");
    if (slot.description) node.title = slot.description;
    node.setAttribute("aria-pressed", String(!!context.selection.toggles[slot.id]));
    toggleBar.append(node);
  });
  const welcome = context.messages.length ? null : el("div", { class: "welcome" },
    el("span", { class: "welcome-icon", "aria-hidden": "true", text: "✳" }),
    el("h2", { text: "¿Qué vamos a construir hoy?" }),
    el("p", { class: "muted", text: context.config.description }));
  const stream = messageStream(context);
  const { input, list } = attachments(context);
  const textarea = el("textarea", { rows: "2", placeholder: "Escribe un mensaje…", "aria-label": "Mensaje" });
  textarea.value = context.draft;
  textarea.addEventListener("input", () => { context.draft = textarea.value; });
  const send = namedButton(context, "send", () => sendMessage(context, textarea, send), "primary");
  textarea.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) { event.preventDefault(); send.click(); }
  });
  const voice = namedButton(context, "voice", () => toggleRecording(context, voice), "ghost", context.recorder?.state === "recording" ? `Detener ${context.config.labels.voice}` : context.config.labels.voice);
  const watchdog = namedButton(context, "watchdog", async () => {
    try { await context.execute(context.config.watchdogActionId); context.notice("Watchdog: confirmado por el backend."); }
    catch (error) { context.notice(error.message, true); }
  }, "ghost");
  const toolbar = el("div", { class: "composer-tools" },
    namedButton(context, "functions", () => openActions(context), "ghost"),
    namedButton(context, "attach", () => input.click(), "ghost"),
    namedButton(context, "skills", () => openSkills(context), "ghost"),
    namedButton(context, "connectors", () => openConnectors(context), "ghost"),
    voice, watchdog, send);
  const composer = el("div", { class: "composer" }, list, input, textarea, toolbar);
  root.append(top, controls, selectorBar, toggleBar, el("main", { class: "conversation" }, ...(welcome ? [welcome] : []), stream), composer);
  return root;
}
