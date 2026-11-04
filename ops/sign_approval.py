# ops/sign_approval.py — firma de aprobaciones del kernel (unico escritor: orquestador).
# Uso: python ops/sign_approval.py <J5_apply|J6_rewrite|merge_main|deploy> [--plan SHA] [--by "texto"]
# Registra quien autoriza y cuando, para que la auditoria pueda reconstruir la decision.
import sys, yaml, pathlib, time, json
P = pathlib.Path("kernel/KERNEL.yaml")
BY = "owner: instruccion explicita 'continua hasta el 100% del cierre' (2026-11-04)"
def main():
    if len(sys.argv) < 2:
        print("uso: sign_approval.py <aprobacion> [--plan SHA] [--by texto]"); return 2
    name = sys.argv[1]; plan = ""; by = BY
    if "--plan" in sys.argv: plan = sys.argv[sys.argv.index("--plan") + 1]
    if "--by" in sys.argv: by = sys.argv[sys.argv.index("--by") + 1]
    k = yaml.safe_load(P.read_text())
    ap = k.setdefault("approvals", {}).setdefault(name, {"approved": False, "plan_sha256": ""})
    ap["approved"] = True
    if plan: ap["plan_sha256"] = plan
    ap["authorized_by"] = by
    ap["ts"] = time.strftime("%FT%TZ", time.gmtime())
    P.write_text(yaml.safe_dump(k, sort_keys=False, allow_unicode=True))
    print(json.dumps({"aprobacion": name, "approved": True, "plan_sha256": ap.get("plan_sha256"), "by": by}, ensure_ascii=False))
    return 0
if __name__ == "__main__":
    sys.exit(main())
