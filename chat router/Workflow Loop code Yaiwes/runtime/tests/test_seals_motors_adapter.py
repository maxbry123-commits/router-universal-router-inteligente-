"""S-07A: motores canónicos como Native Toolset — runtime test Motor 5."""
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

_MOTORS = Path(__file__).resolve().parents[2] / "wordflow_loop" / "adapters" / "seals_motors"


def test_seis_motores_presentes_y_verificados_en_manifest():
    manifest = json.loads((_MOTORS.parent.parent / "contracts" / "seals_motors" / "manifest.json").read_text())
    assert manifest["all_verified"] is True
    assert len(manifest["motors"]) == 6
    for name, row in manifest["motors"].items():
        assert row["sha256"] == row["readback_sha256"], name


def test_motor5_zip_root_runtime(tmp_path):
    src = tmp_path / "src"
    (src / "sub").mkdir(parents=True)
    (src / "sub" / "f.txt").write_text("hello")
    out_zip = tmp_path / "out.zip"
    manifest = tmp_path / "man.json"
    env = {**os.environ, "ROOT_DIR": str(src), "OUTPUT_ZIP": str(out_zip),
           "MANIFEST_PATH": str(manifest)}
    proc = subprocess.run([sys.executable, str(_MOTORS / "motor_5_zip_root.py")],
                          env=env, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout[-500:]
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload.get("verdict") == "VERIFIED_CLOSED"
    with zipfile.ZipFile(out_zip) as z:
        assert "sub/f.txt" in z.namelist()
    m = json.loads(manifest.read_text())
    assert m.get("schema") == "yaiwes.root-zip.v1"


def test_contracts_traducen_structured_action_a_inputs():
    import json as j
    for name in ("motor_1_extract_only", "motor_3_copy_batches", "motor_5_zip_root"):
        c = j.loads((_MOTORS.parent.parent / "contracts" / "seals_motors" / f"{name}.schema.json").read_text())
        assert c["action"] and c["inputs"], name
        assert "copia exacta" in c["rule"]
