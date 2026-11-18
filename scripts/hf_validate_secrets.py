"""hf_validate_secrets.py - Pre-deploy: valida ROUTER_API_KEY y HF_VAULT_KEY.
Exit: 0 OK, 1 HF_TOKEN faltante, 2 space_info error, 3 secretos faltantes."""
import os, sys
from huggingface_hub import HfApi

SPACE = "COMAND-CENTER-1/router-universal-router-inteligente"
REQUIRED = {"ROUTER_API_KEY", "HF_VAULT_KEY"}


def main() -> int:
    token = os.getenv("HF_TOKEN")
    if not token:
        print("FATAL: HF_TOKEN faltante", file=sys.stderr); return 1
    api = HfApi(token=token)
    try:
        info = api.space_info(SPACE)
    except Exception as e:
        print(f"FATAL: space_info:{e}", file=sys.stderr); return 2
    keys = {s.key for s in (api.get_space_secrets(SPACE) or [])}
    miss = REQUIRED - keys
    if miss:
        print(f"FATAL: missing_secrets:{sorted(miss)}", file=sys.stderr)
        return 3
    stage = info.runtime.stage if info.runtime else "?"
    print(f"SECRETS_OK: keys={sorted(keys)} stage={stage}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
