/* 06-access-key.js
 * 1 función: abrir panel de configuración solo con clave.
 * Fail-closed: hash no coincide => locked.
 * Cambiar clave: setPassphrase("tu-clave") una vez, se guarda el hash.
 * Cablear: import { AccessKey } from "./06-access-key.js";
 */

const STORE = "yaiwes.biblioteca.access.v1";
const SESSION = "yaiwes.biblioteca.session.v1";

const DEFAULT_PASSPHRASE = "YAIWES-CONFIG";

export class AccessKey {
  constructor(storage) {
    this._storage = storage || (typeof localStorage !== "undefined" ? localStorage : null);
    this._session = typeof sessionStorage !== "undefined" ? sessionStorage : null;
  }

  async _sha256(text) {
    const enc = new TextEncoder().encode(String(text));
    const buf = await crypto.subtle.digest("SHA-256", enc);
    return Array.from(new Uint8Array(buf))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  }

  _read() {
    if (!this._storage) return null;
    try {
      return JSON.parse(this._storage.getItem(STORE) || "null");
    } catch (err) {
      return null;
    }
  }

  async ensureDefault() {
    if (this._read()) return this._read();
    const hash = await this._sha256(DEFAULT_PASSPHRASE);
    const rec = { algo: "SHA-256", hash, setAt: Date.now(), defaultHint: DEFAULT_PASSPHRASE };
    if (this._storage) this._storage.setItem(STORE, JSON.stringify(rec));
    return rec;
  }

  async setPassphrase(passphrase) {
    if (!passphrase || String(passphrase).length < 8) {
      return { ok: false, reason: "passphrase_too_short" };
    }
    const hash = await this._sha256(passphrase);
    const rec = { algo: "SHA-256", hash, setAt: Date.now() };
    if (this._storage) this._storage.setItem(STORE, JSON.stringify(rec));
    this.lock();
    return { ok: true };
  }

  isUnlocked() {
    if (!this._session) return false;
    return this._session.getItem(SESSION) === "1";
  }

  lock() {
    if (this._session) this._session.removeItem(SESSION);
  }

  async unlock(passphrase) {
    const rec = await this.ensureDefault();
    const hash = await this._sha256(passphrase);
    if (hash !== rec.hash) {
      this.lock();
      return { ok: false, reason: "key_mismatch" };
    }
    if (this._session) this._session.setItem(SESSION, "1");
    return { ok: true };
  }
}

export const accessKey = new AccessKey();
