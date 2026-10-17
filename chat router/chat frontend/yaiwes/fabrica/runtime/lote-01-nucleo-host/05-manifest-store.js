/* 05-manifest-store.js
 * 1 función: persistir manifiestos de extensión SIN tocar archivos originales de ventanas.
 * Storage: localStorage + export JSON descargable.
 * Cablear: import { ManifestStore } from "./05-manifest-store.js";
 */

import { validateManifest, validateManifestList } from "./04-manifest-schema.js";

const KEY = "yaiwes.biblioteca.manifests.v1";

export class ManifestStore {
  constructor(storage) {
    this._storage = storage || (typeof localStorage !== "undefined" ? localStorage : null);
    this._items = [];
    this.load();
  }

  load() {
    if (!this._storage) {
      this._items = [];
      return this._items;
    }
    try {
      const raw = this._storage.getItem(KEY);
      const parsed = raw ? JSON.parse(raw) : [];
      const checked = validateManifestList(parsed);
      this._items = checked.values;
      return this._items;
    } catch (err) {
      this._items = [];
      return this._items;
    }
  }

  save() {
    if (!this._storage) return { ok: false, reason: "no_storage" };
    this._storage.setItem(KEY, JSON.stringify(this._items));
    return { ok: true, count: this._items.length };
  }

  list() {
    return this._items.slice().sort((a, b) => a.sequence - b.sequence);
  }

  get(id) {
    return this._items.find((m) => m.id === id) || null;
  }

  add(raw) {
    const v = validateManifest(raw);
    if (!v.ok) return { ok: false, reason: "schema", errors: v.errors };
    if (this.get(v.value.id)) return { ok: false, reason: "duplicate_id", id: v.value.id };
    this._items.push(v.value);
    this.save();
    return { ok: true, value: v.value };
  }

  remove(id) {
    const before = this._items.length;
    this._items = this._items.filter((m) => m.id !== id);
    this.save();
    return { ok: this._items.length !== before, id };
  }

  exportBlob() {
    const json = JSON.stringify({ schema: "yaiwes.manifests.v1", items: this.list() }, null, 2);
    return new Blob([json], { type: "application/json" });
  }

  download(filename) {
    const blob = this.exportBlob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename || "yaiwes-manifests.json";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  importList(list) {
    const checked = validateManifestList(list);
    let added = 0;
    checked.values.forEach((item) => {
      if (!this.get(item.id)) {
        this._items.push(item);
        added += 1;
      }
    });
    this.save();
    return { ok: true, added, rejected: checked.errors };
  }
}

export const manifests = new ManifestStore();
