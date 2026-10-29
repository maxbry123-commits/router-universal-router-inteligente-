from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SUITES = [
    REPO / "dataset Yaiwes" / "tests" / "test_data.py",
    HERE / "tests" / "test_router.py",
    HERE / "tests" / "test_control.py",
    HERE / "tests" / "test_integration.py",
]


def load_module(path: Path):
    name = "yaiwes_verify_" + path.stem + "_" + str(abs(hash(str(path))))
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    passed = 0
    failed = 0
    details = []
    for suite in SUITES:
        module = load_module(suite)
        tests = sorted((name, value) for name, value in vars(module).items()
                       if name.startswith("test_") and callable(value))
        if not tests:
            failed += 1
            details.append((str(suite), "NO_TESTS", "no test_* callables found"))
            continue
        for name, func in tests:
            label = f"{suite.relative_to(REPO)}::{name}"
            try:
                func()
            except Exception as exc:
                failed += 1
                details.append((label, "FAIL", f"{type(exc).__name__}: {exc}"))
                traceback.print_exc()
            else:
                passed += 1
                details.append((label, "PASS", ""))
    for label, state, note in details:
        print(f"[{state}] {label}{': ' + note if note else ''}")
    print(f"YAIWES_VERIFY_SUMMARY passed={passed} failed={failed} total={passed + failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
