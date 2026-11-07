# ROUTER MVP v1/audit/hf_audit.py
# Inventario REAL de los Spaces/Datasets/Modelos de Hugging Face del titular del token.
# Se ejecuta DENTRO del Job de HF (HF_TOKEN presente en el entorno).
# Salida: ROUTER MVP v1/audit/HF_INVENTORY.json (ruta relativa al repo, CWD = raiz del repo).
# Regla: NUNCA se escribe el valor de un secreto, solo el NOMBRE y su ubicacion.
import json
import os
import sys
import datetime
from huggingface_hub import HfApi

OUT_PATH = "ROUTER MVP v1/audit/HF_INVENTORY.json"


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _safe(fn, default=None):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001 - la auditoria no debe morir por un endpoint
        return {"__error__": "{}: {}".format(type(e).__name__, e)}


def _ts(value):
    if value is None:
        return None
    iso = getattr(value, "isoformat", None)
    if callable(iso):
        try:
            return iso()
        except Exception:  # noqa: BLE001
            pass
    return str(value)


def _plain(value):
    """Convierte un objeto del hub (SpaceInfo/Runtime/...) en un dict JSON-safe."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_plain(v) for v in value]
    if hasattr(value, "isoformat"):
        return _ts(value)
    if hasattr(value, "model_dump"):
        try:
            return _plain(value.model_dump())
        except Exception:  # noqa: BLE001
            pass
    if hasattr(value, "__dict__"):
        return {
            k: _plain(v)
            for k, v in vars(value).items()
            if not k.startswith("_") and not callable(v)
        }
    return str(value)


def _runtime_of(info):
    rt = getattr(info, "runtime", None)
    if rt is None:
        return None
    stage = getattr(rt, "stage", None)
    hw = getattr(rt, "hardware", None)
    req = getattr(rt, "requested_hardware", None)
    if isinstance(hw, dict):
        cur = hw.get("current")
        rq = hw.get("requested")
    else:
        cur = hw
        rq = req
    storage = getattr(rt, "storage", None)
    return {
        "stage": stage,
        "hardware_current": cur,
        "hardware_requested": rq,
        "storage_current": getattr(storage, "current", None) if storage else None,
        "sleep_time": getattr(rt, "sleep_time", None),
        "volumes": _plain(getattr(rt, "volumes", None)),
    }


def _space_entry(api, space_id):
    """Datos reales de un Space: hardware, runtime, secretos (solo nombres) y ficheros."""
    entry = {"id": space_id, "repo_type": "space"}
    info = _safe(lambda: api.space_info(space_id))
    if info is not None and not (isinstance(info, dict) and "__error__" in info):
        entry["private"] = getattr(info, "private", None)
        entry["sha"] = getattr(info, "sha", None)
        entry["created_at"] = _ts(getattr(info, "created_at", None))
        entry["last_modified"] = _ts(getattr(info, "last_modified", None))
        entry["tags"] = _plain(getattr(info, "tags", None))
        entry["sdk"] = getattr(info, "sdk", None)
        entry["likes"] = getattr(info, "likes", None)
        entry["runtime"] = _runtime_of(info)
    else:
        entry["runtime"] = {"__error__": "space_info no disponible: {}".format(info)}
        entry["secret_names"] = {"__error__": "space_info no disponible"}

    # SECRETOS: la API devuelve nombre -> SpaceSecret (sin valor). Solo se guardan los NOMBRES.
    secrets = _safe(lambda: sorted(list(api.get_space_secrets(space_id).keys())))
    if isinstance(secrets, dict):
        entry["secret_names_error"] = secrets
        entry["secret_names"] = []
    else:
        entry["secret_names"] = secrets

    files = _safe(lambda: sorted(api.list_repo_files(space_id, repo_type="space")))
    if isinstance(files, dict):
        entry["files_error"] = files
        entry["files_count"] = None
        entry["files"] = []
    else:
        entry["files_count"] = len(files)
        entry["files"] = files
    return entry


def _repo_entry(api, repo_id, repo_type):
    entry = {"id": repo_id, "repo_type": repo_type}
    info = _safe(lambda: api.repo_info(repo_id, repo_type=repo_type))
    if info is not None and not (isinstance(info, dict) and "__error__" in info):
        entry["private"] = getattr(info, "private", None)
        entry["sha"] = getattr(info, "sha", None)
        entry["created_at"] = _ts(getattr(info, "created_at", None))
        entry["last_modified"] = _ts(getattr(info, "last_modified", None))
        entry["tags"] = _plain(getattr(info, "tags", None))
        entry["likes"] = getattr(info, "likes", None)
        entry["downloads"] = getattr(info, "downloads", None)
        entry["used_storage"] = getattr(info, "used_storage", None)
    else:
        entry["info_error"] = info

    files = _safe(lambda: sorted(api.list_repo_files(repo_id, repo_type=repo_type)))
    if isinstance(files, dict):
        entry["files_error"] = files
        entry["files_count"] = None
        entry["files"] = []
    else:
        entry["files_count"] = len(files)
        entry["files"] = files
    return entry


def main():
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("ERROR: HF_TOKEN no esta definido en el Job")
        return 1

    api = HfApi(token=token)
    who = _safe(lambda: api.whoami())
    if not isinstance(who, dict) or "__error__" in who:
        print("ERROR: whoami fallo: {}".format(who))
        return 1
    namespace = who.get("name")
    print("Inventario HF del namespace: {}".format(namespace))

    # list_* devuelven generadores de objetos (SpaceInfo/DatasetInfo/ModelInfo): se extrae el .id
    space_ids = _safe(lambda: sorted(o.id for o in api.list_spaces(author=namespace))) or []
    dataset_ids = _safe(lambda: sorted(o.id for o in api.list_datasets(author=namespace))) or []
    model_ids = _safe(lambda: sorted(o.id for o in api.list_models(author=namespace))) or []

    if isinstance(space_ids, dict):
        space_ids = []
    if isinstance(dataset_ids, dict):
        dataset_ids = []
    if isinstance(model_ids, dict):
        model_ids = []

    print("Spaces encontrados: {}".format(len(space_ids)))
    print("Datasets encontrados: {}".format(len(dataset_ids)))
    print("Modelos encontrados: {}".format(len(model_ids)))

    spaces = [_space_entry(api, s) for s in space_ids]
    datasets = [_repo_entry(api, d, "dataset") for d in dataset_ids]
    models = [_repo_entry(api, m, "model") for m in model_ids]

    hw = {}
    for s in spaces:
        rt = s.get("runtime") or {}
        cur = rt.get("hardware_current")
        hw[str(cur)] = hw.get(str(cur), 0) + 1

    inventory = {
        "generated_at": _now(),
        "generated_by": "hf_audit.py dentro de un Job real de Hugging Face",
        "job_context": {
            "namespace": namespace,
            "hf_username_env": os.environ.get("HF_USERNAME"),
            "job_id": os.environ.get("HF_JOB_ID"),
        },
        "counts": {
            "spaces": len(spaces),
            "datasets": len(datasets),
            "models": len(models),
        },
        "hardware_histogram": hw,
        "spaces": spaces,
        "datasets": datasets,
        "models": models,
    }

    out_dir = os.path.dirname(OUT_PATH) or "."
    os.makedirs(out_dir, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(inventory, fh, indent=2, ensure_ascii=False, sort_keys=False, default=_plain)

    with open(os.path.join(out_dir, "HF_INVENTORY.summary.txt"), "w", encoding="utf-8") as fh:
        fh.write("namespace={}\n".format(namespace))
        fh.write("spaces={} datasets={} models={}\n".format(len(spaces), len(datasets), len(models)))
        for s in spaces:
            rt = s.get("runtime") or {}
            fh.write(
                "SPACE {} stage={} hw={} req={} files={} secrets={}\n".format(
                    s["id"],
                    rt.get("stage"),
                    rt.get("hardware_current"),
                    rt.get("hardware_requested"),
                    s.get("files_count"),
                    len(s.get("secret_names") or []),
                )
            )

    print("Inventario guardado en {}".format(OUT_PATH))
    print("   Spaces encontrados: {}".format(len(spaces)))
    print("   Datasets encontrados: {}".format(len(datasets)))
    print("   Modelos encontrados: {}".format(len(models)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
