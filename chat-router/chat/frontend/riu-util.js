// riu-util.js — utilidades comunes de los componentes RUI (dividido de chat-riu2.js).
export const $ = (s, r = document) => r.querySelector(s);
export const crear = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
export const leer = (k, def) => { try { const v = JSON.parse(localStorage.getItem(k) || "null"); return v == null ? def : v; } catch (e) { return def; } };
export const escribir = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
export const SVG = (p, w = 18) => '<svg viewBox="0 0 24 24" width="' + w + '" height="' + w + '" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + p + "</svg>";
export const seguro = (f, ...a) => { try { f(...a); } catch (e) { console.warn("riu2:", f.name, e); } };
