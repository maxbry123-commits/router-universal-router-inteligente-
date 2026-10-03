import { button, el } from "../dom.js";

function field(label, value, onChange, multiline = false) {
  const input = el(multiline ? "textarea" : "input", { class: "setting-input", "aria-label": label });
  if (!multiline) input.type = "text";
  input.value = value;
  input.addEventListener("input", () => onChange(input.value));
  return el("label", { class: "setting-field" }, el("span", { text: label }), input);
}

function group(title, items, edit) {
  const container = el("section", { class: "settings-group" }, el("h3", { text: title }));
  items.forEach((item, index) => {
    const row = el("details", { class: "setting-row" }, el("summary", { text: `${index + 1}. ${item.label}` }));
    row.append(field("Nombre", item.label, value => { item.label = value; row.querySelector("summary").textContent = `${index + 1}. ${value}`; }));
    row.append(field("Descripción", item.description, value => { item.description = value; }));
    row.append(field("Comando de acción (actionId)", item.actionId, value => { item.actionId = value; }));
    edit?.(row, item);
    container.append(row);
  });
  return container;
}

export function renderSettings(context) {
  const draft = structuredClone(context.config);
  const root = el("section", { class: "settings panel", "aria-label": "Configuración del chat" });
  const header = el("header", { class: "settings-header" },
    button(`← ${draft.labels.back}`, () => context.showChat(), "ghost"), el("h1", { text: "Configuración" }));
  const intro = el("div", { class: "settings-group" },
    el("p", { class: "muted", text: "Aquí se editan nombres, descripciones y actionId. Nunca pegues claves, contraseñas ni código ejecutable: el bridge seguro implementa los comandos." }),
    field("Título del chat", draft.title, value => { draft.title = value; }),
    field("Descripción del chat", draft.description, value => { draft.description = value; }),
    el("label", { class: "setting-field" }, el("span", { text: "Tema" }), (() => {
      const select = el("select", { "aria-label": "Tema" });
      for (const name of ["little", "matte", "blanco"]) {
        const option = el("option", { value: name, text: name });
        select.append(option);
      }
      select.value = draft.theme;
      select.addEventListener("change", () => { draft.theme = select.value; });
      return select;
    })()));

  const commands = el("div", { class: "settings-group" }, el("h3", { text: "Conexiones de backend" }));
  for (const [key, label] of Object.entries({
    modelsActionId: "Cargar catálogo de modelos", modelActionId: "Seleccionar modelo", sendActionId: "Enviar mensaje",
    attachActionId: "Subir adjunto", voiceActionId: "Enviar voz", watchdogActionId: "Watchdog",
    skillsActionId: "Listar habilidades", connectorsActionId: "Listar conectores",
  })) commands.append(field(`${label} · actionId`, draft[key], value => { draft[key] = value; }));

  const labels = el("section", { class: "settings-group" }, el("h3", { text: "Nombres y descripciones de botones" }));
  for (const key of Object.keys(draft.labels)) {
    const row = el("details", { class: "setting-row" }, el("summary", { text: draft.labels[key] }));
    row.append(field("Nombre", draft.labels[key], value => { draft.labels[key] = value; row.querySelector("summary").textContent = value; }));
    row.append(field("Descripción", draft.descriptions[key], value => { draft.descriptions[key] = value; }));
    labels.append(row);
  }

  const models = el("section", { class: "settings-group" }, el("h3", { text: "Modelos" }),
    el("p", { class: "muted", text: "Un modelo por línea: id | nombre. Si tienes catálogo remoto, configura también su comando." }));
  const modelLines = draft.models.map(model => `${model.id} | ${model.label}`).join("\n");
  let modelsText = modelLines;
  models.append(field("Modelos (id | nombre)", modelLines, value => { modelsText = value; }, true));
  const selectors = group("5 selectores · una ventana por selector", draft.selectors, (row, item) => {
    let text = item.options.map(option => `${option.id} | ${option.label} | ${option.actionId}`).join("\n");
    row.append(field("Opciones: id | nombre | actionId (una por línea)", text, value => { text = value; item.options = text.split("\n").filter(line => line.trim()).map(line => {
      const [id, label, actionId] = line.split("|").map(part => part.trim());
      return { id, label, actionId };
    }); }, true));
  });
  const feedback = el("p", { class: "error", role: "alert" });
  const save = button(draft.labels.save, () => {
    const lines = modelsText.split("\n").filter(line => line.trim());
    if (lines.some(line => !line.includes("|"))) { feedback.textContent = "Cada modelo necesita id | nombre."; return; }
    draft.models = lines.map(line => { const [id, label] = line.split("|").map(part => part.trim()); return { id, label }; });
    if (draft.models.some(model => !model.id || !model.label) || draft.selectors.some(slot => slot.options.some(option => !option.id || !option.label))) {
      feedback.textContent = "Completa id y nombre en los modelos y opciones."; return;
    }
    try { context.updateConfig(draft); context.showChat(); context.notice("Configuración guardada localmente. Los comandos remotos requieren un bridge real."); }
    catch (error) { feedback.textContent = error.message; }
  }, "primary");
  root.append(header, intro, commands, labels, models, group("8 niveles de razonamiento", draft.modes), selectors,
    group("8 controles de encendido", draft.toggles), group("12 funciones del menú +", draft.actions), feedback, save);
  return root;
}
