import { tell } from "./base.js";

const key = "yaiwes-ui-preferences";
const defaults = { theme: "gris", scale: 100, reducedMotion: false };
const themes = ["gris", "little", "matte", "blanco"];

function validate(value) {
  if (!value || !themes.includes(value.theme) ||
    !Number.isInteger(value.scale) || value.scale < 85 || value.scale > 130 ||
    typeof value.reducedMotion !== "boolean") throw new Error("Ajustes no válidos.");
  return { theme: value.theme, scale: value.scale, reducedMotion: value.reducedMotion };
}

function stored() {
  try { return validate(JSON.parse(localStorage.getItem(key))); }
  catch { return { ...defaults }; }
}

function apply(preferences) {
  document.documentElement.dataset.theme = preferences.theme;
  document.documentElement.dataset.reducedMotion = String(preferences.reducedMotion);
  document.body.style.fontSize = `${preferences.scale * 0.15}px`;
}

export function mount(root) {
  let exportUrl;
  let preferences = stored();
  const status = root.querySelector("#preferences-status");
  const theme = root.querySelector("#ui-theme");
  const scale = root.querySelector("#ui-scale");
  const motion = root.querySelector("#ui-motion");
  const cards = [...root.querySelectorAll("[data-theme-choice]")];

  const updateTokens = () => {
    const computed = getComputedStyle(document.documentElement);
    for (const item of root.querySelectorAll("[data-token]")) {
      const token = item.dataset.token;
      item.textContent = computed.getPropertyValue(token).trim() || "—";
    }
  };

  const render = () => {
    apply(preferences);
    theme.value = preferences.theme;
    scale.value = preferences.scale;
    motion.checked = preferences.reducedMotion;
    root.querySelector("#scale-value").value = `${preferences.scale} %`;
    for (const card of cards) card.setAttribute("aria-pressed", String(card.dataset.themeChoice === preferences.theme));
    requestAnimationFrame(updateTokens);
  };

  const persist = message => {
    try {
      localStorage.setItem(key, JSON.stringify(preferences));
      status.textContent = message || "Ajustes guardados automáticamente.";
      status.dataset.state = "ok";
    } catch {
      status.textContent = "Ajustes activos sólo en esta pestaña; el navegador no permitió guardarlos.";
      status.dataset.state = "pending";
    }
  };

  const saveFromControls = message => {
    preferences = validate({ theme: theme.value, scale: Number(scale.value), reducedMotion: motion.checked });
    render();
    persist(message);
  };

  for (const card of cards) {
    card.addEventListener("click", () => {
      theme.value = card.dataset.themeChoice;
      saveFromControls(`Paleta ${card.querySelector("strong")?.textContent || card.dataset.themeChoice} aplicada y guardada.`);
    });
  }

  for (const item of root.querySelectorAll("[data-token]")) {
    item.title = "Copiar valor";
    item.tabIndex = 0;
    item.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); item.click(); } });
    item.addEventListener("click", async () => {
      const value = item.textContent;
      if (!value || value === "—") return;
      try {
        await navigator.clipboard.writeText(value);
        status.textContent = `${item.dataset.token} copiado: ${value}`;
        status.dataset.state = "ok";
      } catch {
        status.textContent = "El navegador no permitió copiar.";
        status.dataset.state = "error";
      }
    });
  }

  scale.addEventListener("input", () => saveFromControls("Tamaño de texto aplicado y guardado."));
  motion.addEventListener("change", () => saveFromControls(motion.checked ? "Animaciones reducidas." : "Animaciones normales."));

  root.querySelector("#ui-reset").addEventListener("click", () => {
    preferences = { ...defaults };
    render();
    persist("Gris V07 y ajustes predeterminados restaurados.");
  });

  root.querySelector("#ui-export").addEventListener("click", () => {
    if (exportUrl) URL.revokeObjectURL(exportUrl);
    exportUrl = URL.createObjectURL(new Blob([JSON.stringify(preferences, null, 2)], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = exportUrl;
    link.download = "yaiwes-ui-preferences.json";
    link.click();
    status.textContent = "Ajustes exportados.";
    status.dataset.state = "ok";
  });

  root.querySelector("#ui-copy").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(preferences, null, 2));
      status.textContent = "Ajustes copiados al portapapeles.";
      status.dataset.state = "ok";
    } catch {
      status.textContent = "El navegador no permitió copiar al portapapeles.";
      status.dataset.state = "error";
    }
  });

  root.querySelector("#ui-import").addEventListener("change", async event => {
    const file = event.target.files[0];
    if (!file) return;
    try {
      if (file.size > 10240) throw new Error("Archivo JSON demasiado grande.");
      preferences = validate(JSON.parse(await file.text()));
      render();
      persist("Ajustes importados y aplicados.");
    } catch (error) {
      status.textContent = error.message;
      status.dataset.state = "error";
    }
    event.target.value = "";
  });

  render();
  status.textContent = "Preferencias listas · autoguardado activo.";
  status.dataset.state = "ok";

  return () => { if (exportUrl) URL.revokeObjectURL(exportUrl); };
}

try { mount(document); }
catch (error) { tell(error.message); }
