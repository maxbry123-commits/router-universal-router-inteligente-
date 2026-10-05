try {
  const saved = JSON.parse(localStorage.getItem("yaiwes-ui-preferences"));
  if (["gris", "little", "matte", "blanco"].includes(saved?.theme)) document.documentElement.dataset.theme = saved.theme;
  if (saved?.reducedMotion === true) document.documentElement.dataset.reducedMotion = "true";
  if (Number.isInteger(saved?.scale) && saved.scale >= 85 && saved.scale <= 130) document.body.style.fontSize = `${saved.scale * 0.15}px`;
} catch {
  document.documentElement.dataset.theme = "gris";
}

export function tell(message) {
  document.querySelector("#notice").textContent = message || "";
}
