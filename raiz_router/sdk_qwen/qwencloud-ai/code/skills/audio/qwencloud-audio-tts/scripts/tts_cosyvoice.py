#!/usr/bin/env python3
"""Synthesize speech from text via CosyVoice models (WebSocket API).

CosyVoice models require the DashScope SDK (WebSocket-based, not HTTP REST).
Run with --help for usage.

Dependencies:
    pip install dashscope>=1.25.17

Or with venv:
    python3 -m venv .venv && source .venv/bin/activate && pip install dashscope>=1.25.17
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 9):
    print(f"Error: Python 3.9+ required (found {sys.version}).", file=sys.stderr)
    sys.exit(1)

# Check dashscope dependency before other imports
try:
    import dashscope
    from dashscope.audio.tts_v2 import SpeechSynthesizer
    from dashscope.audio.tts_v2.speech_synthesizer import AudioFormat
except ImportError:
    print(
        "Error: dashscope SDK not installed.\n\n"
        "Install with:\n"
        "  pip install dashscope>=1.25.17\n\n"
        "Or use venv:\n"
        "  python3 -m venv .venv\n"
        "  source .venv/bin/activate  # Windows: .venv\\Scripts\\activate\n"
        "  pip install dashscope>=1.25.17",
        file=sys.stderr,
    )
    sys.exit(1)

import argparse
import json
import urllib.parse
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qwencloud_lib import (  # noqa: E402
    build_source_config,
    load_cdn_model_config,
    native_base_url,
    require_api_key,
    run_update_signal,
)

# is_token_plan_key is being added to qwencloud_lib; fall back to a local
# check until the shared helper is exported in every installation.
try:
    from qwencloud_lib import is_token_plan_key  # noqa: E402,F401
except ImportError:
    def is_token_plan_key(api_key: str) -> bool:  # type: ignore[misc]
        return api_key.startswith("sk-sp-")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKILL_USER_AGENT = "qwencloud-skills"  # Required header for Token Plan routing
_MODEL_CONFIG_DIR = Path(__file__).resolve().parent.parent / "cdn" / "config"

# The WebSocket endpoint is derived at runtime from the shared native base
# URL (see qwencloud_lib), so a custom QWEN_BASE_URL override and Token Plan
# routing apply to the WebSocket path automatically. With no override,
# native_base_url() defaults to https://dashscope-intl.aliyuncs.com/api/v1,
# resolving to wss://dashscope-intl.aliyuncs.com/api-ws/v1/inference.
_WEBSOCKET_PATH = "/api-ws/v1/inference"

def _validate_model_config(config: dict[str, Any]) -> bool:
    cosyvoice = config.get("cosyvoice")
    if not isinstance(cosyvoice, dict):
        return False
    model_voices = cosyvoice.get("model_voices")
    instruction_voices = cosyvoice.get("instruction_voices")
    if not (
        isinstance(cosyvoice.get("default_model"), str)
        and bool(cosyvoice["default_model"])
        and isinstance(cosyvoice.get("default_voice"), str)
        and bool(cosyvoice["default_voice"])
        and isinstance(model_voices, dict)
        and bool(model_voices)
        and all(
            isinstance(model, str)
            and model
            and isinstance(voices, list)
            and bool(voices)
            and all(isinstance(voice, str) and voice for voice in voices)
            for model, voices in model_voices.items()
        )
        and isinstance(instruction_voices, dict)
        and all(
            isinstance(model, str)
            and model in model_voices
            and isinstance(voices, list)
            and all(isinstance(voice, str) and voice for voice in voices)
            and set(voices).issubset(model_voices[model])
            for model, voices in instruction_voices.items()
        )
    ):
        return False
    default_model = cosyvoice["default_model"]
    return (
        default_model in model_voices
        and cosyvoice["default_voice"] in model_voices[default_model]
    )


def _model_config() -> dict[str, Any]:
    return load_cdn_model_config(
        "qwencloud-audio-tts-config.json",
        local_dir=_MODEL_CONFIG_DIR,
        required_keys=("cosyvoice",),
        validator=_validate_model_config,
    )["cosyvoice"]


def _default_model() -> str:
    return _model_config()["default_model"]


def _default_voice() -> str:
    return _model_config()["default_voice"]


def _voice_map(key: str) -> dict[str, frozenset[str]]:
    return {
        model: frozenset(voices)
        for model, voices in _model_config()[key].items()
    }

_SAMPLE_RATES = (8000, 16000, 22050, 24000, 44100, 48000)

# (format, sample_rate) -> SDK AudioFormat enum for the WebSocket synthesizer
_AUDIO_FORMATS = {
    ("mp3", 8000): AudioFormat.MP3_8000HZ_MONO_128KBPS,
    ("mp3", 16000): AudioFormat.MP3_16000HZ_MONO_128KBPS,
    ("mp3", 22050): AudioFormat.MP3_22050HZ_MONO_256KBPS,
    ("mp3", 24000): AudioFormat.MP3_24000HZ_MONO_256KBPS,
    ("mp3", 44100): AudioFormat.MP3_44100HZ_MONO_256KBPS,
    ("mp3", 48000): AudioFormat.MP3_48000HZ_MONO_256KBPS,
    ("wav", 8000): AudioFormat.WAV_8000HZ_MONO_16BIT,
    ("wav", 16000): AudioFormat.WAV_16000HZ_MONO_16BIT,
    ("wav", 22050): AudioFormat.WAV_22050HZ_MONO_16BIT,
    ("wav", 24000): AudioFormat.WAV_24000HZ_MONO_16BIT,
    ("wav", 44100): AudioFormat.WAV_44100HZ_MONO_16BIT,
    ("wav", 48000): AudioFormat.WAV_48000HZ_MONO_16BIT,
    ("pcm", 8000): AudioFormat.PCM_8000HZ_MONO_16BIT,
    ("pcm", 16000): AudioFormat.PCM_16000HZ_MONO_16BIT,
    ("pcm", 22050): AudioFormat.PCM_22050HZ_MONO_16BIT,
    ("pcm", 24000): AudioFormat.PCM_24000HZ_MONO_16BIT,
    ("pcm", 44100): AudioFormat.PCM_44100HZ_MONO_16BIT,
    ("pcm", 48000): AudioFormat.PCM_48000HZ_MONO_16BIT,
}


def _ws_url() -> str:
    """Derive the WebSocket inference endpoint from the shared native base URL.

    The ws/wss scheme mirrors the base URL's http/https scheme and the host
    is preserved, so QWEN_BASE_URL overrides and Token Plan routing (both
    handled inside ``native_base_url()``) apply automatically.
    """
    parsed = urllib.parse.urlparse(native_base_url())
    scheme = "wss" if parsed.scheme == "https" else "ws"
    return f"{scheme}://{parsed.netloc}{_WEBSOCKET_PATH}"


def _resolve_audio_format(fmt: str, sample_rate: int) -> AudioFormat:
    try:
        return _AUDIO_FORMATS[(fmt, sample_rate)]
    except KeyError:
        print(
            f"Error: unsupported format/sample-rate combination: "
            f"{fmt}@{sample_rate}Hz. "
            f"Sample rates: {', '.join(str(r) for r in _SAMPLE_RATES)}.",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    run_update_signal(caller=__file__)

    parser = argparse.ArgumentParser(
        description="CosyVoice TTS via DashScope SDK (WebSocket)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""\
model examples (current compatibility/defaults load from CDN configuration):
  cosyvoice-v3-flash   High quality, fast, supports system voices
  cosyvoice-v3-plus    Highest quality, supports system voices

voice compatibility:
  cosyvoice-v3-plus    longanyang, longanhuan
  cosyvoice-v3-flash   See CDN model configuration/catalog for the full list

instruction compatibility:
  The selected model and voice must both be instruction-compatible. The script
  validates the exact pair against CDN configuration before making a request.

note:
  CosyVoice models are NOT available on Token Plan. With a Token Plan key
  (sk-sp-...), use tts.py with qwen-audio-3.0-tts-plus instead.

  For Qwen TTS models (qwen3-tts-*, qwen-audio-3.0-tts-plus), use tts.py.

examples:
  # Basic synthesis
  python {Path(__file__).name} --text "Hello, world!"

  # Chinese with specific voice
  python {Path(__file__).name} --text "你好世界" --voice longanhuan

  # High quality model
  python {Path(__file__).name} --text "Hello" --model cosyvoice-v3-plus

  # Instruction-guided style control (cosyvoice-v3-flash)
  python {Path(__file__).name} --text "欢迎光临" --instruction "用热情洋溢的声音" --language-hints zh

  # WAV output at 48 kHz
  python {Path(__file__).name} --text "Hello" --format wav --sample-rate 48000

  # Save to specific file
  python {Path(__file__).name} --text "Hello" --output hello.mp3
""",
    )
    parser.add_argument("--text", "-t", required=True, help="Text to synthesize")
    parser.add_argument("--model", "-m", default=None,
                        help="Model (default loaded from CDN model configuration)")
    parser.add_argument("--voice", "-v", default=None,
                        help="Voice (default loaded from CDN model configuration)")
    parser.add_argument("--output", "-o", type=Path, default=Path("output/qwencloud-audio-tts/cosyvoice.mp3"), help="Output file (default: output/qwencloud-audio-tts/cosyvoice.mp3)")
    parser.add_argument("--format", "-f", default="mp3", choices=["mp3", "wav", "pcm"], help="Audio format (default: mp3)")
    parser.add_argument("--sample-rate", type=int, default=24000, choices=_SAMPLE_RATES,
                        help="Sample rate in Hz (default: 24000)")
    parser.add_argument("--instruction", type=str, default=None,
                        help="Free-style speech instruction; supported voices are loaded from CDN configuration")
    parser.add_argument("--language-hints", type=str, default=None,
                        help="Target language hint (e.g. zh, en)")
    args = parser.parse_args()

    api_key = require_api_key(script_file=__file__, domain="CosyVoice TTS")
    if is_token_plan_key(api_key):
        print(
            "Error: cosyvoice models are not available on Token Plan.\n"
            "Use tts.py with qwen-audio-3.0-tts-plus instead (Token Plan supported).",
            file=sys.stderr,
        )
        sys.exit(1)

    # Model priority: CLI > default
    try:
        model = args.model or _default_model()
        voice = args.voice or _default_voice()
        model_voices = _voice_map("model_voices")
        instruction_voices = _voice_map("instruction_voices")
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if model not in model_voices:
        print(
            f"Error: unsupported CosyVoice model '{model}'. Supported models: "
            f"{', '.join(sorted(model_voices))}",
            file=sys.stderr,
        )
        sys.exit(1)
    if voice not in model_voices[model]:
        print(
            f"Error: voice '{voice}' is not supported by model '{model}'. "
            f"Supported voices: {', '.join(sorted(model_voices[model]))}",
            file=sys.stderr,
        )
        sys.exit(1)
    if args.instruction and voice not in instruction_voices.get(model, frozenset()):
        supported = ", ".join(sorted(instruction_voices.get(model, frozenset()))) or "none"
        print(
            f"Error: --instruction is not supported for voice '{voice}' with model "
            f"'{model}'. Instruction-compatible voices: {supported}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Setup: derive the WebSocket endpoint AFTER require_api_key so that
    # Token Plan / custom QWEN_BASE_URL routing inside native_base_url() is
    # already in effect.
    dashscope.api_key = api_key
    websocket_url = _ws_url()
    dashscope.base_websocket_api_url = websocket_url

    # Synthesize
    print(f"Synthesizing (WebSocket): model={model}, voice={voice}", file=sys.stderr)
    try:
        headers = {"User-Agent": SKILL_USER_AGENT}
        source_config = build_source_config(__file__)
        if source_config:
            headers["X-DashScope-Source-Config"] = source_config
        synthesizer = SpeechSynthesizer(
            model=model,
            voice=voice,
            format=_resolve_audio_format(args.format, args.sample_rate),
            instruction=args.instruction or None,
            language_hints=[args.language_hints] if args.language_hints else None,
            headers=headers,
            url=websocket_url,
        )
        audio_data = synthesizer.call(args.text)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not audio_data:
        # Structured WebSocket error extraction: pull error_code /
        # error_message / task_id from the last task-failed response header.
        try:
            response = synthesizer.get_response()
        except Exception:
            response = None
        header = response.get("header", {}) if isinstance(response, dict) else {}
        if header.get("event") == "task-failed":
            error_code = header.get("error_code", "UnknownError")
            error_message = header.get("error_message", "Unknown error")
            task_id = header.get("task_id", "")
            suffix = f" (task_id={task_id})" if task_id else ""
            print(
                f"Error: WebSocket task failed: {error_code}: "
                f"{error_message}{suffix}",
                file=sys.stderr,
            )
        else:
            print("Error: No audio data returned.", file=sys.stderr)
        sys.exit(1)

    # Save
    output = args.output
    if output.suffix.lower() not in {".mp3", ".wav", ".pcm"}:
        output = output.with_suffix(f".{args.format}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(audio_data)

    print(f"Audio saved to {output}", file=sys.stderr)
    print(json.dumps({"audio_file": str(output), "size_bytes": len(audio_data)}))


if __name__ == "__main__":
    main()
