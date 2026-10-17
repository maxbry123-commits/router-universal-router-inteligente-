/* 04-manifest-schema.js
 * 1 función: validar manifiesto de ventana o botón.
 * Fail-closed: inválido => REJECT, no pintar.
 * Cablear: import { validateManifest, MANIFEST_KINDS } from "./04-manifest-schema.js";
 */

export const MANIFEST_KINDS = Object.freeze({
  window: "window",
  group: "group",
  button: "button",
  toggle: "toggle",
  separator: "separator"
});

export const MANIFEST_SIZES = Object.freeze({
  small: "small",
  regular: "regular",
  large: "large"
});

const ID_RE = /^[a-z][a-z0-9._-]{1,63}$/;

function fail(errors, field, msg) {
  errors.push({ field, msg });
}

export function validateManifest(raw) {
  const errors = [];
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    return { ok: false, errors: [{ field: "$", msg: "manifesto no es objeto" }] };
  }

  if (!ID_RE.test(String(raw.id || ""))) {
    fail(errors, "id", "id kebab/dot minúsculas, 2-64 chars");
  }
  if (!MANIFEST_KINDS[raw.kind]) {
    fail(errors, "kind", "kind debe ser window|group|button|toggle|separator");
  }
  if (typeof raw.label !== "string" || !raw.label.trim()) {
    fail(errors, "label", "label requerido");
  }

  if (raw.kind === "window") {
    if (typeof raw.slotId !== "string" || !raw.slotId.trim()) {
      fail(errors, "slotId", "ventana requiere slotId propio");
    }
  } else {
    if (typeof raw.targetSlot !== "string" || !raw.targetSlot.trim()) {
      fail(errors, "targetSlot", "control requiere targetSlot de ventana existente");
    }
  }

  if (raw.kind === "button" || raw.kind === "toggle") {
    if (typeof raw.action !== "string" || !raw.action.trim()) {
      fail(errors, "action", "button/toggle requieren action id");
    }
    if (raw.size && !MANIFEST_SIZES[raw.size]) {
      fail(errors, "size", "size small|regular|large");
    }
  }

  if (raw.icon != null && typeof raw.icon !== "string") {
    fail(errors, "icon", "icon string o omitir");
  }
  if (raw.acl != null && typeof raw.acl !== "string") {
    fail(errors, "acl", "acl string o omitir");
  }
  if (raw.sequence != null && !Number.isFinite(Number(raw.sequence))) {
    fail(errors, "sequence", "sequence número");
  }

  return errors.length ? { ok: false, errors } : { ok: true, errors: [], value: normalize(raw) };
}

function normalize(raw) {
  return {
    id: String(raw.id),
    kind: String(raw.kind),
    label: String(raw.label).trim(),
    targetSlot: raw.targetSlot ? String(raw.targetSlot) : null,
    slotId: raw.slotId ? String(raw.slotId) : null,
    action: raw.action ? String(raw.action) : null,
    icon: raw.icon ? String(raw.icon) : "",
    size: raw.size && MANIFEST_SIZES[raw.size] ? raw.size : "regular",
    acl: raw.acl ? String(raw.acl) : "config-key",
    sequence: Number.isFinite(Number(raw.sequence)) ? Number(raw.sequence) : 100,
    enabled: raw.enabled === false ? false : true,
    origin: raw.origin === "builtin" ? "builtin" : "library"
  };
}

export function validateManifestList(list) {
  if (!Array.isArray(list)) {
    return { ok: false, errors: [{ field: "$", msg: "lista no es array" }], values: [] };
  }
  const values = [];
  const errors = [];
  list.forEach((item, i) => {
    const r = validateManifest(item);
    if (!r.ok) {
      r.errors.forEach((e) => errors.push({ index: i, ...e }));
    } else {
      values.push(r.value);
    }
  });
  return { ok: errors.length === 0, errors, values };
}
