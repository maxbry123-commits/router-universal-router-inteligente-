# package
# Compat HF: huggingface_hub no reexporta sus clases de error en el nivel
# superior en ninguna version publicada (verificado 0.16.0 -> 2.4.0): viven en
# huggingface_hub.errors (>=0.30) o huggingface_hub.utils (<0.30). Se reexportan
# aqui para que los modulos del paquete puedan usar
# `from huggingface_hub import HfHubHTTPError` / `RepositoryNotFoundError`.
try:  # pragma: no cover - el paquete no debe romperse si falta la dependencia
    import importlib

    import huggingface_hub as _hf

    _errors = None
    for _mod_name in ("huggingface_hub.errors", "huggingface_hub.utils"):
        try:
            _errors = importlib.import_module(_mod_name)
            break
        except ImportError:
            continue
    if _errors is not None:
        for _name in dir(_errors):
            _obj = getattr(_errors, _name)
            if (
                isinstance(_obj, type)
                and issubclass(_obj, BaseException)
                and not _obj.__module__.startswith("builtins")
            ):
                setattr(_hf, _name, _obj)
except Exception:  # pragma: no cover
    pass
