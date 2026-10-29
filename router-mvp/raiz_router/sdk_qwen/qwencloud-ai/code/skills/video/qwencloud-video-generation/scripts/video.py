#!/usr/bin/env python3
"""Video generation via Wan models on DashScope API.

Supports ALL video generation modes:
  t2v   -- text-to-video (prompt only)
  i2v   -- image-to-video based on first frame
  kf2v  -- image-to-video based on first + last frames
  r2v   -- reference-based video (character role-play)
  vace  -- video editing (multi-image ref, repainting, edit, extension, outpainting)
  animate -- image-to-animation (character image + reference video, wan2.2-animate-*)

Submits async task, polls until completion, downloads video.
Self-contained, stdlib only.
"""
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
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qwencloud_lib import (  # noqa: E402
    check_token_plan_model_support,
    download_file,
    http_request,
    is_token_plan_key,
    is_token_plan_model_supported,
    load_request,
    native_base_url,
    poll_task,
    require_api_key,
    run_update_signal,
    sanitize_diagnostic,
)
from video_lib import (  # noqa: E402
    ENDPOINTS,
    MODE_ANIMATE,
    MODE_I2V,
    MODE_KF2V,
    MODE_VIDEO_EDIT,
    PAYLOAD_BUILDERS,
    RESOLVE_KEYS,
    detect_mode,
    get_default_model,
    is_animate_model,
    is_happyhorse_i2v_model,
    is_video_edit_model,
    is_wan27_i2v_model,
    resolve_request_urls,
    extract_video_url,
    estimate_cost,
    resolve_resolution,
    format_task_status,
)

# ---------------------------------------------------------------------------
# Token Plan credits usage consoles — PAYG pricing is irrelevant for TP keys
_TOKEN_PLAN_PERSONAL_CONSOLE_URL = (
    "https://home.qwencloud.com/analytics/token-plan/individual"
)
_TOKEN_PLAN_TEAM_CONSOLE_URL = "https://home.qwencloud.com/analytics/token-plan/team"
# Model market — activation guidance for models not yet enabled on the account
_MODEL_MARKET_URL = "https://www.qwencloud.com/models/"

# Error keywords indicating the model is not activated/subscribed (case-insensitive)
_ACTIVATION_ERROR_HINTS = ("not activated", "not subscribed", "activation", "activate")


def _check_not_activated(error_text: str, model: str, api_key: str) -> None:
    """Print activation guidance when the API error indicates the model is not activated."""
    text = (error_text or "").lower()
    if not any(h in text for h in _ACTIVATION_ERROR_HINTS):
        return
    if is_token_plan_key(api_key):
        print(
            f"Hint: model '{model}' may not be included in your Token Plan subscription.\n"
            "Manage your subscription:\n"
            f"  Personal: {_TOKEN_PLAN_PERSONAL_CONSOLE_URL}\n"
            f"  Team: {_TOKEN_PLAN_TEAM_CONSOLE_URL}",
            file=sys.stderr,
        )
    else:
        print(
            f"Hint: model '{model}' may require activation before use.\n"
            f"Activate it at {_MODEL_MARKET_URL}{model} "
            "(see the model's page for activation steps).",
            file=sys.stderr,
        )


