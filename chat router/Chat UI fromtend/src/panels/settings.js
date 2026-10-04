import { button, el } from "../dom.js";
import { chatDescription, controlLabel, LANGUAGES, slotLabel, t } from "../i18n.js";
import { themePicker } from "../components/theme-picker.js";
import { DEFAULT_CONFIG } from "../config.js";
import { exportSettings, importSettings } from "../actions/settings-transfer.js";
import { openIconLibrary } from "../windows/icon-library.js";

function field(label, value, onChange, multiline = false) {
  const input = el(multiline ? "textarea" : "input", { class: "setting-input", "aria-label": label });
  if (!multiline) input.type = "text";
  input.value = value;
  input.addEventListener("input", () => onChange(input.value));
  return el("label", { class: "setting-field" }, el("span", { text: label }), input);
}

function group(title, items, context, edit) {
  const container = el("section", { class: "settings-group" }, el("h3", { text: title }));
  items.forEach((item, index) => {
    const row = el("details", { class: "setting-row" }, el("summary", { text: `${index + 1}. ${slotLabel(context, item)}` }));
    row.append(field(t(context, "name"), slotLabel(context, item), value => { item.label = value; row.querySelector("summary").textContent = `${index + 1}. ${value}`; }));
    row.append(field(t(context, "description"), item.description, value => { item.description = value; }));
    row.append(field(t(context, "actionId"), item.actionId, value => { item.actionId = value; }));
    edit?.(row, item);
    container.append(row);
  });
  return container;
}

