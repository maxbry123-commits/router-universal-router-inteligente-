// Compresión local de fotografías para el almacén existente (700 kB binarios; ~933 kB en base64).
// No agrega servicios, no conserva copias ni sube nada antes del usuario.
export const MAX_ARCHIVO_CHAT = 700_000;
export async function prepararImagenOArchivo(file) {
  if (!file || typeof file.size !== "number") throw new Error("ARCHIVO_INVALIDO");
  if (file.size <= MAX_ARCHIVO_CHAT) return file;
  if (!/^image\/(?:jpeg|png|webp|gif)$/i.test(file.type || "")) {
    throw new Error("ARCHIVO_MUY_GRANDE: límite del almacén 700 KB");
  }
  if (file.size > 25_000_000) throw new Error("FOTO_MUY_GRANDE: selecciona una imagen menor de 25 MB");
  if (typeof document === "undefined" || typeof createImageBitmap !== "function") {
    throw new Error("FOTO_SIN_COMPRESION: el navegador no puede adaptar la imagen (700 KB máximo)");
  }
  const imagen = await createImageBitmap(file);
  try {
    const canvas = document.createElement("canvas");
    const lado = Math.max(imagen.width, imagen.height);
    if (!lado) throw new Error("FOTO_INVALIDA");
    const base = file.name.replace(/\.[^.]+$/, "") || "foto";
    for (const dimension of [1600, 1280, 1024, 800, 640, 480]) {
      const escala = Math.min(1, dimension / lado);
      canvas.width = Math.max(1, Math.round(imagen.width * escala));
      canvas.height = Math.max(1, Math.round(imagen.height * escala));
      const ctx = canvas.getContext("2d");
      if (!ctx) throw new Error("FOTO_CANVAS_NO_DISPONIBLE");
      ctx.fillStyle = "#ffffff"; // transparencia PNG -> fondo blanco al pasar a JPEG
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(imagen, 0, 0, canvas.width, canvas.height);
      for (const calidad of [0.82, 0.68, 0.5]) {
        const blob = await new Promise(ok => canvas.toBlob(ok, "image/jpeg", calidad));
        if (blob && blob.size > 0 && blob.size <= MAX_ARCHIVO_CHAT) {
          return new File([blob], base + ".jpg", { type: "image/jpeg" });
        }
      }
    }
    throw new Error("FOTO_NO_REDUCIBLE: no se pudo comprimir bajo 700 KB");
  } finally {
    imagen.close();
  }
}