def _handle_result(result: dict[str, Any], args: argparse.Namespace,
                   model: str = "", api_key: str = "") -> None:
    output = result.get("output", {})
    status = output.get("task_status", "")
    if status != "SUCCEEDED":
        msg = output.get("message", "Unknown error")
        code = output.get("code", "")
        _check_not_activated(f"{code}: {msg}" if code else msg, model, api_key)
        print(sanitize_diagnostic(f"Error: Task failed ({status}): {msg}"), file=sys.stderr)
        sys.exit(1)

    video_url = extract_video_url(result)
    if not video_url:
        print(sanitize_diagnostic(f"Error: No video URL in result: {result}"), file=sys.stderr)
        sys.exit(1)

    args.output.mkdir(parents=True, exist_ok=True)
    resp_file = args.output / "response.json"
    resp_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Response saved to {resp_file}", file=sys.stderr)

    # Use URL basename for unique filename (contains task ID from API)
    url_basename = Path(urlparse(video_url).path).name
    if url_basename and "." in url_basename:
        video_file = args.output / url_basename
    else:
        video_file = args.output / "video.mp4"
    try:
        download_file(video_url, video_file)
    except Exception as e:
        print(sanitize_diagnostic(f"Warning: Could not download video: {e}"), file=sys.stderr)
    else:
        print(f"Video saved to {video_file}", file=sys.stderr)

    if args.print_response:
        print(json.dumps({
            "video_url": video_url,
            "local_path": str(video_file),
        }, ensure_ascii=False))

    print(sanitize_diagnostic(f"Video URL: {video_url}"), file=sys.stderr)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    run_update_signal(caller=__file__)
    parser = argparse.ArgumentParser(
        description="Generate video via Wan models (t2v/i2v/kf2v/r2v/vace)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
mode auto-detection (from request JSON fields; defaults load from CDN config):
  t2v   prompt only → text-to-video
  i2v   img_url/media/first_frame_url → image-to-video
  kf2v  first_frame_url (without media) → keyframe-to-video
  r2v   reference_urls → reference role-play
  vace  function → video editing/repaint/extend
  videoedit  model-id (wan2.7-videoedit / happyhorse-1.0-video-edit) →
        media-based video editing
  animate    model-id (wan2.2-animate-move / wan2.2-animate-mix) →
        image-to-animation

model version differences (handled automatically):
  wan2.6-t2v: uses "size" param (e.g. "1280*720"), supports seed, shot_type
  wan2.7-t2v / happyhorse-1.0-t2v / happyhorse-1.1-t2v: use "resolution" + "ratio" params
  wan2.6-i2v: single img_url input
  wan2.7-i2v: media array (first_frame, last_frame, driving_audio, first_clip)
  wan3.0-video / wan3.0-video-prime: media array i2v + optional "ratio" param
    (adaptive/16:9/9:16/1:1) on top of resolution/duration
  happyhorse-1.0-i2v / happyhorse-1.1-i2v: strict spec — media=[{type:'first_frame', url}]
    (exactly one); only resolution/duration/watermark/seed params. Rejects
    negative_prompt / prompt_extend / ratio / last_frame / first_clip / driving_audio.
    Legacy img_url is auto-converted for convenience.
  wan2.7-videoedit / happyhorse-1.0-video-edit: media=[{type:'video', url}] +
    [{type:'reference_image', url}] (no `function` field). wan2.7-videoedit also
    supports negative_prompt + ratio/duration/prompt_extend; happyhorse only
    resolution/watermark/audio_setting/seed (prompt required).
  wan2.2-animate-move / wan2.2-animate-mix: image_url (character) + video_url
    (reference video, 2-30s) + mode ("wan-std" faster / "wan-pro" smoother,
    required) + optional check_image. NO prompt, NO resolution/duration/seed.

request JSON fields (--request / --file):
  prompt            Text description (required for t2v/i2v/r2v, optional for vace)
  duration          Video length in seconds (default: 5, wan2.7: 2-15)
  size              Resolution for wan2.6 t2v/r2v, e.g. "1280*720"
  resolution        Resolution for wan2.7/i2v/kf2v, e.g. "720P", "1080P"
  ratio             Aspect ratio for wan2.7-t2v, e.g. "16:9", "9:16"
  img_url           First-frame image (i2v wan2.6 / happyhorse-i2v compat)
  first_frame_url   First frame (wan2.7-i2v/kf2v)
  last_frame_url    Last frame (wan2.7-i2v/kf2v)
  first_clip_url    Video to continue (wan2.7-i2v)
  driving_audio_url Audio for lip-sync (wan2.7-i2v)
  media             Array of {type, url} for wan2.7-i2v / happyhorse-i2v / videoedit
  reference_urls    Character reference URLs (r2v)
  reference_images  Reference image URLs (videoedit)
  function          VACE: repainting, editing, extension, outpainting
  image_url         Character image URL/path (animate)
  video_url         Source video (VACE / videoedit / animate)
  mode              Service mode: "wan-std" / "wan-pro" (animate, required)
  audio_url         Audio track (t2v/i2v)
  negative_prompt   What to avoid
  seed              Reproducibility (wan2.6 only)
  prompt_extend     Auto-enhance prompt (default: true)
  watermark         Add watermark (default: false)

local files:
  Local paths are auto-uploaded to DashScope temp storage (48h TTL).

environment variables:
  QWENCLOUD_API_KEY  (preferred) API key — also loaded from .env
  QWEN_API_KEY       (fallback) Legacy alias
  DASHSCOPE_API_KEY  (fallback) Legacy provider variable
  QWEN_REGION        ap-southeast-1 (default)

examples:
  # Text-to-video (wan2.6)
  python scripts/video.py --request '{"prompt":"A cat playing piano","duration":5}'

  # Text-to-video with wan2.7 (ratio, auto-dubbing)
  python scripts/video.py --request '{"prompt":"Multi-shot cinematic...",
    "resolution":"1080P","ratio":"16:9","duration":15}' --model wan2.7-t2v

  # Image-to-video (wan2.6)
  python scripts/video.py --request '{"prompt":"Animate this","img_url":"photo.jpg"}'

  # Image-to-video with wan2.7 (first frame + audio sync)
  python scripts/video.py --request '{"prompt":"A rapper sings","first_frame_url":"rapper.png",
    "driving_audio_url":"rap.mp3"}' --model wan2.7-i2v

  # Video continuation with wan2.7
  python scripts/video.py --request '{"prompt":"Dog continues skateboarding",
    "first_clip_url":"dog_skateboard.mp4"}' --model wan2.7-i2v

  # Submit only, then resume later
  python scripts/video.py --request '{"prompt":"A sunset"}' --submit-only
  python scripts/video.py --task-id <TASK_ID>

  # VACE video editing
  python scripts/video.py --request '{"function":"repainting",
    "video_url":"input.mp4","prompt":"Change sky to sunset"}'

  # Video editing with wan2.7-videoedit (media[] protocol, no `function`)
  python scripts/video.py --request '{"prompt":"Replace the man with a robot",
    "video_url":"input.mp4","reference_images":["robot.png"],
    "resolution":"1080P","ratio":"16:9"}' --model wan2.7-videoedit

  # Image-to-video with happyhorse-i2v (img_url auto-promoted to media first_frame)
  python scripts/video.py --request '{"prompt":"gentle motion",
    "img_url":"photo.png"}' --model happyhorse-1.1-i2v

  # Image-to-animation: transfer actions from a reference video to a character
  python scripts/video.py --request '{"image_url":"character.jpg",
    "video_url":"dance.mp4","mode":"wan-std"}' --model wan2.2-animate-move