export function renderSettings(context) {
  const draft = structuredClone(context.config);
  const replaceConfig = config => {
    const persisted = context.updateConfig(config);
    context.selection = { modelId: "", modeId: "mode-1", selectors: {}, toggles: {} };
    context.showSettings();
    return persisted;
  };
  const root = el("section", { class: "settings panel", "aria-label": t(context, "settingsAria") });
  const header = el("header", { class: "settings-header" },
    button(`← ${controlLabel(context, "back")}`, () => context.showChat(), "ghost"), el("h1", { text: t(context, "settingsTitle") }));
  const intro = el("div", { class: "settings-group" },
    el("p", { class: "muted", text: t(context, "settingsIntro") }),
    field(t(context, "chatTitle"), draft.title, value => { draft.title = value; }),
    field(t(context, "chatDescription"), chatDescription(context), value => { draft.description = value; }),
    themePicker(context, draft),
    el("label", { class: "setting-field" }, el("span", { text: t(context, "language") }), (() => {
      const select = el("select", { "aria-label": t(context, "language") });
      for (const locale of LANGUAGES) select.append(el("option", { value: locale, text: locale.toUpperCase() }));
      select.value = draft.locale;
      select.addEventListener("change", () => { draft.locale = select.value; });
      return select;
    })()));

  const commands = el("div", { class: "settings-group" }, el("h3", { text: t(context, "backendConnections") }));
  for (const key of ["modelsActionId", "modelActionId", "sendActionId", "attachActionId", "documentsActionId", "voiceActionId", "watchdogActionId", "skillsActionId", "connectorsActionId"]) {
    commands.append(field(`${t(context, key)} · actionId`, draft[key], value => { draft[key] = value; }));
  }

  const icons = el("section", { class: "settings-group" },
    el("h3", { text: t(context, "iconLibrary") }),
    el("p", { class: "muted", text: t(context, "iconLibraryDesc") }),
    button(t(context, "iconLibrary"), () => openIconLibrary(context), "ghost"));

  const typography = el("section", { class: "settings-group" },
    el("h3", { text: t(context, "typography") }),
    el("p", { class: "muted", text: t(context, "typoDesc") }),
    button(t(context, "typography"), () => openTypography(context), "ghost"));

  const transfer = el("section", { class: "settings-group" }, el("h3", { text: t(context, "configExport") }));
  const transferStatus = el("p", { role: "status" });
  const fileInput = el("input", { type: "file", accept: ".json,application/json", hidden: true, "aria-label": t(context, "configImport") });
  fileInput.addEventListener("change", async () => {
    const file = fileInput.files?.[0];
    fileInput.value = "";
    if (!file) return;
    try {
      const imported = await importSettings(file);
      if (!window.confirm(t(context, "configImportConfirm"))) return;
      const persisted = replaceConfig(imported);
      context.notice(t(context, persisted ? "configImported" : "settingsTemporary"), !persisted);
    } catch {
      transferStatus.textContent = t(context, "configInvalid");
      transferStatus.className = "error";
    }
  });
  transfer.append(
    fileInput,
    button(t(context, "configExport"), () => {
      try { exportSettings(context.config); context.notice(t(context, "configExported")); }
      catch (error) { transferStatus.textContent = error.message; transferStatus.className = "error"; }
    }),
    button(t(context, "configImport"), () => fileInput.click()),
    button(t(context, "configReset"), () => {
      if (!window.confirm(t(context, "configResetConfirm"))) return;
      const persisted = replaceConfig(DEFAULT_CONFIG);
      context.notice(t(context, persisted ? "configResetDone" : "settingsTemporary"), !persisted);
    }),
    transferStatus
  );

  const labels = el("section", { class: "settings-group" }, el("h3", { text: t(context, "namesAndDescriptions") }));
  for (const key of Object.keys(draft.labels)) {
    const row = el("details", { class: "setting-row" }, el("summary", { text: controlLabel(context, key) }));
    row.append(field(t(context, "name"), controlLabel(context, key), value => { draft.labels[key] = value; row.querySelector("summary").textContent = value; }));
    row.append(field(t(context, "description"), draft.descriptions[key], value => { draft.descriptions[key] = value; }));
    labels.append(row);
  }

  const models = el("section", { class: "settings-group" }, el("h3", { text: t(context, "modelsHeading") }),
    el("p", { class: "muted", text: t(context, "modelsInfo") }));
  const modelLines = draft.models.map(model => `${model.id} | ${model.label}`).join("\n");
  let modelsText = modelLines;
  models.append(field(t(context, "modelsField"), modelLines, value => { modelsText = value; }, true));
  const selectors = group(t(context, "selectorGroup"), draft.selectors, context, (row, item) => {
    let text = item.options.map(option => `${option.id} | ${option.label} | ${option.actionId}`).join("\n");
    row.append(field(t(context, "optionsField"), text, value => { text = value; item.options = text.split("\n").filter(line => line.trim()).map(line => {
      const [id, label, actionId] = line.split("|").map(part => part.trim());
      return { id, label, actionId };
    }); }, true));
  });
  const feedback = el("p", { class: "error", role: "alert" });
  const save = button(controlLabel(context, "save"), () => {
    const lines = modelsText.split("\n").filter(line => line.trim());
    if (lines.some(line => !line.includes("|"))) { feedback.textContent = t(context, "modelsFormat"); return; }
    draft.models = lines.map(line => { const [id, label] = line.split("|").map(part => part.trim()); return { id, label }; });
    if (draft.models.some(model => !model.id || !model.label) || draft.selectors.some(slot => slot.options.some(option => !option.id || !option.label))) {
      feedback.textContent = t(context, "missingNames"); return;
    }
    try {
      const persisted = context.updateConfig(draft);
      context.showChat();
      context.notice(t(context, persisted ? "settingsSaved" : "settingsTemporary"), !persisted);
    }
    catch (error) { feedback.textContent = error.message; }
  }, "primary");
  root.append(header, intro, icons, commands, labels, models, group(t(context, "modesGroup"), draft.modes, context), selectors,
    group(t(context, "togglesGroup"), draft.toggles, context), group(t(context, "actionsGroup"), draft.actions, context), transfer, feedback, save);
  return root;
}
