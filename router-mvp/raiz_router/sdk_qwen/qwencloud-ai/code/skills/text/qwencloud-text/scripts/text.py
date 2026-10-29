#!/usr/bin/env python3
"""Chat with Qwen models via OpenAI-compatible API. Self-contained, stdlib only."""
from __future__ import annotations

import sys

if sys.version_info < (3, 9):
    print(f"Error: Python 3.9+ required (found {sys.version}). "
          "Install: https://www.python.org/downloads/", file=sys.stderr)
    sys.exit(1)

import argparse
import json
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qwencloud_lib import (  # noqa: E402
    chat_url,
    check_token_plan_model_support,
    http_post,
    load_cdn_model_config,
    load_request,
    require_api_key,
    run_update_signal,
    stream_sse,
)


_MODEL_CONFIG_DIR = Path(__file__).resolve().parent.parent / "cdn" / "config"


def _validate_model_config(config: dict[str, Any]) -> bool:
    return isinstance(config.get("default_model"), str) and bool(config["default_model"])


def _default_model() -> str:
    config = load_cdn_model_config(
        "qwencloud-text-config.json",
        local_dir=_MODEL_CONFIG_DIR,
        required_keys=("default_model",),
        validator=_validate_model_config,
    )
    model = config["default_model"]
    if not isinstance(model, str) or not model:
        raise RuntimeError("Invalid text model configuration: default_model must be a string")
    return model


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------

def _extract_content(resp: dict[str, Any]) -> str:
    choices = resp.get("choices", [])
    if choices:
        msg = choices[0].get("message", {})
        return msg.get("content", "") or ""
    return ""


# ---------------------------------------------------------------------------
# Streaming
# ---------------------------------------------------------------------------

def _run_stream(url: str, api_key: str, request: dict[str, Any],
                print_response: bool, print_reasoning: bool = True) -> dict[str, Any]:
    full_content = ""
    reasoning_content = ""
    is_answering = False
    model = request.get("model", "")
    tool_calls: dict[int, dict[str, Any]] = {}  # keyed by index per official docs
    finish_reason = "stop"

    for chunk in stream_sse(url, api_key, request):
        choices = chunk.get("choices", [])
        if not choices:
            continue
        choice = choices[0]
        delta = choice.get("delta", {})

        # Handle reasoning_content (thinking mode)
        rc = delta.get("reasoning_content") or ""
        if rc:
            reasoning_content += rc
            if print_response and print_reasoning and not is_answering:
                print(rc, end="", flush=True, file=sys.stderr)

        # Handle regular content
        text = delta.get("content", "") or ""
        if text:
            if not is_answering:
                is_answering = True
                if print_response and reasoning_content:
                    print("\n", file=sys.stderr)  # newline after reasoning
            full_content += text
            if print_response:
                print(text, end="", flush=True)

        # Handle function calling (delta.tool_calls) - per official docs pattern
        if "tool_calls" in delta and delta["tool_calls"]:
            for tc in delta["tool_calls"]:
                idx = tc.get("index", 0)
                args = (tc.get("function") or {}).get("arguments") or ""
                if idx not in tool_calls:
                    tool_calls[idx] = tc
                    # Ensure arguments is string, not None
                    if "function" in tool_calls[idx]:
                        tool_calls[idx]["function"]["arguments"] = args
                else:
                    # Accumulate arguments across chunks
                    tool_calls[idx]["function"]["arguments"] += args

        # Track finish_reason
        if choice.get("finish_reason"):
            finish_reason = choice["finish_reason"]

        if not model and chunk.get("model"):
            model = chunk["model"]

    if print_response:
        print()

    message: dict[str, Any] = {"role": "assistant", "content": full_content}
    if tool_calls:
        message["tool_calls"] = list(tool_calls.values())

    result: dict[str, Any] = {
        "model": model,
        "choices": [{"message": message, "finish_reason": finish_reason}],
    }
    if reasoning_content:
        result["reasoning"] = reasoning_content
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    run_update_signal(caller=__file__)
    parser = argparse.ArgumentParser(
        description="Chat with Qwen models via OpenAI-compatible API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
request JSON fields (--request / --file):
  messages          (required) Array of {role, content} message objects
  model             Model ID — overridden by --model flag
  enable_thinking   true/false — override the model's thinking default
  tools             Array of tool/function definitions for function calling
  response_format   {"type":"json_object"} or {"type":"json_schema","json_schema":{...}}
  temperature       Sampling temperature (0-2)
  max_tokens        Maximum output tokens
  stream            true/false — overridden by --stream flag

environment variables:
  QWENCLOUD_API_KEY  (preferred) API key — also loaded from .env file
  QWEN_API_KEY       (fallback) Legacy alias
  DASHSCOPE_API_KEY  (fallback) Legacy provider variable
  QWEN_REGION        ap-southeast-1 (default)
  QWEN_BASE_URL      Override the API base URL entirely

examples:
  # Simple chat
  python scripts/text.py --request '{"messages":[{"role":"user","content":"Hello"}]}'

  # With system prompt and streaming
  python scripts/text.py --request '{"messages":[
    {"role":"system","content":"You are a helpful assistant"},
    {"role":"user","content":"Explain quantum computing"}
  ]}' --stream --print-response

  # From file, save output
  python scripts/text.py --file request.json --output results/ --print-response

  # Structured JSON output
  python scripts/text.py --request '{"messages":[{"role":"user","content":"List 3 colors"}],
    "response_format":{"type":"json_object"}}' --print-response
