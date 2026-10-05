document.documentElement.dataset.theme = "gris";

export function tell(message) {
  document.querySelector("#notice").textContent = message || "";
}
