#!/usr/bin/env python3
"""Synthesize speech from text via Qwen TTS models on DashScope API.

Supports multiple voices, instruction-controlled style, and automatic audio
download. Self-contained, stdlib only.

Protocol routing:
  - qwen3-tts-flash, qwen3-tts-instruct-flash → HTTP REST API
  - qwen-audio-3.0-tts-plus/flash → raw WebSocket duplex streaming
  - cosyvoice-v3-* → scripts/tts_cosyvoice.py (DashScope SDK)
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 9):
    print(f"Error: Python 3.9+ required (found {sys.version}). "
          "Install: https://www.python.org/downloads/", file=sys.stderr)
    sys.exit(1)

import argparse
import hashlib
import json
import os
import socket
import ssl
import struct
import time
import uuid as uuid_mod
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qwencloud_lib import (  # noqa: E402
    check_token_plan_model_support,
    download_file,
    http_request,
    load_cdn_model_config,
    load_request,
    native_base_url,
    require_api_key,
    run_update_signal,
)

# ---------------------------------------------------------------------------
# TTS constants
# ---------------------------------------------------------------------------

TTS_GENERATION_PATH = "/services/aigc/multimodal-generation/generation"
_AUDIO_EXTS = {".wav", ".mp3", ".flac", ".ogg", ".pcm", ".aac", ".opus"}

_MODEL_CONFIG_DIR = Path(__file__).resolve().parent.parent / "cdn" / "config"


def _validate_model_config(config: dict[str, Any]) -> bool:
    tts = config.get("tts")
    if not isinstance(tts, dict):
        return False
    cosyvoice = config.get("cosyvoice")
    cosyvoice_models = (
        set(cosyvoice.get("model_voices", {}))
        if isinstance(cosyvoice, dict) and isinstance(cosyvoice.get("model_voices"), dict)
        else set()
    )
    voices = tts.get("ws_default_voices")
    if not (
        isinstance(tts.get("default_model"), str)
        and bool(tts["default_model"])
        and isinstance(tts.get("default_voice"), str)
        and bool(tts["default_voice"])
        and isinstance(tts.get("ws_models"), list)
        and all(isinstance(item, str) and item for item in tts["ws_models"])
        and isinstance(voices, dict)
        and all(
            isinstance(model, str) and isinstance(voice, str) and voice
            for model, voice in voices.items()
        )
    ):
        return False
    ws_models = set(tts["ws_models"])
    return (
        tts["default_model"] in ws_models
        and ws_models == set(voices)
        and ws_models.isdisjoint(cosyvoice_models)
    )


def _model_config() -> dict[str, Any]:
    return load_cdn_model_config(
        "qwencloud-audio-tts-config.json",
        local_dir=_MODEL_CONFIG_DIR,
        required_keys=("tts",),
        validator=_validate_model_config,
    )["tts"]


def _default_model() -> str:
    return _model_config()["default_model"]


def _default_voice() -> str:
    return _model_config()["default_voice"]


def _ws_models() -> frozenset[str]:
    return frozenset(_model_config()["ws_models"])


def _ws_default_voices() -> dict[str, str]:
    return dict(_model_config()["ws_default_voices"])

# WebSocket endpoint paths
_WS_PATH = "/api-ws/v1/inference"
_WS_HOST_PAYG = "dashscope-intl.aliyuncs.com"
_WS_HOST_TOKEN_PLAN = "token-plan.ap-southeast-1.maas.aliyuncs.com"


def _is_audio_file_output(path: Path) -> bool:
    """Return whether *path* denotes an audio file rather than a directory."""
    return not path.is_dir() and path.suffix.lower() in _AUDIO_EXTS


# ---------------------------------------------------------------------------
# WebSocket minimal implementation (stdlib: ssl + socket + struct + hashlib)
# ---------------------------------------------------------------------------

def _ws_connect(host: str, path: str, api_key: str) -> socket.socket:
    """Perform WebSocket HTTP Upgrade handshake, return connected socket."""
    ctx = ssl.create_default_context()
    raw = socket.create_connection((host, 443), timeout=60)
    sock = ctx.wrap_socket(raw, server_hostname=host)

    ws_key = hashlib.sha1(uuid_mod.uuid4().bytes).digest()
    import base64
    ws_key_b64 = base64.b64encode(ws_key[:16]).decode()

    handshake = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {ws_key_b64}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"Authorization: Bearer {api_key}\r\n"
        f"User-Agent: qwencloud-skills\r\n"
        f"\r\n"
    )
    sock.sendall(handshake.encode())

    # Read HTTP response
    resp_data = b""
    while b"\r\n\r\n" not in resp_data:
        chunk = sock.recv(4096)
        if not chunk:
            raise RuntimeError("WebSocket handshake failed: connection closed")
        resp_data += chunk

    status_line = resp_data.split(b"\r\n", 1)[0].decode()
    if "101" not in status_line:
        raise RuntimeError(f"WebSocket handshake failed: {status_line}")

    return sock


def _ws_send_text(sock: socket.socket, data: str) -> None:
    """Send a masked text frame over WebSocket."""
    payload = data.encode("utf-8")
    length = len(payload)

    # Build frame header: FIN=1, opcode=1 (text), MASK=1
    header = bytearray()
    header.append(0x81)  # FIN + text opcode

    if length < 126:
        header.append(0x80 | length)
    elif length < 65536:
        header.append(0x80 | 126)
        header.extend(struct.pack("!H", length))
    else:
        header.append(0x80 | 127)
        header.extend(struct.pack("!Q", length))

    # Masking key (4 random bytes)
    mask = os.urandom(4)
    header.extend(mask)

    # Mask the payload
    masked = bytearray(length)
    for i in range(length):
        masked[i] = payload[i] ^ mask[i % 4]

    sock.sendall(bytes(header) + bytes(masked))


def _ws_recv_frame(sock: socket.socket) -> tuple[int, bytes]:
    """Receive one complete WebSocket message. Returns (opcode, payload)."""
    def _recv_exact(n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                raise RuntimeError("WebSocket connection closed unexpectedly")
            buf += chunk
        return buf

    def _recv_raw_frame() -> tuple[bool, int, bytes]:
        hdr = _recv_exact(2)
        fin = bool(hdr[0] & 0x80)
        opcode = hdr[0] & 0x0F
        masked = bool(hdr[1] & 0x80)
        length = hdr[1] & 0x7F

        if opcode >= 0x08:
            if not fin:
                raise RuntimeError("WebSocket protocol error: control frame must not be fragmented")
            if length > 125:
                raise RuntimeError(
                    "WebSocket protocol error: control frame payload exceeds 125 bytes"
                )

        if length == 126:
            length = struct.unpack("!H", _recv_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", _recv_exact(8))[0]

        mask_key = _recv_exact(4) if masked else None
        payload = _recv_exact(length)

        if mask_key:
            payload = bytes(payload[i] ^ mask_key[i % 4] for i in range(length))

        return fin, opcode, payload

    message_opcode: int | None = None
    message_chunks: list[bytes] = []

    while True:
        fin, opcode, payload = _recv_raw_frame()

        if opcode == 0x09:  # Ping control frame may interrupt a fragmented message
            _ws_send_pong(sock, payload)
            continue
        if opcode == 0x0A:  # Pong control frame
            continue
        if opcode == 0x08:  # Close control frame
            return opcode, payload

        if opcode in (0x01, 0x02):
            if message_opcode is not None:
                raise RuntimeError("WebSocket protocol error: new data frame before continuation")
            if fin:
                return opcode, payload
            message_opcode = opcode
            message_chunks.append(payload)
            continue

        if opcode == 0x00:
            if message_opcode is None:
                raise RuntimeError("WebSocket protocol error: unexpected continuation frame")
            message_chunks.append(payload)
            if fin:
                return message_opcode, b"".join(message_chunks)
            continue

        raise RuntimeError(f"WebSocket protocol error: unsupported opcode {opcode}")


def _ws_close(sock: socket.socket) -> None:
    """Send close frame and shut down."""
    try:
        # Send close frame: FIN=1, opcode=8, masked, empty payload
        mask = os.urandom(4)
        sock.sendall(b"\x88\x80" + mask)
    except OSError:
        pass
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    sock.close()


def _ws_send_pong(sock: socket.socket, payload: bytes) -> None:
    """Send a masked pong frame with the given payload."""
    pong_hdr = bytearray([0x8A])  # FIN + pong opcode
    plen = len(payload)
    if plen < 126:
        pong_hdr.append(0x80 | plen)
    else:
        pong_hdr.append(0x80 | 126)
        pong_hdr.extend(struct.pack("!H", plen))
    mask = os.urandom(4)
    pong_hdr.extend(mask)
    masked_payload = bytes(payload[i] ^ mask[i % 4] for i in range(plen))
    sock.sendall(bytes(pong_hdr) + masked_payload)


def _ws_tts(api_key: str, model: str, text: str, voice: str,
            output: Path, *, sample_rate: int = 24000,
            audio_format: str = "mp3",
            style_params: dict[str, Any] | None = None,
            use_model_default_voice: bool = False) -> dict[str, Any]:
    """Perform TTS via WebSocket duplex protocol.

    *style_params* may carry optional run-task style parameters
    (``volume`` / ``rate`` / ``pitch``); only keys explicitly provided
    by the user are forwarded.

    Returns dict with audio_file path and metadata.
    """
    # Determine endpoint based on key type
    if api_key.startswith("sk-sp-"):
        host = _WS_HOST_TOKEN_PLAN
    else:
        host = _WS_HOST_PAYG

    # Resolve the model default only when no voice was supplied by the caller.
    # An explicit voice named "Cherry" must remain Cherry even though that is
    # also the generic CLI default.
    ws_default_voices = _ws_default_voices()
    if use_model_default_voice and model in ws_default_voices:
        voice = ws_default_voices[model]
        print(f"Using default voice '{voice}' for model {model}", file=sys.stderr)

    task_id = str(uuid_mod.uuid4())

    print(f"Connecting to wss://{host}{_WS_PATH} ...", file=sys.stderr)
    sock = _ws_connect(host, _WS_PATH, api_key)

    try:
        # 1. Send run-task
        ws_params: dict[str, Any] = {
            "text_type": "PlainText",
            "format": audio_format,
            "sample_rate": sample_rate,
            "voice": voice,
        }
        for k in ("volume", "rate", "pitch"):
            if style_params and style_params.get(k) is not None:
                ws_params[k] = style_params[k]

        run_task_msg = json.dumps({
            "header": {
                "action": "run-task",
                "task_id": task_id,
                "streaming": "duplex",
            },
            "payload": {
                "task_group": "audio",
                "task": "tts",
                "function": "SpeechSynthesizer",
                "model": model,
                "parameters": ws_params,
                "input": {},
            },
        })
        _ws_send_text(sock, run_task_msg)

        # 2. Wait for task-started event before sending text (protocol requirement)
        task_started = False
        error_msg = ""
        while not task_started:
            opcode, frame_payload = _ws_recv_frame(sock)
            if opcode == 0x01:  # Text frame
                try:
                    event = json.loads(frame_payload.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                header = event.get("header", {})
                event_name = header.get("event", "")
                if event_name == "task-started":
                    task_started = True
                elif event_name == "task-failed":
                    error_msg = header.get("error_message", "Unknown error")
                    raise RuntimeError(f"WebSocket TTS task-start failed: {error_msg}")
            elif opcode == 0x08:  # Close frame
                raise RuntimeError("WebSocket closed before task-started")

        # 3. Send continue-task with text
        continue_task_msg = json.dumps({
            "header": {
                "action": "continue-task",
                "task_id": task_id,
                "streaming": "duplex",
            },
            "payload": {
                "input": {"text": text},
            },
        })
        _ws_send_text(sock, continue_task_msg)

        # 4. Send finish-task
        finish_task_msg = json.dumps({
            "header": {
                "action": "finish-task",
                "task_id": task_id,
                "streaming": "duplex",
            },
            "payload": {
                "input": {},
            },
        })
        _ws_send_text(sock, finish_task_msg)

        # 5. Receive frames: binary = audio data, text = event JSON
        audio_chunks: list[bytes] = []
        task_completed = False
        error_msg = ""

        while not task_completed:
            opcode, frame_payload = _ws_recv_frame(sock)

            if opcode == 0x02:  # Binary frame → audio data
                audio_chunks.append(frame_payload)
            elif opcode == 0x01:  # Text frame → event JSON
                try:
                    event = json.loads(frame_payload.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue

                header = event.get("header", {})
                event_name = header.get("event", "")

                if event_name == "task-finished":
                    task_completed = True
                elif event_name == "task-failed":
                    error_msg = header.get("error_message") or "Unknown error"
                    raise RuntimeError(f"WebSocket TTS failed: {error_msg}")
            elif opcode == 0x08:  # Close frame
                raise RuntimeError("WebSocket TTS closed before task-finished")

    finally:
        _ws_close(sock)

    if error_msg:
        raise RuntimeError(f"WebSocket TTS failed: {error_msg}")

    if not audio_chunks:
        raise RuntimeError("WebSocket TTS: no audio data received")

    # Concatenate and write audio. A recognized audio suffix means the caller
    # supplied an exact file path; otherwise the path is an output directory.
    if _is_audio_file_output(output):
        audio_file = output
        output_dir = output.parent
    else:
        output_dir = output
        ext = f".{audio_format}" if not audio_format.startswith(".") else audio_format
        ts = time.strftime("%Y%m%d-%H%M%S")
        audio_file = output_dir / f"audio-{ts}{ext}"

    output_dir.mkdir(parents=True, exist_ok=True)
    audio_file.write_bytes(b"".join(audio_chunks))

    total_bytes = sum(len(c) for c in audio_chunks)
    print(f"WebSocket TTS complete: {total_bytes} bytes received", file=sys.stderr)
    print(f"Audio saved to {audio_file}", file=sys.stderr)

    return {
        "audio_file": str(audio_file),
        "model": model,
        "format": audio_format,
        "sample_rate": sample_rate,
        "bytes": total_bytes,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _guess_audio_ext(url: str, default: str = ".wav") -> str:
    """Extract audio extension from URL path, ignoring query params."""
    path = urlparse(url).path
    for ext in (".wav", ".mp3", ".flac", ".ogg", ".pcm", ".aac"):
        if path.endswith(ext):
            return ext
    return default


# ---------------------------------------------------------------------------
# HTTP REST TTS (qwen3-tts-flash, qwen3-tts-instruct-flash)
# ---------------------------------------------------------------------------

def _http_tts(api_key: str, model: str, voice: str, text: str,
              request: dict[str, Any], args: Any) -> None:
    """Perform TTS via HTTP REST API."""
    input_obj: dict[str, Any] = {"text": text, "voice": voice}
    if request.get("language_type"):
        input_obj["language_type"] = request["language_type"]

    payload: dict[str, Any] = {"model": model, "input": input_obj}

    if request.get("instructions") and "instruct" in model.lower():
        input_obj["instructions"] = request["instructions"]
        if request.get("optimize_instructions") is not None:
            input_obj["optimize_instructions"] = request["optimize_instructions"]

    url = f"{native_base_url()}{TTS_GENERATION_PATH}"

    try:
        resp = http_request("POST", url, api_key, payload, timeout=60)
    except RuntimeError as e:
        print(f"API error: {e}", file=sys.stderr)
        sys.exit(1)

    audio_url = (resp.get("output") or {}).get("audio", {}).get("url")
    if not audio_url:
        print(f"Error: No audio URL in response: {resp}", file=sys.stderr)
        sys.exit(1)

    out = args.output

    if out.suffix.lower() in _AUDIO_EXTS:
        audio_file = out
        out_dir = out.parent
    else:
        out_dir = out
        ext = _guess_audio_ext(audio_url)
        ts = time.strftime("%Y%m%d-%H%M%S")
        audio_file = out_dir / f"audio-{ts}{ext}"

    out_dir.mkdir(parents=True, exist_ok=True)

    resp_file = out_dir / "response.json"
    resp_file.write_text(json.dumps(resp, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Response saved to {resp_file}", file=sys.stderr)

    try:
        download_file(audio_url, audio_file)
    except Exception as e:
        print(f"Warning: Could not download audio: {e}", file=sys.stderr)
        print(f"Audio URL (manual download): {audio_url}", file=sys.stderr)
    else:
        print(f"Audio saved to {audio_file}", file=sys.stderr)

    if args.print_response:
        print(json.dumps({"audio_url": audio_url, "audio_file": str(audio_file)}, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    run_update_signal(caller=__file__)
    parser = argparse.ArgumentParser(
        description="Synthesize speech from text via Qwen TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
request JSON fields (--request / --file):
  text                (required) Text to synthesize into speech
  voice               Voice ID — overridden by --voice flag; defaults and
                      WebSocket model mappings load from CDN configuration
  model               Model ID — overridden by --model flag
                      (default loaded from CDN configuration)
  language_type       Force language: "Auto" / "Chinese" / "English" / "Japanese" /
                      "Korean" etc. (full names, not "zh"/"en" codes).
                      HTTP models only — WebSocket models ignore this field
                      (their language follows the selected voice)
  instructions        Style instructions for instruct models, e.g.
                      "Speak slowly with a warm, gentle tone"
  optimize_instructions  true/false — auto-optimize instruction text
  sample_rate         Audio sample rate in Hz (WebSocket models, default 24000)
  format              Audio format: mp3/wav/pcm/opus (WebSocket models, default mp3)
  volume              Volume [0-100], default 50 (WebSocket models only)
  rate                Speech rate [0.5-2.0], default 1.0; below 1.0 slows
                      speech, above speeds up (WebSocket models only)
  pitch               Pitch multiplier [0.5-2.0], default 1.0; above 1.0 =
                      higher pitch, below = lower (WebSocket models only)

model examples (current routing/defaults load from CDN configuration):
  qwen-audio-3.0-tts-plus        Next-gen TTS, higher quality,
                                  WebSocket streaming (PAYG + Token Plan)
  qwen3-tts-flash                Non-streaming HTTP path — fast, multi-voice
  qwen3-tts-instruct-flash       Instruction-controlled style (non-streaming HTTP)

  Note: CosyVoice models (cosyvoice-v3-plus/flash) require WebSocket API.
        Use tts_cosyvoice.py instead of this script.

  Token Plan (sk-sp-...) keys: only qwen-audio-3.0-tts-plus is supported.
        For basic style control on Token Plan, use volume/rate/pitch with
        qwen-audio-3.0-tts-plus (instruct models require a PAYG key).

output:
  --output can be a directory (audio saved as audio.wav/mp3 inside)
  or a specific file path (e.g. output/speech.mp3). Extension is
  auto-detected from the API response URL.

environment variables:
  QWENCLOUD_API_KEY   (preferred) API key — also loaded from .env
  QWEN_API_KEY        (fallback) Legacy alias
  DASHSCOPE_API_KEY   (fallback) Legacy provider variable
  QWEN_REGION         ap-southeast-1 (default)

examples:
  # Simple TTS
  python scripts/tts.py --request '{"text":"Hello, world!"}'

  # Chinese text with specific voice
  python scripts/tts.py --request '{"text":"你好世界"}' --voice Chelsie

  # Instruction-controlled style
  python scripts/tts.py --request '{"text":"Breaking news today...",
    "instructions":"Speak in a serious news anchor tone, moderate pace"}' \\
    --model qwen3-tts-instruct-flash

  # Save to specific file
  python scripts/tts.py --request '{"text":"Hello"}' --output output/hello.mp3

  # Style control via WebSocket model (default; works with PAYG + Token Plan keys)
  python scripts/tts.py --request '{"text":"落霞与孤鹜齐飞",
    "rate":0.8,"pitch":1.1,"volume":60}'

  # HTTP fallback model (low cost)
  python scripts/tts.py --request '{"text":"Hello"}' --model qwen3-tts-flash
""",
    )
    parser.add_argument("--request", type=str,
                        help="Inline JSON: must contain 'text' field")
    parser.add_argument("--file", type=Path,
                        help="Path to JSON file containing request body")
    parser.add_argument("--output", type=Path, default=Path("output/qwencloud-audio-tts"),
                        help="Output directory or file path (default: %(default)s)")
    parser.add_argument("--print-response", action="store_true",
                        help="Print audio URL and file path JSON to stdout")
    parser.add_argument("--model", type=str, default=None,
                        help="Model ID (default loaded from CDN model configuration)")
    parser.add_argument("--voice", type=str, default=None,
                        help="Voice ID (default loaded from CDN model configuration)")
    args = parser.parse_args()

    try:
        request = load_request(args)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    text = request.get("text")
    if not text:
        print("Error: text is required.", file=sys.stderr)
        sys.exit(1)

    requested_model = args.model if args.model is not None else request.get("model")
    if isinstance(requested_model, str) and requested_model.startswith("cosyvoice-"):
        print(
            f"Error: {requested_model} is not supported by tts.py. "
            "Use scripts/tts_cosyvoice.py for CosyVoice models.",
            file=sys.stderr,
        )
        sys.exit(1)

    api_key = require_api_key(script_file=__file__, domain="TTS")
    try:
        # CLI flags intentionally override values loaded from request JSON.
        voice_explicit = args.voice is not None or bool(request.get("voice"))
        voice = args.voice if args.voice is not None else request.get("voice") or _default_voice()
        model = requested_model or _default_model()
        check_token_plan_model_support(model, domain="TTS")
        use_websocket = model in _ws_models()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Route by protocol: WebSocket models vs HTTP models ---
    if use_websocket:
        # Raw WebSocket path for Qwen-Audio TTS models only.
        out = args.output
        if _is_audio_file_output(out):
            out_dir = out.parent
        else:
            out_dir = out

        sample_rate = request.get("sample_rate", 24000)
        audio_format = request.get("format", "mp3")
        # Optional style control (WebSocket models only) — forward only if
        # explicitly provided by the user. This gives Token Plan users basic
        # style control as an alternative to instruct models' instructions.
        style_params = {
            k: request[k] for k in ("volume", "rate", "pitch")
            if request.get(k) is not None
        }

        try:
            result = _ws_tts(
                api_key, model, text, voice, out,
                sample_rate=sample_rate, audio_format=audio_format,
                style_params=style_params,
                use_model_default_voice=not voice_explicit,
            )
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        # Save response JSON
        resp_file = out_dir / "response.json"
        resp_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Response saved to {resp_file}", file=sys.stderr)

        if args.print_response:
            print(json.dumps(result, ensure_ascii=False))

    else:
        # HTTP REST path for qwen3-tts-flash, qwen3-tts-instruct-flash
        _http_tts(api_key, model, voice, text, request, args)


if __name__ == "__main__":
    main()
