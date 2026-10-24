// ventana-servidor.js — Servidor del Router: encender / apagar / reiniciar el Space. La orden sale de /api/power en Vercel (el Router dormido no puede recibirla).
import { el, btn, ventana } from "./ventanas-control.js";
const ESTILO = { RUNNING: "enabled", PAUSED: "pending", SLEEPING: "pending", STOPPED: "pending", BUILDING: "progress", APP_STARTING: "progress", RUNNING_BUILDING: "progress" };
async function power(metodo, accion) {
  const r = await fetch("/api/power", { method: metodo, headers: { "Content-Type": "application/json", "X-API-Key": sessionStorage.getItem("riu_clave") || "" }, body: accion ? JSON.stringify({ accion }) : undefined });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(r.status === 401 ? "clave incorrecta (usa la del chat)" : r.status === 404 ? "disponible solo en la web de Vercel" : r.status === 402 ? "Hugging Face: faltan créditos (" + (d.detail || "402") + ")" : d.detail || "HTTP " + r.status);
  return d;
}
async function pintarPower(cuerpo) {
  const est = el("div", "cv-est"), chip = el("span", "tag-status pending", "…"), hw = el("div", "muted"); let espera = 0;
  const ver = (d) => { chip.className = "tag-status " + (/ERROR/.test(d.stage || "") ? "warning" : ESTILO[d.stage] || "pending"); chip.textContent = d.stage || "sin estado"; hw.textContent = d.hardware ? "Hardware: " + d.hardware + (d.hardware === "cpu-basic" ? " (gratis)" : " · el hardware de pago consume créditos") : ""; return d; };
  const leer = async () => { try { return ver(await power("GET")); } catch (x) { chip.className = "tag-status warning"; chip.textContent = "error"; est.textContent = "⚠️ " + x.message; return null; } };
  const seguir = async () => { const mia = ++espera; for (let i = 0; i < 60 && mia === espera; i++) { await new Promise((r) => setTimeout(r, 5000)); const d = await leer(); if (!d) return; if (d.stage === "RUNNING") { est.textContent = "✅ listo: el Router está encendido"; return; } if (/ERROR/.test(d.stage || "")) { est.textContent = "⚠️ el Space terminó en " + d.stage; return; } } if (mia === espera) est.textContent = "⚠️ sigue arrancando tras 5 minutos; revisa el Space"; };
  const boton = (texto, accion, confirmar) => { const b = btn(texto, "secondary"); let t = 0;
    const lanzar = async () => { b.disabled = true; est.textContent = "Enviando " + accion + "…"; try { ver(await power("POST", accion)); est.textContent = accion === "apagar" ? "Pausa pedida" : "Arrancando… (consulto cada 5 s)"; if (accion !== "apagar") seguir(); else { espera++; setTimeout(leer, 4000); } } catch (x) { est.textContent = "⚠️ " + x.message; } finally { b.disabled = false; b.textContent = texto; } };
    b.onclick = () => { if (!confirmar) return lanzar(); if (t) { clearTimeout(t); t = 0; return lanzar(); } b.textContent = "¿Seguro? Confirmar"; est.textContent = "Pulsa de nuevo para " + accion + " el Router"; t = setTimeout(() => { t = 0; b.textContent = texto; est.textContent = ""; }, 5000); }; return b; };
  const fila = el("div", "cv-form"); fila.append(boton("Encender", "encender", false), boton("Apagar", "apagar", true), boton("Reiniciar", "reiniciar", true), btn("Actualizar", "secondary", leer));
  cuerpo.replaceChildren(el("div", "cv-sec", "Servidor del Router"), el("div", "cv-fila", ""), hw, fila, est); cuerpo.children[1].append(chip);
  await leer();
}
const montar = () => ventana("power", "Servidor del Router", pintarPower);
new MutationObserver(montar).observe(document.body, { childList: true, subtree: true });
montar();
