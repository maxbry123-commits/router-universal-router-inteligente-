// Cifrado de la credencial SIWC con una llave derivada de la clave del banco (mismo en dispositivo y VM).
import { createCipheriv, createDecipheriv, randomBytes, scryptSync } from "node:crypto";
export function cifradoBanco(clave) {
  if (!clave) throw new Error("falta la clave del banco");
  const llave = scryptSync(clave, "riu-chatgpt-puente-v1", 32);
  return {
    id: "riu-banco-aesgcm-v1",
    isAvailable: () => true,
    encrypt(t) { const iv = randomBytes(12); const c = createCipheriv("aes-256-gcm", llave, iv);
      const d = Buffer.concat([c.update(t, "utf8"), c.final()]); return Buffer.concat([iv, c.getAuthTag(), d]); },
    decrypt(b) { b = Buffer.from(b); const d = createDecipheriv("aes-256-gcm", llave, b.subarray(0, 12));
      d.setAuthTag(b.subarray(12, 28)); return Buffer.concat([d.update(b.subarray(28)), d.final()]).toString("utf8"); },
  };
}