""",
    )
    parser.add_argument("--request", help="Inline JSON: must contain 'messages' array")
    parser.add_argument("--file", help="Path to JSON file containing request body")
    parser.add_argument("--output", default="output/qwencloud-text",
                        help="Directory to save response JSON (default: output/qwencloud-text)")
    parser.add_argument("--print-response", action="store_true", help="Print generated text to stdout")
    parser.add_argument("--model", help="Model ID (default loaded from CDN model configuration)")
    parser.add_argument("--stream", action="store_true", help="Enable streaming response (SSE)")
    parser.add_argument("--enable-thinking", action="store_true", dest="enable_thinking_flag",
                        help="Enable chain-of-thought thinking mode (overrides model defaults). "
                             "Use only when explicitly requested.")
    parser.add_argument("--hide-reasoning", action="store_true",
                        help="Suppress reasoning process output to stderr (reasoning still saved to JSON)")
    args = parser.parse_args()

    try:
        request = load_request(args)
        if args.model is not None:
            request["model"] = args.model
        elif "model" not in request:
            request["model"] = _default_model()
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Thinking mode handling:
    # - User explicitly enabled via flag → set true
    # - User specified in request JSON → respect their choice  
    # - Otherwise → let the API apply the selected model's default
    if args.enable_thinking_flag:
        request["enable_thinking"] = True
        print("Note: Thinking mode enabled explicitly; this may add latency.", file=sys.stderr)
    elif "enable_thinking" not in request:
        # Do nothing - preserve API defaults per model
        pass

    api_key = require_api_key(script_file=__file__)

    try:
        check_token_plan_model_support(request.get("model", ""), domain="Text")
        url = chat_url()
        if args.stream or request.get("stream"):
            print("Connecting to model (streaming)...", file=sys.stderr)
            response_data = _run_stream(url, api_key, request, args.print_response,
                                         print_reasoning=not args.hide_reasoning)
        else:
            request["stream"] = False
            print("Sending request to model, please wait...", file=sys.stderr)
            response_data = http_post(url, api_key, request)
            # Extract reasoning_content from non-streaming response (normalize to top-level)
            msg = (response_data.get("choices") or [{}])[0].get("message", {})
            if msg.get("reasoning_content"):
                response_data["reasoning"] = msg["reasoning_content"]
            if args.print_response:
                print(_extract_content(response_data))
    except RuntimeError as e:
        print(f"API error: {e}", file=sys.stderr)
        sys.exit(1)

    out = Path(args.output)
    if out.suffix.lower() == ".json":
        out_file = out
        out_dir = out.parent
    else:
        out_dir = out
        out_file = out_dir / "response.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(response_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Response saved to {out_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
