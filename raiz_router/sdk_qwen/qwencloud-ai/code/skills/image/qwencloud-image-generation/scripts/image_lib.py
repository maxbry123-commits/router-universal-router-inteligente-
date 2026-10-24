"""Image generation helpers: model classification, payload builders, response extraction.

Shared library for image.py. Contains all model constants, classification
predicates, payload construction, and response parsing logic.
Stdlib only -- no pip install required.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qwencloud_lib import load_cdn_model_config, resolve_file, sanitize_diagnostic  # noqa: E402

# ---------------------------------------------------------------------------
# Model classification constants
# ---------------------------------------------------------------------------

_MODEL_CONFIG_FILE = "qwencloud-image-generation-config.json"
_MODEL_CONFIG_DIR = Path(__file__).resolve().parent.parent / "cdn" / "config"
_MODEL_CONFIG_STRING_KEYS = (
    "default_model",
    "i2i_default_model",
    "mt_image_default_model",
)
_MODEL_CONFIG_ARRAY_KEYS = (
    "image_edit_models",
    "multi_func_models",
    "i2i_models",
    "qwen_image_edit_models",
    "qwen_image_edit_prefixes",
    "qwen_image_30_models",
    "qwen_t2i_models",
    "qwen_t2i_async_models",
    "qwen_t2i_sync_models",
    "qwen_t2i_valid_sizes",
    "qwen_image_edit_single_output_models",
    "qwen_reference_required_models",
    "z_image_models",
    "mt_image_models",
)
DEFAULT_SIZE = "1280*1280"

SYNC_PATH = "/services/aigc/multimodal-generation/generation"
ASYNC_PATH = "/services/aigc/image-generation/generation"
I2I_ASYNC_PATH = "/services/aigc/image2image/image-synthesis"
T2I_ASYNC_PATH = "/services/aigc/text2image/image-synthesis"

def _validate_model_config(config: dict[str, Any]) -> bool:
    if not all(isinstance(config.get(key), str) and config[key] for key in _MODEL_CONFIG_STRING_KEYS):
        return False
    if not all(
        isinstance(config.get(key), list)
        and bool(config[key])
        and all(isinstance(item, str) and item for item in config[key])
        for key in _MODEL_CONFIG_ARRAY_KEYS
    ):
        return False

    qwen_edit = set(config["qwen_image_edit_models"])
    general_models = (
        set(config["image_edit_models"])
        | set(config["multi_func_models"])
        | qwen_edit
        | set(config["qwen_t2i_models"])
        | set(config["z_image_models"])
    )
    return (
        config["default_model"] in general_models
        and config["i2i_default_model"] in config["i2i_models"]
        and config["mt_image_default_model"] in config["mt_image_models"]
        and set(config["qwen_image_30_models"]).issubset(qwen_edit)
        and set(config["qwen_image_edit_single_output_models"]).issubset(qwen_edit)
        and set(config["qwen_reference_required_models"]).issubset(qwen_edit)
        and set(config["qwen_t2i_async_models"]).isdisjoint(config["qwen_t2i_sync_models"])
        and (
            set(config["qwen_t2i_async_models"])
            | set(config["qwen_t2i_sync_models"])
        ) == set(config["qwen_t2i_models"])
    )


def _model_config() -> dict[str, Any]:
    return load_cdn_model_config(
        _MODEL_CONFIG_FILE,
        local_dir=_MODEL_CONFIG_DIR,
        required_keys=_MODEL_CONFIG_STRING_KEYS + _MODEL_CONFIG_ARRAY_KEYS,
        validator=_validate_model_config,
    )


def _model_ids(key: str) -> frozenset[str]:
    return frozenset(_model_config()[key])


def _model_prefixes(key: str) -> tuple[str, ...]:
    return tuple(_model_config()[key])


def _default_model(key: str = "default_model") -> str:
    return _model_config()[key]


def default_model() -> str:
    return _default_model()


def i2i_default_model() -> str:
    return _default_model("i2i_default_model")


def mt_image_default_model() -> str:
    return _default_model("mt_image_default_model")

# ---------------------------------------------------------------------------
# Model classification predicates
# ---------------------------------------------------------------------------

def is_image_edit_model(model: str) -> bool:
    """Return True if model is a Wan image-editing model (requires reference images)."""
    return model in _model_ids("image_edit_models")


def is_multi_func_model(model: str) -> bool:
    """Return True if model is a multi-function model (wan2.7 series, supports t2i + editing)."""
    return model in _model_ids("multi_func_models")


def is_i2i_model(model: str) -> bool:
    """Return True if model uses the dedicated image-to-image async endpoint."""
    return model in _model_ids("i2i_models")


def is_qwen_image_edit_model(model: str) -> bool:
    """Return True if model is a Qwen image-editing model (includes snapshot versions)."""
    if model in _model_ids("qwen_image_edit_models"):
        return True
    # Support snapshot versions like qwen-image-2.0-pro-2026-03-03
    return model.startswith(_model_prefixes("qwen_image_edit_prefixes"))


def is_qwen_t2i_model(model: str) -> bool:
    """Return True if model uses a legacy fixed-size Qwen T2I contract."""
    return model in _model_ids("qwen_t2i_models")


def is_qwen_t2i_async_model(model: str) -> bool:
    """Return True if model uses the asynchronous text2image endpoint."""
    return model in _model_ids("qwen_t2i_async_models")


def is_qwen_t2i_sync_model(model: str) -> bool:
    """Return True if model uses the synchronous multimodal endpoint."""
    return model in _model_ids("qwen_t2i_sync_models")


def is_z_image_model(model: str) -> bool:
    """Return True if model is the z-image series (sync-only, single-text-content)."""
    return model in _model_ids("z_image_models")


def is_mt_image_model(model: str) -> bool:
    """Return True for image translation (bundled script uses its async route)."""
    return model in _model_ids("mt_image_models")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_file_url(value: str, api_key: str, model: str) -> str:
    """Resolve a local file path or URL, uploading to OSS if needed."""
    return resolve_file(value, api_key=api_key, model=model)

# ---------------------------------------------------------------------------
# Payload builders
# ---------------------------------------------------------------------------

def _build_z_image_payload(req: dict[str, Any], model: str) -> dict[str, Any]:
    """Build payload for z-image-turbo: sync-only, single text content, no `n`, no reference images.

    Per openapi-z-image.json: parameters accept ONLY size / prompt_extend / seed.
    `n` is NOT supported (server returns 400). Reference images are NOT supported.
    """
    prompt = req.get("prompt")
    if not prompt:
        raise ValueError("z-image-turbo requires non-empty prompt")
    if req.get("reference_images") or req.get("reference_image"):
        print(
            f"Warning: {model} does not accept reference images. "
            "Images will be ignored.",
            file=sys.stderr,
        )
    if req.get("n") not in (None, 1):
        print(
            f"Warning: {model} does not support n>1 (n parameter is forbidden). "
            "Falling back to single-image output.",
            file=sys.stderr,
        )

    parameters: dict[str, Any] = {}
    if req.get("size"):
        parameters["size"] = req["size"]
    if req.get("prompt_extend") is not None:
        parameters["prompt_extend"] = req["prompt_extend"]
    if req.get("seed") is not None:
        parameters["seed"] = req["seed"]

    return {
        "model": model,
        "input": {"messages": [{"role": "user", "content": [{"text": prompt}]}]},
        "parameters": parameters,
    }


def _build_qwen_t2i_sync_payload(req: dict[str, Any], model: str) -> dict[str, Any]:
    """Build the synchronous fixed-size Qwen Image request (qwen-image-max)."""
    prompt = req.get("prompt")
    if not prompt:
        raise ValueError("prompt is required")
    if req.get("reference_images") or req.get("reference_image"):
        print(
            f"Warning: {model} does not support reference images for text-to-image. "
            "Images will be ignored. Use a compatible image-editing model instead.",
            file=sys.stderr,
        )
    if req.get("n") not in (None, 1):
        print(
            f"Warning: {model} supports exactly one output; n={req['n']} will be ignored.",
            file=sys.stderr,
        )

    size = req.get("size", "1328*1328")
    valid_sizes = _model_ids("qwen_t2i_valid_sizes")
    if size not in valid_sizes:
        valid = ", ".join(sorted(valid_sizes))
        print(
            f"Warning: size '{size}' may not be valid for {model}. Valid sizes: {valid}",
            file=sys.stderr,
        )

    parameters: dict[str, Any] = {
        "size": size,
        "n": 1,
        "prompt_extend": req.get("prompt_extend", True),
        "watermark": req.get("watermark", False),
    }
    if req.get("negative_prompt"):
        parameters["negative_prompt"] = req["negative_prompt"]
    if req.get("seed") is not None:
        parameters["seed"] = req["seed"]
    return {
        "model": model,
        "input": {"messages": [{"role": "user", "content": [{"text": prompt}]}]},
        "parameters": parameters,
    }


def build_mt_image_payload(req: dict[str, Any], model: str, api_key: str) -> dict[str, Any]:
    """Build payload for qwen-mt-image-2.0 (image translation).

    Per openapi-image-translation.json:
      - input: {image_url (required), source_lang (required), target_lang (required),
        ext (optional: {domainHint, sensitives, terminologies, config})}.
      - NO prompt, NO parameters.
    """
    image_url = req.get("image_url") or req.get("reference_image")
    if not image_url:
        raise ValueError(
            f"{model} requires 'image_url' (URL or local path of the image to translate)."
        )
    source_lang = req.get("source_lang")
    target_lang = req.get("target_lang")
    if not source_lang:
        raise ValueError(
            f"{model} requires 'source_lang' (e.g. \"auto\", \"zh\", \"en\")."
        )
    if not target_lang:
        raise ValueError(
            f"{model} requires 'target_lang' (e.g. \"zh\", \"en\")."
        )

    resolved_url = _resolve_file_url(str(image_url), api_key, model)

    input_obj: dict[str, Any] = {
        "image_url": resolved_url,
        "source_lang": str(source_lang),
        "target_lang": str(target_lang),
    }
    if isinstance(req.get("ext"), dict) and req["ext"]:
        input_obj["ext"] = req["ext"]

    return {"model": model, "input": input_obj}


def build_payload(req: dict[str, Any], model: str, api_key: str) -> dict[str, Any]:
    """Build the DashScope request payload for Wan image-edit and general generation."""
    # z-image-turbo: dedicated branch (sync-only, single-text-content, no n, no images).
    if is_z_image_model(model):
        return _build_z_image_payload(req, model)
    if is_qwen_t2i_sync_model(model):
        return _build_qwen_t2i_sync_payload(req, model)

    prompt = req.get("prompt")
    if not prompt:
        raise ValueError("prompt is required")

    enable_interleave = req.get("enable_interleave", False)
    enable_sequential = req.get("enable_sequential", False)
    is_wan_edit = is_image_edit_model(model)
    is_wan_multi = is_multi_func_model(model)
    is_qwen_edit = is_qwen_image_edit_model(model)
    content: list[dict[str, Any]] = [{"text": prompt}]

    # --- Fallback: models that require reference images ---
    if is_wan_edit:
        images = req.get("reference_images") or []
        if not images and req.get("reference_image"):
            images = [req["reference_image"]]
        if not enable_interleave and not images:
            print(
                f"Warning: {model} requires reference_images or enable_interleave=true. "
                f"Falling back to {default_model()} for text-to-image.",
                file=sys.stderr,
            )
            model = default_model()
            req["model"] = model
            is_wan_edit = False
    elif is_qwen_edit:
        images = req.get("reference_images") or []
        if not images and req.get("reference_image"):
            images = [req["reference_image"]]
        if not images and model in _model_ids("qwen_reference_required_models"):
            print(
                f"Warning: {model} requires reference_images for editing. "
                f"Falling back to {default_model()} for text-to-image.",
                file=sys.stderr,
            )
            model = default_model()
            req["model"] = model
            is_qwen_edit = False

    # --- Image content building ---
    if is_wan_edit:
        images = req.get("reference_images") or []
        if not images and req.get("reference_image"):
            images = [req["reference_image"]]
        if not enable_interleave and len(images) > 4:
            raise ValueError("Image editing mode supports at most 4 reference images")
        if enable_interleave and len(images) > 1:
            raise ValueError("Interleaved text-image mode supports at most 1 reference image")
        for img in images:
            content.append({"image": _resolve_file_url(str(img), api_key, model)})
    elif is_wan_multi:
        # wan2.7 series: supports 0-9 images
        images = req.get("reference_images") or []
        if not images and req.get("reference_image"):
            images = [req["reference_image"]]
        if len(images) > 9:
            raise ValueError("wan2.7 series supports at most 9 reference images")
        for img in images:
            content.append({"image": _resolve_file_url(str(img), api_key, model)})
    elif is_qwen_edit:
        images = req.get("reference_images") or []
        if not images and req.get("reference_image"):
            images = [req["reference_image"]]
        if len(images) > 3:
            raise ValueError("Qwen image editing supports at most 3 reference images")
        for img in images:
            content.append({"image": _resolve_file_url(str(img), api_key, model)})
    else:
        ref_image = req.get("reference_image")
        if not ref_image and req.get("reference_images"):
            ref_image = req["reference_images"][0]
        if ref_image:
            content.insert(0, {"image": _resolve_file_url(str(ref_image), api_key, model)})

    # --- Parameters ---
    if is_wan_edit:
        parameters: dict[str, Any] = {"size": req.get("size", "1K")}
        parameters["enable_interleave"] = enable_interleave
        if enable_interleave:
            parameters["n"] = 1
            parameters["max_images"] = req.get("max_images", 5)
        else:
            parameters["n"] = req.get("n", 1)
            parameters["prompt_extend"] = req.get("prompt_extend", True)
        parameters["watermark"] = req.get("watermark", False)
    elif is_wan_multi:
        # wan2.7 series parameters
        parameters = {"size": req.get("size", "2K")}  # Default 2K for wan2.7
        parameters["enable_sequential"] = enable_sequential
        if enable_sequential:
            # Sequential mode: n=1-12
            parameters["n"] = min(req.get("n", 12), 12)
        else:
            # Non-sequential: n=1-4
            parameters["n"] = min(req.get("n", 4), 4)
        # thinking_mode: default true (only for t2i without sequential)
        images = req.get("reference_images") or []
        if not images and req.get("reference_image"):
            images = [req["reference_image"]]
        if not enable_sequential and not images:
            parameters["thinking_mode"] = req.get("thinking_mode", True)
        parameters["watermark"] = req.get("watermark", False)
        # bbox_list for interactive editing
        if req.get("bbox_list"):
            parameters["bbox_list"] = req["bbox_list"]
        # color_palette for custom colors (only non-sequential)
        if not enable_sequential and req.get("color_palette"):
            parameters["color_palette"] = req["color_palette"]
    elif is_qwen_edit:
        is_qwen_30 = model in _model_ids("qwen_image_30_models")
        if is_qwen_30:
            # qwen-image-3.0 series: NO default size -- only pass size when explicitly
            # provided, so the model auto-recommends resolution otherwise.
            parameters = {}
            if req.get("size"):
                parameters["size"] = req["size"]
        else:
            parameters = {"size": req.get("size", "1024*1024")}
        if model in _model_ids("qwen_image_edit_single_output_models"):
            parameters["n"] = 1
        else:
            parameters["n"] = req.get("n", 1)
        parameters["prompt_extend"] = req.get("prompt_extend", True)
        parameters["watermark"] = req.get("watermark", False)
        if is_qwen_30:
            # 3.0-exclusive params: pass through only when explicitly provided.
            # Use membership check so a literal False for enable_thinking is honored.
            if "enable_thinking" in req:
                parameters["enable_thinking"] = req["enable_thinking"]
            if req.get("prompt_extend_mode"):
                parameters["prompt_extend_mode"] = req["prompt_extend_mode"]
    else:
        parameters = {"size": req.get("size", DEFAULT_SIZE)}
        parameters["prompt_extend"] = req.get("prompt_extend", True)
        parameters["n"] = req.get("n", 1)

    if req.get("negative_prompt"):
        parameters["negative_prompt"] = req["negative_prompt"]
    if req.get("seed") is not None:
        parameters["seed"] = req["seed"]

    return {
        "model": model,
        "input": {"messages": [{"role": "user", "content": content}]},
        "parameters": parameters,
    }


def build_i2i_payload(req: dict[str, Any], model: str, api_key: str) -> dict[str, Any]:
    """Build the DashScope request payload for wan2.5-i2i image-to-image generation."""
    prompt = req.get("prompt")
    if not prompt:
        raise ValueError("prompt is required")

    images = req.get("reference_images") or []
    if not images and req.get("reference_image"):
        images = [req["reference_image"]]
    if not images:
        raise ValueError(
            "wan2.5-i2i-preview requires at least one image via "
            "'reference_images' (array) or 'reference_image' (single)."
        )
    if len(images) > 3:
        raise ValueError("wan2.5-i2i-preview supports at most 3 images")

    resolved_images = [_resolve_file_url(str(img), api_key, model) for img in images]

    payload: dict[str, Any] = {
        "model": model,
        "input": {"prompt": prompt, "images": resolved_images},
        "parameters": {},
    }
    if req.get("negative_prompt"):
        payload["input"]["negative_prompt"] = req["negative_prompt"]

    params = payload["parameters"]
    params["n"] = req.get("n", 1)
    if req.get("size"):
        params["size"] = req["size"]
    params["prompt_extend"] = req.get("prompt_extend", True)
    params["watermark"] = req.get("watermark", False)
    if req.get("seed") is not None:
        params["seed"] = req["seed"]

    return payload


def build_t2i_payload(req: dict[str, Any], model: str) -> dict[str, Any]:
    """Build the DashScope request payload for Qwen text-to-image generation."""
    prompt = req.get("prompt")
    if not prompt:
        raise ValueError("prompt is required")

    if req.get("reference_images") or req.get("reference_image"):
        print(
            f"Warning: {model} does not support reference images for text-to-image. "
            "Images will be ignored. Use qwen-image-edit series for editing.",
            file=sys.stderr,
        )

    # Models routed through this legacy fixed-size endpoint support n=1.
    n_value = req.get("n", 1)
    if is_qwen_t2i_model(model) and n_value != 1:
        print(
            f"Warning: {model} only supports n=1 (fixed). Your value ({n_value}) will be ignored.",
            file=sys.stderr,
        )
        n_value = 1

    size = req.get("size", "1328*1328")
    valid_sizes = _model_ids("qwen_t2i_valid_sizes")
    if size not in valid_sizes:
        valid = ", ".join(sorted(valid_sizes))
        print(
            f"Warning: size '{size}' may not be valid for {model}. Valid sizes: {valid}",
            file=sys.stderr,
        )

    payload: dict[str, Any] = {
        "model": model,
        "input": {"prompt": prompt},
        "parameters": {
            "n": n_value,
            "size": size,
            "prompt_extend": req.get("prompt_extend", True),
            "watermark": req.get("watermark", False),
        },
    }
    if req.get("negative_prompt"):
        payload["input"]["negative_prompt"] = req["negative_prompt"]
    if req.get("seed") is not None:
        payload["parameters"]["seed"] = req["seed"]

    return payload

# ---------------------------------------------------------------------------
# Response extraction
# ---------------------------------------------------------------------------

def extract_image_urls(resp: dict[str, Any]) -> list[str]:
    """Extract all image URLs from all choices in the response."""
    output = resp.get("output") or {}
    choices = output.get("choices") or []
    if not choices:
        raise RuntimeError("No choices returned by DashScope")
    urls: list[str] = []
    for choice in choices:
        content = (choice.get("message") or {}).get("content") or []
        for item in content:
            if isinstance(item, dict) and item.get("image"):
                urls.append(item["image"])
    if not urls:
        raise RuntimeError("No image URL returned by DashScope")
    return urls


def extract_i2i_urls(resp: dict[str, Any]) -> list[str]:
    """Extract image URLs from output.results[].url format (i2i / t2i endpoints)."""
    output = resp.get("output") or {}
    results = output.get("results") or []
    urls = [r["url"] for r in results if isinstance(r, dict) and r.get("url")]
    if not urls:
        raise RuntimeError("No image URL returned by DashScope (i2i)")
    return urls


def extract_mt_image_url(resp: dict[str, Any]) -> str:
    """Extract the translated image URL from output.image_url.

    The image-translation task result carries the URL directly under output.image_url
    (not inside output.results[]). When the image has no translatable text the task
    still SUCCEEDS and returns message "No text detected for translation" with no URL.
    """
    url = (resp.get("output") or {}).get("image_url")
    if not url:
        msg = (resp.get("output") or {}).get("message", "")
        if msg:
            raise RuntimeError(sanitize_diagnostic(f"No translated image URL returned (message: {msg})"))
        raise RuntimeError("No translated image URL returned by DashScope")
    return url


def extract_interleaved_content(resp: dict[str, Any]) -> list[dict[str, str]]:
    """Extract interleaved text and image content from response."""
    output = resp.get("output") or {}
    choices = output.get("choices") or []
    if not choices:
        raise RuntimeError("No choices returned by DashScope")
    content = (choices[0].get("message") or {}).get("content") or []
    result: list[dict[str, str]] = []
    for item in content:
        if isinstance(item, dict):
            if item.get("type") == "text" and item.get("text"):
                result.append({"type": "text", "text": item["text"]})
            elif item.get("type") == "image" and item.get("image"):
                result.append({"type": "image", "image": item["image"]})
            elif item.get("image"):
                result.append({"type": "image", "image": item["image"]})
            elif item.get("text"):
                result.append({"type": "text", "text": item["text"]})
    return result


def extract_usage(resp: dict[str, Any]) -> tuple[int | None, int | None]:
    """Extract image width and height from response usage field.

    Supports two usage formats:
      - width/height integer fields (z-image-turbo: {"width": 1024, "height": 1024})
      - size string field (other models: {"size": "1024*1024"})
    """
    usage = resp.get("usage") or {}
    if isinstance(usage.get("width"), int) and isinstance(usage.get("height"), int):
        return usage["width"], usage["height"]
    size_str = usage.get("size", "")
    if size_str and "*" in size_str:
        parts = size_str.split("*")
        if len(parts) == 2:
            try:
                return int(parts[0]), int(parts[1])
            except ValueError:
                pass
    return None, None
