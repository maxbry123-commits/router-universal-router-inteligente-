# ops/make_guide.py — genera kernel/GUIDE.md: bloques 1+2+3 en orden, en un solo fichero.
import pathlib
P=pathlib.Path
R=P(".")
def rd(p):
    f=R/p
    return f.read_text(encoding="utf-8") if f.exists() else ""
parts=[]
parts.append("# GUIDE.md — REPO KERNEL DSL DAG v1\n\nBloques 1+2+3 concatenados en orden. Generado por `ops/make_guide.py`; las fuentes viven en `kernel/` y `ops/`.\n")
parts.append("\n## BLOQUE 1/3 — KERNEL, GOALS, SIMULACIONES, COUNCIL, DAG\n")
for t,f in [("# 0. INPUT BLOCK (VERBATIM, FROZEN)","kernel/INPUT_BLOCK.yaml"),
            ("# 1. 12 GOALS (INPUT -> OUTPUT)","kernel/GOALS.yaml"),
            ("# 2. 4 SIMULATIONS (GAP -> BUILT-IN FIX)","kernel/SIMULATIONS.yaml"),
            ("# 3. 12-STEP ASK COUNCIL (CLOSE CRITERIA)","kernel/COUNCIL.yaml"),
            ("# 4. KERNEL — SUPREME AUTHORITY (`kernel/KERNEL.yaml`)","kernel/KERNEL.yaml"),
            ("# 4.b kernel_rules","kernel/KERNEL_RULES.yaml"),
            ("# 5. MASTER DSL DAG","kernel/DAG.yaml"),
            ("# 6. LANES","kernel/LANES.mmd")]:
    parts.append(f"\n{t}\n```yaml\n{rd(f).rstrip()}\n```\n")
parts.append("\n## BLOQUE 2/3 — ops/ code (common + J0..J4)\n")
parts.append("\nPath: ops/<file>.py in branch GH_BRANCH. Env: GH_REPO GH_BRANCH [TARGET_BRANCH] DATASET_REPO RUN_ID HF_TOKEN [GH_TOKEN].\n")
for i,f in [(7,"ops/common.py"),(8,"ops/j0_preflight.py"),(9,"ops/j1_inventory.py"),(10,"ops/j2_graph.py"),(11,"ops/j3_history.py"),(12,"ops/j4_plan.py")]:
    parts.append(f"\n## {i}. {f} (path: {f})\n```python\n{rd(f).rstrip()}\n```\n")
parts.append("\n## BLOQUE 3/3 — J5..J8, wiring_check, kernel.py, launcher, failure sources, recommendations\n")
for i,f in [(13,"ops/wiring_check.py"),(14,"ops/j5_apply.py"),(15,"ops/j7_mirror.py"),(16,"ops/j8_audit.py"),(17,"ops/j6_rewrite.py"),(18,"ops/kernel.py")]:
    parts.append(f"\n## {i}. {f} (path: {f})\n```python\n{rd(f).rstrip()}\n```\n")
parts.append("\n## 19. LANZADOR DE JOBS\n```bash\n"+rd("ops/launch.sh").rstrip()+"\n```\n")
parts.append("\n"+rd("kernel/GUIDE_tail.md").rstrip()+"\n")
parts.append("\n## ANEXO — ROADMAP U1 (catálogo único) y utilidades\n")
for f in ["ops/patterns.py","ops/j11_patterns.py","ops/test_patterns.py","ops/make_registry.py","ops/make_guide.py"]:
    parts.append(f"\n### {f}\n```python\n{rd(f).rstrip()}\n```\n")
out=R/"kernel/GUIDE.md"
out.write_text("".join(parts),encoding="utf-8")
print("kernel/GUIDE.md:",out.stat().st_size,"bytes")
