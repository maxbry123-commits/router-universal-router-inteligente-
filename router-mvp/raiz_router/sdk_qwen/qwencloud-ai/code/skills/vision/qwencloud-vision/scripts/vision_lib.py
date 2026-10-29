"""Shared infrastructure for qwencloud-vision scripts.

Thin wrapper around qwencloud_lib that re-exports common symbols and adds
vision-specific helpers (streaming with reasoning content, base64 encoding for
smaller files, shared multimodal content builder). Stdlib only -- no pip install
required.
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 9):
    print(f"Error: Python 3.9+ required (found {sys.version}). "
          "Install: https://www.python.org/downloads/", file=sys.stderr)
    sys.exit(1)

from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Re-export shared infrastructure so existing scripts keep working with
# ``from vision_lib import ...``.
from qwencloud_lib import (  # noqa: E402,F401
    DiagnosticStream,
    chat_url,
    check_token_plan_model_support,
    extract_text,
    has_oss_url,
    http_post,
    load_cdn_model_config,
    load_request,
    native_base_url,
    require_api_key as _require_api_key_base,
    resolve_file,
    run_update_signal,
    sanitize_diagnostic,
    save_result,
    stream_sse,
    try_parse_json,
    upload_local_file,
)


_MODEL_CONFIG_DIR = Path(__file__).resolve().parent.parent / "cdn" / "config"


def _validate_model_config(config: dict[str, Any]) -> bool:
    defaults = config.get("default_models")
    return (
        isinstance(defaults, dict)
        and all(
            isinstance(defaults.get(task), str) and defaults[task]
            for task in ("analyze", "reason", "ocr")
        )
    )


def get_default_model(task: str) -> str:
    """Return the current default model for a vision task."""
    config = load_cdn_model_config(
        "qwencloud-vision-config.json",
        local_dir=_MODEL_CONFIG_DIR,
        required_keys=("default_models",),
        validator=_validate_model_config,
    )
    model = config["default_models"].get(task)
    if not isinstance(model, str) or not model:
        raise RuntimeError(f"Invalid vision model configuration: missing default for {task}")
    return model

# ---------------------------------------------------------------------------
# Vision-specific credential wrapper
# ---------------------------------------------------------------------------

def require_api_key() -> str:
    """Load API key with vision domain tagging.

    Token Plan keys (``sk-sp-...``) pass through here and are routed to the
    Token Plan endpoint by ``qwencloud_lib``; per-model availability is
    handled by ``check_token_plan_model_support()`` in each script (aligned
    with the qianwen-ai implementation).
    """
    return _require_api_key_base(script_file=__file__, domain="Vision")

# ---------------------------------------------------------------------------
# Update-check signal (convenience)
# ---------------------------------------------------------------------------

def prompt_update_check_install() -> None:
    """Emit structured signals about update-check skill status to stderr."""
    run_update_signal(caller=__file__)

# ---------------------------------------------------------------------------
# Shared multimodal content builder
# ---------------------------------------------------------------------------

def build_content(
    req: dict[str, Any],
    detail: str = "auto",
    *,
    upload_key: str | None = None,
    upload_model: str | None = None,
) -> list[dict[str, Any]]:
    """Build multimodal content parts from image/video/video_frames input.

    Shared by analyze.py and reason.py. The ``detail`` parameter is only
    applied to image_url items and is ignored for video content.

    Supports:
      - ``video_frames``: list of frame image paths/URLs → video content part
      - ``video``: single video URL/path → video_url content part
      - ``images``: list of image paths/URLs → multiple image_url parts
      - ``image``: single image path/URL → one image_url part
    """
    parts: list[dict[str, Any]] = []

    if req.get("video_frames"):
        frames = [
            resolve_file(str(frame), api_key=upload_key, model=upload_model)
            for frame in req["video_frames"]
        ]
        video_obj: dict[str, Any] = {"type": "video", "video": frames}
        if req.get("fps"):
            video_obj["fps"] = float(req["fps"])
        parts.append(video_obj)
    elif req.get("video"):
        video_url = resolve_file(str(req["video"]), api_key=upload_key, model=upload_model)
        video_obj = {
            "type": "video_url",
            "video_url": {"url": video_url},
        }
        if req.get("fps"):
            video_obj["fps"] = float(req["fps"])
        parts.append(video_obj)
    elif req.get("images"):
        for img in req["images"]:
            resolved_url = resolve_file(str(img), api_key=upload_key, model=upload_model)
            parts.append({"type": "image_url", "image_url": {"url": resolved_url, "detail": detail}})
    elif req.get("image"):
        resolved_url = resolve_file(str(req["image"]), api_key=upload_key, model=upload_model)
        parts.append({"type": "image_url", "image_url": {"url": resolved_url, "detail": detail}})
    else:
        raise ValueError("Provide 'image', 'images', 'video', or 'video_frames'")

    return parts
