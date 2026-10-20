"""Store a Codex subscription login as an HF Space Secret, never a Git artifact."""
import argparse
import json
import os
from pathlib import Path
import sys


def validated_auth(raw):
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("auth_mode") != "chatgpt":
        raise ValueError("Expected a ChatGPT subscription login")
    tokens = data.get("tokens")
    if not isinstance(tokens, dict) or not all(
        isinstance(tokens.get(key), str) and tokens[key].strip()
        for key in ("access_token", "refresh_token", "id_token")
    ):
        raise ValueError("Incomplete subscription credentials")
    if data.get("OPENAI_API_KEY"):
        raise ValueError("API-key credentials are not accepted")
    return json.dumps(data, separators=(",", ":"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("preflight", "save"))
    parser.add_argument("--account", required=True, choices=("1", "2"))
    args = parser.parse_args()
    space = os.environ.get("HF_SPACE_ID", "").strip()
    token = os.environ.get("HF_TOKEN", "").strip()
    if not space or not token:
        print("::error::Configure Actions secret HF_TOKEN (Space write permission) and variable HF_SPACE_ID before authorization.")
        return 2
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=token)
        api.space_info(space)
        if args.phase == "preflight":
            print("HF_DESTINATION_ACCESSIBLE; write permission will be checked when saving.")
            return 0
        auth_path = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "auth.json"
        value = validated_auth(auth_path.read_text())
        key = "CODEX_AUTH_JSON_ACCOUNT_" + args.account
        api.add_space_secret(repo_id=space, key=key, value=value)
        print("HF_SECRET_SAVED=" + key)
        print("AGENT_INFERENCE_TEST=PENDING")
        return 0
    except Exception as exc:
        # Do not print exception messages: HTTP payloads can contain credentials.
        print("::error::HF_AUTH_SETUP_FAILED=" + type(exc).__name__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