""",
    )
    parser.add_argument("--request", type=str, help="Inline JSON: fields depend on mode")
    parser.add_argument("--file", type=Path, help="Path to JSON file containing request body")
    parser.add_argument("--output", type=Path, default=Path("output/qwencloud-video-generation"),
                        help="Directory to save response and video (default: %(default)s)")
    parser.add_argument("--print-response", action="store_true", help="Print video URL to stdout")
    parser.add_argument("--model", type=str,
                        help="Model ID (overrides auto-default; see epilog for defaults per mode)")
    parser.add_argument("--mode", type=str,
                        choices=["t2v", "i2v", "kf2v", "r2v", "vace", "videoedit", "animate"],
                        help="Force mode (auto-detected from request fields if omitted). "
                             "'videoedit' is for wan2.7-videoedit / happyhorse-1.0-video-edit; "
                             "'animate' is for wan2.2-animate-move / wan2.2-animate-mix.")
    parser.add_argument("--poll-interval", type=int, default=15,
                        help="Seconds between poll attempts (default: 15)")
    parser.add_argument("--timeout", type=int, default=600,
                        help="Max seconds to wait for task (default: 600)")
    parser.add_argument("--submit-only", action="store_true",
                        help="Submit task, print task_id to stdout, exit without polling")
    parser.add_argument("--task-id", type=str,
                        help="Resume polling an existing task (skip submission)")
    parser.add_argument("--poll-once", action="store_true",
                        help="With --task-id: single status check, exit code 2 if not done")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress progress output during polling")
    args = parser.parse_args()

    verbose = not args.quiet
    api_key = require_api_key(script_file=__file__, domain="Video")

    # --- Single check mode ---
    if args.task_id and args.poll_once:
        result = http_request("GET", f"{native_base_url()}/tasks/{args.task_id}", api_key)
        if verbose:
            print(f"  {format_task_status(result)}", file=sys.stderr)
        status = result.get("output", {}).get("task_status", "")
        if status in ("SUCCEEDED", "FAILED", "CANCELED"):
            _handle_result(result, args, model=args.model or "", api_key=api_key)
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(2)
        return

    # --- Resume mode ---
    if args.task_id:
        task_id = args.task_id
        if verbose:
            print(sanitize_diagnostic(f"Resuming task: {task_id}"), file=sys.stderr)
            print(f"Polling every {args.poll_interval}s (timeout: {args.timeout}s)...",
                  file=sys.stderr)
        try:
            result = poll_task(task_id, api_key,
                               timeout_s=args.timeout, interval=args.poll_interval,
                               verbose=verbose)
        except TimeoutError as e:
            print(sanitize_diagnostic(f"Error: {e}"), file=sys.stderr)
            print(sanitize_diagnostic(f"Task may still be running. Resume with: --task-id {task_id}"), file=sys.stderr)
            sys.exit(1)
        _handle_result(result, args, model=args.model or "", api_key=api_key)
        return

    # --- Normal mode: submit new task ---
    try:
        request = load_request(args)
    except ValueError as e:
        print(sanitize_diagnostic(f"Error: {e}"), file=sys.stderr)
        sys.exit(1)

    try:
        mode = args.mode or detect_mode(request, model=args.model or request.get("model", ""))
        model = args.model or request.get("model") or get_default_model(mode)
        check_token_plan_model_support(model, domain="Video")
        # Model-aware correction: wan2.7-i2v / happyhorse-i2v use first_frame_url
        # but belong to i2v mode (detect_mode would have classified them as kf2v).
        if is_wan27_i2v_model(model) or is_happyhorse_i2v_model(model):
            if mode == MODE_KF2V:
                mode = MODE_I2V
        # Correct model-routed modes when the request shape alone is ambiguous.
        if is_video_edit_model(model) and mode != MODE_VIDEO_EDIT:
            mode = MODE_VIDEO_EDIT
        if is_animate_model(model) and mode != MODE_ANIMATE:
            mode = MODE_ANIMATE
        duration = request.get("duration", 5)
        resolution = resolve_resolution(request, mode)
        # Token Plan keys consume credits, not PAYG pricing.
        token_plan = is_token_plan_key(api_key)
        token_plan_model = is_token_plan_model_supported(model, "Video")
        cost_str = None if token_plan else estimate_cost(model, duration, resolution)

        if verbose:
            info = f"Mode: {mode} | Model: {model}"
            if token_plan and token_plan_model:
                info += (
                    f" | Credits: Personal {_TOKEN_PLAN_PERSONAL_CONSOLE_URL}"
                    f" | Team {_TOKEN_PLAN_TEAM_CONSOLE_URL}"
                )
            elif token_plan:
                info += " | Billing: PAYG-only model (not available on Token Plan)"
            elif cost_str:
                info += f" | Cost: {cost_str}"
            print(info, file=sys.stderr)

        resolve_request_urls(request, api_key, model, RESOLVE_KEYS[mode])
        builder = PAYLOAD_BUILDERS[mode]
        payload = builder(request, model)
    except (ValueError, KeyError, RuntimeError) as e:
        print(sanitize_diagnostic(f"Error: {e}"), file=sys.stderr)
        sys.exit(1)

    url = f"{native_base_url()}{ENDPOINTS[mode]}"

    try:
        resp = http_request("POST", url, api_key, payload,
                            extra_headers={"X-DashScope-Async": "enable"}, timeout=60)
    except Exception as e:
        _check_not_activated(str(e), model, api_key)
        print(sanitize_diagnostic(f"API error: {e}"), file=sys.stderr)
        sys.exit(1)

    task_id = resp.get("output", {}).get("task_id")
    if not task_id:
        print(sanitize_diagnostic(f"Error: No task_id in response: {json.dumps(resp, ensure_ascii=False)}")[:500],
              file=sys.stderr)
        sys.exit(1)

    if verbose:
        print(sanitize_diagnostic(f"Task submitted: {task_id}"), file=sys.stderr)

    if args.submit_only:
        print(task_id)
        return

    if verbose:
        print(f"Polling every {args.poll_interval}s (timeout: {args.timeout}s)...",
              file=sys.stderr)

    try:
        result = poll_task(task_id, api_key,
                           timeout_s=args.timeout, interval=args.poll_interval,
                           verbose=verbose)
    except TimeoutError as e:
        print(sanitize_diagnostic(f"Error: {e}"), file=sys.stderr)
        print(sanitize_diagnostic(f"Task may still be running. Resume with: --task-id {task_id}"), file=sys.stderr)
        sys.exit(1)

    _handle_result(result, args, model=model, api_key=api_key)

if __name__ == "__main__":
    main()
