# package
# Compat HF: huggingface_hub no reexporta sus clases de error en el nivel
# superior en ninguna version publicada (verificado 0.16.0 -> 2.4.0): viven en
# huggingface_hub.errors (>=0.30) o huggingface_hub.utils (<0.30). Se reexportan
# aqui para que los modulos del paquete puedan usar
# `from huggingface_hub import HfHubHTTPError` / `RepositoryNotFoundError`.
try:  # pragma: no cover - el paquete no debe romperse si falta la dependencia
    import importlib

    import huggingface_hub as _hf

    # Se recorren TODOS los modulos candidatos y se fusionan sus clases de
    # error. El `break` anterior paraba en el primero importable: con
    # huggingface_hub 0.22.2 (pin del Space) `huggingface_hub.errors` existe pero
    # NO contiene HfHubHTTPError (solo errores de generacion), de modo que los
    # errores de `huggingface_hub.utils` nunca se inyectaban y el proxy no
    # arrancaba (ImportError en external/tools/space_power_manager.py).
    for _mod_name in ("huggingface_hub.errors", "huggingface_hub.utils"):
        try:
            _errors = importlib.import_module(_mod_name)
        except ImportError:
            continue
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
