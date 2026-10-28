"""README.md y MANIFEST.json de la carpeta destino: que se copio, de donde, con que sha256."""
import json
import time
from pathlib import Path

from .acciones import archivos_de, sha256

MAX_MANIFIESTO = 20000


def escribir(destino, origen, accion):
    """Escribe los dos archivos en `destino`. Si ya hay un README.md no lo pisa: usa LEEME-MOTOR.md."""
    d = Path(destino)
    if not d.is_dir():
        return None
    rels = [r for r in archivos_de(d) if r.name not in ("MANIFEST.json", "LEEME-MOTOR.md")]
    manifiesto = {str(r): {"bytes": (d / r).stat().st_size, "sha256": sha256(d / r)} for r in rels[:MAX_MANIFIESTO]}
    (d / "MANIFEST.json").write_text(json.dumps({"origen": origen, "accion": accion, "archivos": len(rels), "manifiesto": manifiesto}, ensure_ascii=False, indent=1), encoding="utf-8")
    nombre = "LEEME-MOTOR.md" if (d / "README.md").exists() and not (d / "README.md").read_text(encoding="utf-8", errors="ignore").startswith("# Motor de archivos") else "README.md"
    filas = "\n".join("| %s | %d |" % (r, (d / r).stat().st_size) for r in rels[:200])
    (d / nombre).write_text("# Motor de archivos\n\n- Origen: `%s`\n- Accion: %s\n- Fecha (UTC): %s\n- Archivos: %d\n- Verificacion: sha256 de cada archivo en `MANIFEST.json`\n\n| Archivo | Bytes |\n|---|---|\n%s\n%s"
                            % (origen, accion, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), len(rels), filas, "\n(lista recortada a 200)\n" if len(rels) > 200 else ""), encoding="utf-8")
    return nombre
