"""Video generation helpers: mode constants, payload builders, result extraction.

Shared library for video.py. Contains all mode constants, model defaults,
endpoint paths, payload construction, and result parsing/formatting logic.
Stdlib only -- no pip install required.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qwencloud_lib import load_cdn_model_config, resolve_file, sanitize_diagnostic  # noqa: E402

# ---------------------------------------------------------------------------
# Mode constants
# ---------------------------------------------------------------------------

MODE_T2V = "t2v"
MODE_I2V = "i2v"
MODE_KF2V = "kf2v"
MODE_R2V = "r2v"
MODE_VACE = "vace"
MODE_VIDEO_EDIT = "videoedit"
MODE_ANIMATE = "animate"

_MODEL_CONFIG_FILE = "qwencloud-video-generation-config.json"
_MODEL_CONFIG_DIR = Path(__file__).resolve().parent.parent / "cdn" / "config"
_MODEL_CONFIG_ARRAY_KEYS = (
    "wan27_t2v_models",
    "wan27_i2v_models",
    "wan30_video_models",
    "animate_models",
    "happyhorse_i2v_models",
    "happyhorse_r2v_models",
    "wan27_r2v_models",
    "video_edit_models",
    "happyhorse_video_edit_models",
)


def _validate_model_config(config: dict[str, Any]) -> bool:
    defaults = config.get("default_models")
    if not isinstance(defaults, dict) or not all(
        isinstance(mode, str) and isinstance(model, str) and model
        for mode, model in defaults.items()
    ):
        return False
    required_modes = {
        MODE_T2V, MODE_I2V, MODE_KF2V, MODE_R2V,
        MODE_VACE, MODE_VIDEO_EDIT, MODE_ANIMATE,
    }
    if not required_modes.issubset(defaults):
        return False
    if not all(
        isinstance(config.get(key), list)
        and bool(config[key])
        and all(isinstance(item, str) and item for item in config[key])
        for key in _MODEL_CONFIG_ARRAY_KEYS
    ):
        return False
    return (
        defaults[MODE_T2V] in config["wan27_t2v_models"]
        and defaults[MODE_I2V] in (
            config["wan27_i2v_models"] + config["happyhorse_i2v_models"]
        )
        and defaults[MODE_R2V] in (
            config["wan27_r2v_models"] + config["happyhorse_r2v_models"]
        )
        and defaults[MODE_VIDEO_EDIT] in config["video_edit_models"]
        and defaults[MODE_ANIMATE] in config["animate_models"]
        and set(config["wan30_video_models"]).issubset(config["wan27_t2v_models"])
        and set(config["wan30_video_models"]).issubset(config["wan27_i2v_models"])
        and set(config["happyhorse_video_edit_models"]).issubset(config["video_edit_models"])
    )


def _model_config() -> dict[str, Any]:
    return load_cdn_model_config(
        _MODEL_CONFIG_FILE,
        local_dir=_MODEL_CONFIG_DIR,
        required_keys=("default_models",) + _MODEL_CONFIG_ARRAY_KEYS,
        validator=_validate_model_config,
    )


def _model_ids(key: str) -> frozenset[str]:
    return frozenset(_model_config()[key])


def get_default_model(mode: str) -> str:
    model = _model_config()["default_models"].get(mode)
    if not isinstance(model, str) or not model:
        raise RuntimeError(f"Invalid video model configuration: missing default for {mode}")
    return model


def is_wan27_i2v_model(model: str) -> bool:
    return model in _model_ids("wan27_i2v_models")


def is_happyhorse_i2v_model(model: str) -> bool:
    return model in _model_ids("happyhorse_i2v_models")


def is_video_edit_model(model: str) -> bool:
    return model in _model_ids("video_edit_models")


def is_animate_model(model: str) -> bool:
    return model in _model_ids("animate_models")

# wan2.7 and wan3.0 models use the same modes but with different payload structure.
# happyhorse-1.0/1.1-t2v share the wan2.7-t2v structure (resolution + ratio,
# per openapi-happyhorse-text-to-video.json: resolution/ratio/duration/watermark/seed).
# wan3.0 spec supports the `ratio` parameter (adaptive/16:9/9:16/1:1) in BOTH t2v
# and i2v (openapi-wan3-video-generation*.json); wan2.7-i2v derives the ratio from
# the first frame and does not accept it. Reference: qianwen-ai video_lib
# _build_wan30_video_payload passes ratio through.
# Image-to-animation models (openapi-wan-image-to-animation.json /
# openapi-wan-character-swap.json): input={image_url, video_url} +
# parameters.mode (wan-std/wan-pro, REQUIRED). No prompt. Output is a video
# (image2video endpoint), so they live in this video skill.
# happyhorse-i2v diverges from wan2.7-i2v: media must be EXACTLY ONE
# {type:'first_frame', url} and parameters are limited to
# resolution/duration/watermark/seed (openapi-happyhorse-image-to-video.json).
# happyhorse-r2v uses media[{type:"reference_image", url}] + resolution+ratio
# wan2.7-r2v uses input.media = [{type, url}] mixed image/video/audio refs (max 5)
_WAN27_R2V_MAX_MEDIA = 5

# Video-edit models share a unified media protocol (no `function` field):
# input.media = [{type:"video", url}] + [{type:"reference_image", url}, ...].
# wan2.7-videoedit: prompt optional, negative_prompt + ratio/duration/prompt_extend.
# happyhorse-1.0-video-edit: prompt REQUIRED, only resolution/watermark/
# audio_setting/seed (openapi-happyhorse-video-editing.json).
ENDPOINTS: dict[str, str] = {
    MODE_T2V: "/services/aigc/video-generation/video-synthesis",
    MODE_I2V: "/services/aigc/video-generation/video-synthesis",
    MODE_KF2V: "/services/aigc/image2video/video-synthesis",
    MODE_R2V: "/services/aigc/video-generation/video-synthesis",
    MODE_VACE: "/services/aigc/video-generation/video-synthesis",
    MODE_VIDEO_EDIT: "/services/aigc/video-generation/video-synthesis",
    MODE_ANIMATE: "/services/aigc/image2video/video-synthesis",
}

_PRICING_URL = "https://docs.qwencloud.com/developer-guides/getting-started/pricing"

# ---------------------------------------------------------------------------
# Mode detection
# ---------------------------------------------------------------------------

def detect_mode(request: dict[str, Any], model: str = "") -> str:
    """Auto-detect video generation mode from request fields."""
    # Highest priority: model-routed modes whose requests carry no discriminating
    # fields (animate has image_url+video_url; video-edit models have no `function`).
    if is_animate_model(model):
        return MODE_ANIMATE
    if is_video_edit_model(model):
        return MODE_VIDEO_EDIT
    # happyhorse-i2v: media/img_url/first_frame_url all mean i2v mode
    # (a bare first_frame_url would otherwise be misclassified as kf2v).
    if is_happyhorse_i2v_model(model):
        return MODE_I2V
    if request.get("function"):
        return MODE_VACE
    if request.get("reference_urls"):
        return MODE_R2V
    # happyhorse-r2v / wan2.7-r2v may be triggered by model id alone (media provided in input)
    if (model in _model_ids("happyhorse_r2v_models")
            or model in _model_ids("wan27_r2v_models")):
        return MODE_R2V
    # wan2.7-i2v uses media array or first_clip_url
    if request.get("media") or request.get("first_clip_url"):
        return MODE_I2V
    if request.get("first_frame_url"):
        return MODE_KF2V
    if request.get("img_url") or request.get("reference_image"):
        return MODE_I2V
    return MODE_T2V

# ---------------------------------------------------------------------------
# File resolution helpers
# ---------------------------------------------------------------------------

RESOLVE_KEYS: dict[str, list[str]] = {
    MODE_T2V: ["audio_url"],
    MODE_I2V: ["img_url", "reference_image", "audio_url",
               "first_frame_url", "last_frame_url", "driving_audio_url", "first_clip_url",
               "media"],
    MODE_KF2V: ["first_frame_url", "last_frame_url"],
    MODE_R2V: ["reference_urls", "media"],
    MODE_VACE: ["video_url", "mask_image_url", "mask_video_url",
                "ref_images_url", "first_clip_url", "last_clip_url",
                "first_frame_url", "last_frame_url"],
    MODE_VIDEO_EDIT: ["video_url", "reference_images", "media"],
    MODE_ANIMATE: ["image_url", "video_url"],
}


def resolve_request_urls(request: dict[str, Any], api_key: str, model: str,
                         keys: list[str]) -> None:
    """In-place resolve local file paths to OSS URLs for the given request keys."""
    for key in keys:
        val = request.get(key)
        if val is None:
            continue
        if isinstance(val, str):
            request[key] = resolve_file(val, api_key=api_key, model=model)
        elif isinstance(val, list):
            if val and isinstance(val[0], dict):
                # Handle list[dict] structure (e.g. media: [{type: "...", url: "..."}])
                for item in val:
                    if isinstance(item, dict) and "url" in item:
                        url_val = item["url"]
                        if isinstance(url_val, str):
                            item["url"] = resolve_file(url_val, api_key=api_key, model=model)
            else:
                # Handle list[str] (e.g. reference_urls: ["url1", "url2"])
                request[key] = [resolve_file(str(v), api_key=api_key, model=model) for v in val]

# ---------------------------------------------------------------------------
# Payload builders
# ---------------------------------------------------------------------------

def _require_prompt(request: dict[str, Any], mode: str, model: str) -> None:
    """Raise ValueError when a prompt-driven mode has no top-level prompt.

    Detects the common mistake of passing the API-native nested format
    ({"input": {"prompt": ...}}) instead of this script's flat format.
    """
    if request.get("prompt"):
        return
    msg = (f"{model} ({mode}) requires a non-empty top-level 'prompt'. "
           "Request JSON uses FLAT fields, e.g. "
           '{"prompt":"A cat playing piano"} — not the API-native nested '
           '{"input":{"prompt":...}} format.')
    if isinstance(request.get("input"), dict):
        msg += (" Detected nested 'input' object in your request — "
                "flatten its keys (prompt/media/...) to the top level.")
    raise ValueError(msg)


def build_t2v_payload(request: dict[str, Any], model: str) -> dict[str, Any]:
    """Build payload for text-to-video generation (wan2.6/wan2.7)."""
    _require_prompt(request, MODE_T2V, model)
    is_v27 = model in _model_ids("wan27_t2v_models")

    input_obj: dict[str, Any] = {"prompt": request.get("prompt", "")}
    if request.get("negative_prompt"):
        input_obj["negative_prompt"] = request["negative_prompt"]
    if request.get("audio_url"):
        input_obj["audio_url"] = request["audio_url"]

    params: dict[str, Any] = {"duration": request.get("duration", 5)}

    if is_v27:
        # wan2.7-t2v: uses resolution and ratio
        params["resolution"] = request.get("resolution", "1080P")
        if request.get("ratio"):
            params["ratio"] = request["ratio"]
    else:
        # wan2.6-t2v: uses size
        if request.get("size"):
            params["size"] = request["size"]
        for key in ("seed", "shot_type"):
            if request.get(key) is not None:
                params[key] = request[key]

    for key in ("prompt_extend", "watermark"):
        if request.get(key) is not None:
            params[key] = request[key]

    return {"model": model, "input": input_obj, "parameters": params}


def build_i2v_payload(request: dict[str, Any], model: str) -> dict[str, Any]:
    """Build payload for image-to-video generation (wan2.6/wan2.7/happyhorse).

    Routing (front-loaded predicates -- different model families MUST NOT
    share a builder, even when payloads look superficially similar):
      1. happyhorse-1.0-i2v / happyhorse-1.1-i2v -> _build_happyhorse_i2v_payload (strict spec)
      2. wan2.7-i2v / wan3.0 / explicit media[] / first_clip_url -> _build_i2v_v27_payload
      3. wan2.6-i2v fallback (single img_url)
    """
    # 1) happyhorse-i2v has its own strict spec; never fall through.
    if is_happyhorse_i2v_model(model):
        return _build_happyhorse_i2v_payload(request, model)

    is_v27 = is_wan27_i2v_model(model)

    # wan2.7-i2v uses media array
    if is_v27 or request.get("media") or request.get("first_clip_url"):
        return _build_i2v_v27_payload(request, model)

    # wan2.6-i2v uses img_url
    _require_prompt(request, MODE_I2V, model)
    img_url = request.get("img_url") or request.get("reference_image", "")
    input_obj: dict[str, Any] = {"prompt": request.get("prompt", ""), "img_url": img_url}
    if request.get("negative_prompt"):
        input_obj["negative_prompt"] = request["negative_prompt"]
    if request.get("audio_url"):
        input_obj["audio_url"] = request["audio_url"]

    params: dict[str, Any] = {
        "resolution": request.get("resolution", "720P"),
        "duration": request.get("duration", 5),
    }
    for key in ("prompt_extend", "watermark", "seed", "shot_type", "template", "audio"):
        if request.get(key) is not None:
            params[key] = request[key]

    return {"model": model, "input": input_obj, "parameters": params}


def _build_happyhorse_i2v_payload(request: dict[str, Any], model: str) -> dict[str, Any]:
    """Build payload for happyhorse-1.0-i2v / happyhorse-1.1-i2v.

    Per the official QwenCloud API specification:
      - input: ONLY `prompt` (optional) and `media` (required).
      - media: must be EXACTLY ONE item with `type='first_frame'`.
      - parameters: ONLY `resolution` (480P/720P/1080P) / `duration` / `watermark` / `seed`.
      - REJECTED by server (will 400, verified by API testing) if any of these
        are sent: `negative_prompt`, `prompt_extend`, `ratio`, `last_frame`,
        `driving_audio`, `first_clip`, `audio_url`.

    Backward-compat: accept wan2.6-style `img_url` / `reference_image` and
    auto-promote to media=[{type:'first_frame', url:...}].
    """
    # 1) Build media (exactly one first_frame).
    media = request.get("media")
    if media:
        if (not isinstance(media, list) or len(media) != 1
                or not isinstance(media[0], dict)
                or media[0].get("type") != "first_frame"
                or not media[0].get("url")):
            raise ValueError(
                f"{model} requires media=[{{type:'first_frame', url:...}}] "
                "with exactly one item."
            )
    else:
        url = (request.get("first_frame_url")
               or request.get("img_url")
               or request.get("reference_image"))
        if not url:
            raise ValueError(
                f"{model} requires a first frame image. Provide via "
                "`first_frame_url`, `img_url`, or "
                "media=[{type:'first_frame', url:...}]."
            )
        media = [{"type": "first_frame", "url": url}]

    # 2) Warn-and-drop unsupported input fields (avoid silent server 400).
    for unsupported in ("negative_prompt", "last_frame_url", "first_clip_url",
                        "driving_audio_url", "audio_url"):
        if request.get(unsupported):
            print(
                f"Warning: {model} does not accept `{unsupported}`; dropped. "
                "Use wan2.7-i2v if you need this feature.",
                file=sys.stderr,
            )

    input_obj: dict[str, Any] = {"media": media}
    if request.get("prompt"):
        input_obj["prompt"] = request["prompt"]

    # 3) Build parameters (whitelist only).
    params: dict[str, Any] = {
        "resolution": request.get("resolution", "1080P"),
        "duration": request.get("duration", 5),
    }
    for key in ("watermark", "seed"):
        if request.get(key) is not None:
            params[key] = request[key]

    # 4) Warn-and-drop unsupported parameters.
    for unsupported in ("prompt_extend", "ratio"):
        if request.get(unsupported) is not None:
            print(
                f"Warning: {model} does not accept parameter `{unsupported}`; "
                "dropped.",
                file=sys.stderr,
            )

    return {"model": model, "input": input_obj, "parameters": params}


def _build_i2v_v27_payload(request: dict[str, Any], model: str) -> dict[str, Any]:
    """Build payload for wan2.7-i2v unified image-to-video generation.

    Serves wan2.7-i2v / wan3.0-video / wan3.0-video-prime ONLY. happyhorse-i2v
    has its own dedicated builder (_build_happyhorse_i2v_payload) -- do NOT
    add happyhorse compat code here.

    Supports: first_frame, last_frame, driving_audio, first_clip (video continuation).
    """
    media: list[dict[str, str]] = []

    if request.get("media"):
        media = request["media"]
    else:
        if request.get("first_frame_url"):
            media.append({"type": "first_frame", "url": request["first_frame_url"]})
        if request.get("last_frame_url"):
            media.append({"type": "last_frame", "url": request["last_frame_url"]})
        if request.get("driving_audio_url"):
            media.append({"type": "driving_audio", "url": request["driving_audio_url"]})
        if request.get("first_clip_url"):
            media.append({"type": "first_clip", "url": request["first_clip_url"]})

    if not media:
        raise ValueError(
            "wan2.7-i2v requires at least one media asset. "
            "Use first_frame_url, first_clip_url, or media array."
        )

    input_obj: dict[str, Any] = {"media": media}
    if request.get("prompt"):
        input_obj["prompt"] = request["prompt"]
    if request.get("negative_prompt"):
        input_obj["negative_prompt"] = request["negative_prompt"]

    params: dict[str, Any] = {
        "resolution": request.get("resolution", "1080P"),
        "duration": request.get("duration", 5),
    }
    # wan3.0 series: pass `ratio` through (spec supports adaptive/16:9/9:16/1:1).
    # wan2.7-i2v does NOT accept ratio (auto-derived from the first frame).
    if model in _model_ids("wan30_video_models") and request.get("ratio") is not None:
        params["ratio"] = request["ratio"]
    for key in ("prompt_extend", "watermark"):
        if request.get(key) is not None:
            params[key] = request[key]

    return {"model": model, "input": input_obj, "parameters": params}


def build_kf2v_payload(request: dict[str, Any], model: str) -> dict[str, Any]:
    """Build payload for keyframe-to-video generation."""
    input_obj: dict[str, Any] = {
        "first_frame_url": request.get("first_frame_url", ""),
        "prompt": request.get("prompt", ""),
    }
    if request.get("last_frame_url"):
        input_obj["last_frame_url"] = request["last_frame_url"]
    if request.get("template"):
        input_obj["template"] = request["template"]

    params: dict[str, Any] = {
        "resolution": request.get("resolution", "720P"),
        "duration": 5,  # Fixed at 5 seconds per qwdocs
    }
    for key in ("prompt_extend", "watermark", "seed"):
        if request.get(key) is not None:
            params[key] = request[key]

    return {"model": model, "input": input_obj, "parameters": params}


def build_r2v_payload(request: dict[str, Any], model: str) -> dict[str, Any]:
    """Build payload for reference-based role-play video generation."""
    # wan2.7-r2v uses input.media = [{type, url}] mixed refs (image/video/audio).
    if model in _model_ids("wan27_r2v_models"):
        return _build_r2v_wan27_payload(request, model)
    # happyhorse-r2v uses media array [{type:"reference_image", url}] + resolution+ratio.
    if model in _model_ids("happyhorse_r2v_models"):
        return _build_r2v_happyhorse_payload(request, model)

    # wan2.6-r2v: uses reference_urls + size
    _require_prompt(request, MODE_R2V, model)
    input_obj: dict[str, Any] = {
        "prompt": request.get("prompt", ""),
        "reference_urls": request.get("reference_urls", []),
    }
    params: dict[str, Any] = {
        "size": request.get("size", "1280*720"),
        "duration": request.get("duration", 5),
    }
    for key in ("shot_type", "watermark", "audio"):
        if request.get(key) is not None:
            params[key] = request[key]

    return {"model": model, "input": input_obj, "parameters": params}


def _build_r2v_happyhorse_payload(request: dict[str, Any], model: str) -> dict[str, Any]:
    """Build payload for happyhorse-r2v reference-to-video.

    Structure: input.media = [{type:"reference_image", url}, ...] + resolution + ratio.
    Up to 9 reference images supported.
    """
    _require_prompt(request, MODE_R2V, model)
    media: list[dict[str, str]] = []
    # Accept reference_urls=[url, ...] (backward-compat shorthand)
    for url in (request.get("reference_urls") or []):
        media.append({"type": "reference_image", "url": str(url)})
    # Accept media=[{type, url}, ...] (native format)
    for item in (request.get("media") or []):
        if isinstance(item, dict):
            media.append(item)
        else:
            media.append({"type": "reference_image", "url": str(item)})
    if not media:
        raise ValueError(
            "happyhorse-r2v requires at least one reference image. "
            "Provide via reference_urls=[...] or media=[{type:reference_image, url}]."
        )

    input_obj: dict[str, Any] = {
        "prompt": request.get("prompt", ""),
        "media": media,
    }
    if request.get("negative_prompt"):
        input_obj["negative_prompt"] = request["negative_prompt"]

    params: dict[str, Any] = {
        "resolution": request.get("resolution", "720P"),
        "duration": request.get("duration", 5),
    }
    for key in ("ratio", "watermark", "seed", "prompt_extend"):
        if request.get(key) is not None:
            params[key] = request[key]

    return {"model": model, "input": input_obj, "parameters": params}


def _build_r2v_wan27_payload(request: dict[str, Any], model: str) -> dict[str, Any]:
    """Build payload for wan2.7-r2v multi-reference video generation.

    Verified contract (tmp/test-new-models/wan2.7-r2v):
      - input.media = [{type, url}, ...] where type in
        {reference_image, reference_video, reference_audio}; up to 5 mixed refs.
        Media items may carry extra fields such as reference_voice (voice cloning)
        and are passed through as-is.
      - input.prompt: required (passthrough).
      - parameters: resolution (720P/1080P) + duration (<=10s) + prompt_extend
        + watermark + seed.
      - NO `ratio` (auto-derived from references), NO `fps`.

    Backward-compat: accept `reference_urls=[...]` (bare strings promoted to
    reference_image) in addition to explicit media=[{type, url}].
    """
    _require_prompt(request, MODE_R2V, model)
    media: list[dict[str, str]] = []
    for url in (request.get("reference_urls") or []):
        media.append({"type": "reference_image", "url": str(url)})
    for item in (request.get("media") or []):
        if isinstance(item, dict):
            media.append(item)
        else:
            media.append({"type": "reference_image", "url": str(item)})

    if not media:
        raise ValueError(
            f"{model} requires at least one reference. Provide via "
            "reference_urls=[...] or media=[{type:reference_image|reference_video|"
            "reference_audio, url}]."
        )
    if len(media) > _WAN27_R2V_MAX_MEDIA:
        raise ValueError(
            f"{model} accepts at most {_WAN27_R2V_MAX_MEDIA} reference media items "
            f"(got {len(media)})."
        )

    input_obj: dict[str, Any] = {
        "prompt": request.get("prompt", ""),
        "media": media,
    }

    params: dict[str, Any] = {
        "resolution": request.get("resolution", "720P"),
        "duration": request.get("duration", 5),
    }
    for key in ("prompt_extend", "watermark", "seed"):
        if request.get(key) is not None:
            params[key] = request[key]

    return {"model": model, "input": input_obj, "parameters": params}


def build_vace_payload(request: dict[str, Any], model: str) -> dict[str, Any]:
    """Build payload for VACE video editing (repainting, extension, outpainting, etc.)."""
    func = request["function"]
    input_obj: dict[str, Any] = {"function": func}

    if request.get("prompt"):
        input_obj["prompt"] = request["prompt"]

    url_fields = [
        "video_url", "mask_image_url", "mask_video_url",
        "first_clip_url", "last_clip_url",
        "first_frame_url", "last_frame_url",
    ]
    for field in url_fields:
        if request.get(field):
            input_obj[field] = request[field]

    if request.get("ref_images_url"):
        input_obj["ref_images_url"] = request["ref_images_url"]
    if request.get("mask_frame_id") is not None:
        input_obj["mask_frame_id"] = request["mask_frame_id"]

    params: dict[str, Any] = {}
    param_keys = [
        "prompt_extend", "size", "watermark", "obj_or_bg",
        "control_condition", "strength", "mask_type", "expand_ratio",
        "top_scale", "bottom_scale", "left_scale", "right_scale",
    ]
    for key in param_keys:
        if request.get(key) is not None:
            params[key] = request[key]

    return {"model": model, "input": input_obj, "parameters": params}


def build_video_edit_payload(request: dict[str, Any], model: str) -> dict[str, Any]:
    """Build payload for wan2.7-videoedit and happyhorse-1.0-video-edit.

    Unified media protocol (no `function` field):
      input.media = [{type:"video", url}] + [{type:"reference_image", url}, ...]

    Parameter differences (per official OpenAPI specs):
      - wan2.7-videoedit (openapi-wan27-video-editing.json): prompt optional,
        negative_prompt supported; parameters resolution/ratio/duration/
        audio_setting/prompt_extend/watermark/seed.
      - happyhorse-1.0-video-edit (openapi-happyhorse-video-editing.json):
        prompt REQUIRED; only resolution/watermark/audio_setting/seed
        (ratio/duration/prompt_extend/negative_prompt are not in the spec).
    """
    media: list[dict[str, str]] = []
    if request.get("video_url"):
        media.append({"type": "video", "url": str(request["video_url"])})
    for item in (request.get("media") or []):
        if isinstance(item, dict):
            media.append(item)
        else:
            media.append({"type": "reference_image", "url": str(item)})
    for url in (request.get("reference_images") or []):
        media.append({"type": "reference_image", "url": str(url)})

    if not media:
        raise ValueError(
            f"{model} requires at least one media asset. "
            "Provide video_url=... and/or media=[{type:'video', url}, ...]."
        )

    input_obj: dict[str, Any] = {"media": media}
    if request.get("prompt"):
        input_obj["prompt"] = request["prompt"]

    params: dict[str, Any] = {}
    if model in _model_ids("happyhorse_video_edit_models"):
        # prompt is REQUIRED per the happyhorse-video-editing spec.
        _require_prompt(request, MODE_VIDEO_EDIT, model)
        for key in ("resolution", "watermark", "audio_setting", "seed"):
            if request.get(key) is not None:
                params[key] = request[key]
        # Warn-and-drop wan2.7-only fields (server would 400).
        for unsupported in ("negative_prompt", "ratio", "duration", "prompt_extend"):
            if request.get(unsupported) is not None:
                print(
                    f"Warning: {model} does not accept `{unsupported}`; dropped. "
                    "Use wan2.7-videoedit if you need this feature.",
                    file=sys.stderr,
                )
    else:
        # wan2.7-videoedit: full parameter whitelist.
        if request.get("negative_prompt"):
            input_obj["negative_prompt"] = request["negative_prompt"]
        for key in ("resolution", "ratio", "duration", "audio_setting",
                    "prompt_extend", "watermark", "seed"):
            if request.get(key) is not None:
                params[key] = request[key]

    return {"model": model, "input": input_obj, "parameters": params}


def build_animate_payload(request: dict[str, Any], model: str) -> dict[str, Any]:
    """Build payload for wan2.2-animate-move / wan2.2-animate-mix.

    Per the official QwenCloud API specifications:
      - input: ONLY `image_url` (character image) + `video_url` (reference
        video whose actions/expressions are transferred). Both REQUIRED. No prompt.
      - parameters: ONLY `mode` (wan-std/wan-pro, REQUIRED) + `check_image`
        (bool, default true). No resolution/duration/seed/watermark.
      - Endpoint: /services/aigc/image2video/video-synthesis (async).
    """
    image_url = request.get("image_url")
    video_url = request.get("video_url")
    if not image_url:
        raise ValueError(
            f"{model} requires 'image_url' (character image URL or local path)."
        )
    if not video_url:
        raise ValueError(
            f"{model} requires 'video_url' (reference video URL or local path, "
            "2-30s, single front-facing person)."
        )
    mode = request.get("mode")
    if mode not in ("wan-std", "wan-pro"):
        raise ValueError(
            f"{model} requires parameters.mode to be 'wan-std' or 'wan-pro' "
            f"(got {mode!r}). wan-std: faster/cheaper; wan-pro: smoother/higher quality."
        )

    input_obj: dict[str, Any] = {
        "image_url": str(image_url),
        "video_url": str(video_url),
    }
    params: dict[str, Any] = {"mode": mode}
    if request.get("check_image") is not None:
        params["check_image"] = request["check_image"]

    return {"model": model, "input": input_obj, "parameters": params}


PAYLOAD_BUILDERS: dict[str, Any] = {
    MODE_T2V: build_t2v_payload,
    MODE_I2V: build_i2v_payload,
    MODE_KF2V: build_kf2v_payload,
    MODE_R2V: build_r2v_payload,
    MODE_VACE: build_vace_payload,
    MODE_VIDEO_EDIT: build_video_edit_payload,
    MODE_ANIMATE: build_animate_payload,
}

# ---------------------------------------------------------------------------
# Result extraction and status formatting
# ---------------------------------------------------------------------------

def extract_video_url(result: dict[str, Any]) -> str | None:
    """Extract video URL from task result, checking all output formats.

    Formats seen across endpoints:
      - output.video_url (happyhorse video-edit)
      - output.results[0].url (kf2v / r2v / t2v / i2v: results is a LIST)
      - output.results.video_url (wan2.2-animate-move/mix: results is an OBJECT)
    """
    output = result.get("output", {})
    url = output.get("video_url")
    if url:
        return url
    results = output.get("results")
    if isinstance(results, dict):
        # animate spec: results = {"video_url": "..."}
        url = results.get("video_url") or results.get("url")
        if url:
            return url
    if isinstance(results, list) and results and isinstance(results[0], dict):
        return results[0].get("url")
    return None


def estimate_cost(_model: str, _duration: int, _resolution: str,
                  _cny: bool = False) -> str:
    """Return a pricing page reference instead of a hardcoded estimate."""
    return f"see {_PRICING_URL} for current rates"


def resolve_resolution(request: dict[str, Any], mode: str) -> str:
    """Derive a human-readable resolution label from the request for cost estimation."""
    # Modes that use resolution parameter
    if mode in (MODE_I2V, MODE_KF2V):
        return request.get("resolution", "720P")
    # Modes that use size parameter (wan2.6 t2v, r2v)
    if mode in (MODE_T2V, MODE_R2V):
        # If resolution is explicitly set (wan2.7), use it
        if request.get("resolution"):
            return request["resolution"]
        size = request.get("size", "1280*720")
        try:
            width, height = size.split("*")
            pixels = int(width) * int(height)
        except (ValueError, AttributeError):
            return "720P"
        if pixels >= 1920 * 1080:
            return "1080P"
        if pixels >= 1280 * 720:
            return "720P"
        return "480P"
    return "720P"


def format_task_status(result: dict[str, Any], elapsed: int | None = None) -> str:
    """Format a human-readable task status line for progress reporting."""
    output = result.get("output", {})
    status = output.get("task_status", "UNKNOWN")
    task_id = output.get("task_id", "")
    parts = []
    if elapsed is not None:
        parts.append(f"[{elapsed}s]")
    parts.append(f"task={task_id}" if task_id else "")
    parts.append(f"status={status}")
    metrics = output.get("task_metrics", {})
    if metrics:
        total = metrics.get("TOTAL", 0)
        succeeded = metrics.get("SUCCEEDED", 0)
        failed = metrics.get("FAILED", 0)
        if total:
            parts.append(f"progress={succeeded}/{total}")
        if failed:
            parts.append(f"failed={failed}")
    msg = output.get("message", "")
    if msg and status in ("FAILED", "CANCELED"):
        parts.append(f"msg={msg[:120]}")
    if output.get("video_url"):
        parts.append("video_url=ready")
    return sanitize_diagnostic("  ".join(part for part in parts if part))
