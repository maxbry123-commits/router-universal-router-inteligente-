"""Shared cloud AI client infrastructure for qwencloud/qwencloud-ai skills.

Provider-based architecture: generic HTTP, env, and file-handling infrastructure
with pluggable AI provider implementations.  DashScope is the built-in default;
additional providers can be registered via ``register_provider()``.

Modules are organised by responsibility:
  - Environment & credentials: load_dotenv, find_repo_root, require_api_key
  - Provider abstraction: AIProvider, DashScopeProvider, register_provider
  - Region & endpoints: compat_base_url, native_base_url
  - HTTP client: http_request, http_post, stream_sse
  - File I/O: upload_local_file, resolve_file, download_file
  - Request/response utilities: load_request, save_result, extract_text
  - Update-check signal: run_update_signal

Stdlib only -- no pip install required.
"""
from __future__ import annotations

import sys

if sys.version_info < (3, 9):
    print(
        f"Error: Python 3.9+ required (found {sys.version}). "
        "Install: https://www.python.org/downloads/",
        file=sys.stderr,
    )
    sys.exit(1)

import base64
import http.client
import inspect
import json
import mimetypes
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any, BinaryIO, Callable, Generator, Iterator, Optional


_MODEL_CONFIG_CDN_BASE = (
    "https://alioth-intl.alicdn.com/skills-info/models/config/"
)
_MODEL_CONFIG_TIMEOUT_SECONDS = 3
# Keep the symlink path when this shared module is imported from an individual
# skill. Resolving it would incorrectly point at ``skills/_lib/cdn`` in the
# source repository instead of that skill's bundled fallback directory.
_MODEL_CONFIG_LOCAL_DIR = Path(__file__).absolute().parent.parent / "cdn" / "config"
_MODEL_CONFIG_CACHE: dict[tuple[str, str], dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Section 1: Generic environment & credential loading
# ---------------------------------------------------------------------------

def find_repo_root(start: Path) -> Path | None:
    """Walk up from *start* looking for a repository root marker.

    Returns the first directory that contains ``.git`` or a ``skills/``
    subdirectory, or ``None`` if no marker is found.
    """
    for parent in [start] + list(start.parents):
        if (parent / ".git").exists() or (parent / "skills").is_dir():
            return parent
    return None


def load_dotenv(path: Path) -> None:
    """Parse a simple ``.env`` file and inject into ``os.environ``.

    Existing environment variables are **not** overwritten.
    """
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_env(script_file: str | Path | None = None) -> None:
    """Load ``.env`` files with proper priority: current dir > repo root.

    Parameters
    ----------
    script_file : str or Path, optional
        ``__file__`` of the calling script, used to locate the repo root.
    """
    load_dotenv(Path.cwd() / ".env")
    origin = Path(script_file).resolve() if script_file else None
    if origin:
        repo = find_repo_root(origin)
        if repo:
            load_dotenv(repo / ".env")


def load_cdn_model_config(
        filename: str,
        *,
        local_dir: str | Path | None = None,
        required_keys: tuple[str, ...] = (),
        validator: Callable[[dict[str, Any]], bool | None] | None = None,
) -> dict[str, Any]:
    """Load model configuration from the CDN, then a bundled local fallback.

    ``local_dir`` lets callers identify their own ``cdn/config`` directory.
    This matters in the source tree, where this module is shared through
    symlinks, while installed skills may contain a materialized copy.
    """
    if (
        Path(filename).name != filename
        or "/" in filename
        or "\\" in filename
        or not filename.endswith(".json")
        or not filename[:-5]
    ):
        raise ValueError(f"Invalid model configuration filename: {filename!r}")

    def validate(config: Any) -> dict[str, Any]:
        if not isinstance(config, dict):
            raise RuntimeError("expected a JSON object")
        missing = [key for key in required_keys if key not in config]
        if missing:
            raise RuntimeError(f"missing {', '.join(missing)}")
        if validator is not None and validator(config) is False:
            raise RuntimeError("custom validation failed")
        return config

    url = urllib.parse.urljoin(_MODEL_CONFIG_CDN_BASE, filename)
    fallback_dir = Path(local_dir) if local_dir is not None else _MODEL_CONFIG_LOCAL_DIR
    local_path = fallback_dir / filename
    if local_dir is None and not local_path.is_file():
        repository_copy = (
            Path(__file__).resolve().parents[2]
            / "skills-info"
            / "models"
            / "config"
            / filename
        )
        if repository_copy.is_file():
            local_path = repository_copy
    cache_key = (filename, str(local_path.absolute()))
    cached = _MODEL_CONFIG_CACHE.get(cache_key)
    if cached is not None:
        try:
            return validate(cached)
        except (RuntimeError, TypeError, ValueError):
            # A later caller may require a stricter schema for the same file.
            # Re-resolve it so a valid bundled fallback can still recover.
            _MODEL_CONFIG_CACHE.pop(cache_key, None)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "qwencloud-skills"},
    )

    try:
        with urllib.request.urlopen(request, timeout=_MODEL_CONFIG_TIMEOUT_SECONDS) as response:
            config = validate(json.loads(response.read().decode("utf-8")))
    except (
        OSError,
        TimeoutError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        http.client.HTTPException,
        RuntimeError,
        TypeError,
        ValueError,
    ) as cdn_exc:
        try:
            config = validate(json.loads(local_path.read_text(encoding="utf-8")))
        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            RuntimeError,
            TypeError,
            ValueError,
        ) as local_exc:
            raise RuntimeError(
                f"Unable to load valid model configuration from {url} or {local_path}: "
                f"CDN error: {cdn_exc}; local error: {local_exc}"
            ) from local_exc

    _MODEL_CONFIG_CACHE[cache_key] = config
    return config


def mask_key(key: str) -> str:
    """Return a masked version of an API key for safe logging.

    Shows the first 4 and last 4 characters with ``...`` in between.
    Keys shorter than 9 characters are fully masked.
    """
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


# Match both ordinary URLs and JSON-escaped slashes in SDK/API messages.
_DIAGNOSTIC_URL = re.compile(r"https?:(?:\\*/){2}[^\s<>\"']+", re.IGNORECASE)
# Prefixes of the same URL grammar, including partially written JSON escapes.
_DIAGNOSTIC_URL_PREFIX = re.compile(
    r"(?:h|ht|htt|http|https|https?:(?:\\*|\\*/\\*|(?:\\*/){2}))$",
    re.IGNORECASE,
)


def sanitize_diagnostic(text: str) -> str:
    """Remove URL queries/fragments from diagnostics, never from API data.

    Drop the entire query instead of maintaining a list of credential names:
    OSS V1/V4 signatures and temporary security tokens must all stay private.
    Call this before truncating an external error message.
    """
    def redact(match: re.Match) -> str:
        url = match.group()
        parts = re.split(r"([?#])", url, maxsplit=1)
        if len(parts) == 1:
            return url
        if re.fullmatch(r"\[REDACTED\][.,;:!)\]}]*", parts[2]):
            return url
        # Preserve closing prose/Markdown delimiters outside the URL.
        suffix = url[len(url.rstrip(".,;:!)]}")):]
        return f"{parts[0]}{parts[1]}[REDACTED]{suffix}"

    return _DIAGNOSTIC_URL.sub(redact, text)


class DiagnosticStream:
    """Redact streaming diagnostics even when a URL spans multiple writes.

    Hold an unfinished URL or scheme prefix; ordinary text stays live.
    ``flush()`` finishes the message; callers must not flush between chunks.
    Structured results should use the original data, not this stream.
    """

    def __init__(self, stream: Any = None) -> None:
        self._stream = sys.stderr if stream is None else stream
        self._pending = ""

    def write(self, text: str) -> None:
        self._pending += text
        end = len(self._pending)
        for match in _DIAGNOSTIC_URL.finditer(self._pending):
            if match.end() == len(self._pending):
                end = match.start()
                break
        else:
            # Even "ht" at the end of a chunk may start the next signed URL.
            prefix = _DIAGNOSTIC_URL_PREFIX.search(self._pending)
            if prefix:
                end = prefix.start()
        if end:
            self._stream.write(sanitize_diagnostic(self._pending[:end]))
            self._stream.flush()
            self._pending = self._pending[end:]

    def flush(self) -> None:
        self._stream.write(sanitize_diagnostic(self._pending))
        self._pending = ""
        self._stream.flush()


# ---------------------------------------------------------------------------
# Section 2: AIProvider base class
# ---------------------------------------------------------------------------

class AIProvider:
    """Base interface for an AI service provider.

    Subclasses must implement all methods.  The built-in ``DashScopeProvider``
    is registered by default; additional providers can be added via
    ``register_provider()`` and selected at runtime with the ``QWEN_PROVIDER``
    environment variable.
    """

    name: str = ""

    # --- Authentication ---

    def get_api_key_env_name(self) -> str:
        """Return the environment variable name for this provider's API key."""
        raise NotImplementedError

    def get_console_url(self) -> str:
        """Return the URL where users can obtain an API key."""
        raise NotImplementedError

    def validate_api_key(
            self,
            key: str,
            *,
            allow_coding_plan: bool = False,
            domain: str = "",
    ) -> str:
        """Validate *key* and return it, or ``sys.exit`` with guidance.

        Provider-specific checks (e.g. prefix validation) go here.
        """
        raise NotImplementedError

    # --- Endpoints ---

    def compat_base_url(self) -> str:
        """Return the OpenAI-compatible API base URL."""
        raise NotImplementedError

    def native_base_url(self) -> str:
        """Return the provider's native API base URL."""
        raise NotImplementedError

    # --- HTTP headers ---

    def make_headers(
            self,
            api_key: str,
            payload: Any = None,
    ) -> dict[str, str]:
        """Build HTTP request headers.

        *payload* is provided so that providers can inject conditional
        headers (e.g. DashScope's ``X-DashScope-OssResourceResolve``).
        """
        raise NotImplementedError

    # --- Managed file URLs ---

    def has_managed_url(self, obj: Any) -> bool:
        """Check whether *obj* contains any provider-managed file URLs."""
        raise NotImplementedError

    def managed_url_schemes(self) -> tuple[str, ...]:
        """Return URL scheme prefixes for provider-managed storage.

        Used by ``resolve_file`` to detect URLs that should pass through
        without modification (e.g. ``("oss://",)`` for DashScope).
        """
        raise NotImplementedError

    # --- File upload ---

    def upload_file(self, api_key: str, model: str, fp: Path) -> str:
        """Upload a local file to provider temp storage.

        Returns a provider-managed URL string.
        """
        raise NotImplementedError

    # --- Async task polling ---

    def task_poll_url(self, task_id: str) -> str:
        """Build the URL to poll an async task's status."""
        raise NotImplementedError

    def extract_task_status(self, result: dict[str, Any]) -> str:
        """Extract the task status string from a poll response."""
        raise NotImplementedError

    def terminal_statuses(self) -> frozenset[str]:
        """Return the set of terminal task statuses."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Section 3: Token Plan configuration
# ---------------------------------------------------------------------------

_TOKEN_PLAN_MODEL_CONFIG = "qwencloud-token-plan-config.json"

_TOKEN_PLAN_COMPAT_BASE = "https://token-plan.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
_TOKEN_PLAN_NATIVE_BASE = "https://token-plan.ap-southeast-1.maas.aliyuncs.com/api/v1"


def _validate_token_plan_config(config: dict[str, Any]) -> bool:
    personal = config.get("personal_models")
    team = config.get("team_models")
    if not isinstance(personal, list) or not all(isinstance(item, str) for item in personal):
        return False
    if not isinstance(team, list) or not all(isinstance(item, str) for item in team):
        return False
    return (
        bool(personal)
        and bool(team)
        and len(personal) == len(set(personal))
        and len(team) == len(set(team))
        and set(personal).issubset(team)
    )


def _load_token_plan_catalog() -> tuple[frozenset[str], frozenset[str]]:
    config = load_cdn_model_config(
        _TOKEN_PLAN_MODEL_CONFIG,
        required_keys=("personal_models", "team_models"),
        validator=_validate_token_plan_config,
    )
    personal = frozenset(config["personal_models"])
    team = frozenset(config["team_models"])
    return personal, team


def get_api_key_from_env(fallback_env: str = "DASHSCOPE_API_KEY") -> str:
    """Return the configured API key using the shared credential precedence.

    ``QWENCLOUD_API_KEY`` is the preferred public name.  The legacy
    ``QWEN_API_KEY`` alias and the provider's ``fallback_env`` remain
    supported for existing installations.
    """
    return (
        os.getenv("QWENCLOUD_API_KEY", "").strip()
        or os.getenv("QWEN_API_KEY", "").strip()
        or os.getenv(fallback_env, "").strip()
    )


def is_token_plan_key(api_key: str | None = None) -> bool:
    """Return True if the given (or env-sourced) API key is a Token Plan key.

    When *api_key* is ``None``, falls back to the shared environment lookup:
    ``QWENCLOUD_API_KEY``, then ``QWEN_API_KEY``, then
    ``DASHSCOPE_API_KEY``.
    """
    if api_key is None:
        api_key = get_api_key_from_env()
    return api_key.startswith("sk-sp-")


def detect_api_key_type(script_file: str | Path | None = None) -> str:
    """Return the API key type: ``'token-plan'``, ``'payg'``, or ``'not-set'``.

    Parameters
    ----------
    script_file : str or Path, optional
        ``__file__`` of the calling script, used to locate ``.env`` files.
    """
    load_env(script_file)
    key = get_api_key_from_env()
    if not key:
        return "not-set"
    return "token-plan" if key.startswith("sk-sp-") else "payg"


def is_token_plan_model(model: str) -> bool:
    """Check if a model is supported by Token Plan (any edition)."""
    _, team_models = _load_token_plan_catalog()
    return model in team_models


def is_token_plan_personal_model(model: str) -> bool:
    """Check if a model is supported by Token Plan Personal Edition."""
    personal_models, _ = _load_token_plan_catalog()
    return model in personal_models


def is_token_plan_model_supported(model: str, domain: str = "") -> bool:
    """Return whether Token Plan supports *model* in any edition.

    ``domain`` is retained for caller compatibility but model capabilities are
    intentionally not duplicated in the Token Plan configuration.
    """
    return is_token_plan_model(model)


def check_token_plan_model_support(model: str, domain: str = "") -> None:
    """Warn with actionable guidance when a Token Plan key is used with an unsupported model.

    Prints a friendly suggestion to stderr (does not block execution — the API
    may still accept it for edge cases we don't track).  Call after
    ``require_api_key()`` so that ``.env`` files have been loaded.

    Parameters
    ----------
    model : str
        Model ID being requested.  Empty/None stays silent (nothing to check).
    domain : str
        Optional caller context used only in warning text. Model capabilities
        are not stored in the Token Plan configuration. This function also does
        not detect Personal vs Team entitlement.
    """
    if not is_token_plan_key():
        return  # PAYG key — no restriction
    if not model:
        return
    if is_token_plan_model_supported(model, domain):
        return
    capability_note = f" for {domain}" if domain else ""
    lines = [f"Warning: model '{model}' is not available on Token Plan{capability_note}."]
    _, team_models = _load_token_plan_catalog()
    lines.append(
        f"All Token Plan-supported models: "
        f"{', '.join(sorted(team_models))}"
    )
    lines.append(
        f"Alternative: switch to a supported model above, or use a PAYG key "
        f"(sk-...) for '{model}'."
    )
    lines.extend([
        "Personal docs: "
        "https://docs.qwencloud.com/token-plan/personal/token-plan-personal-overview",
        "Team docs: "
        "https://docs.qwencloud.com/token-plan/team/token-plan-team-overview",
    ])
    print("\n".join(lines), file=sys.stderr)


# ---------------------------------------------------------------------------
# Section 4: DashScopeProvider implementation
# ---------------------------------------------------------------------------

class DashScopeProvider(AIProvider):
    """Built-in provider for Alibaba Cloud Model Studio (DashScope)."""

    name = "dashscope"

    _CONSOLE_URL = "https://home.qwencloud.com/api-keys"

    _COMPAT_BASE: dict[str, str] = {
        "ap-southeast-1": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    }

    _NATIVE_BASE: dict[str, str] = {
        "ap-southeast-1": "https://dashscope-intl.aliyuncs.com/api/v1",
    }

    # --- Authentication ---

    def get_api_key_env_name(self) -> str:
        return "DASHSCOPE_API_KEY"

    def get_console_url(self) -> str:
        return self._CONSOLE_URL

    def validate_api_key(
            self,
            key: str,
            *,
            allow_coding_plan: bool = False,
            domain: str = "",
    ) -> str:
        self._current_key = key  # Remember key for Token Plan routing
        return key

    # --- Endpoints ---

    def compat_base_url(self) -> str:
        url = os.getenv("QWEN_BASE_URL")
        region = os.getenv("QWEN_REGION", "ap-southeast-1").lower()
        if region == "none":
            # When QWEN_REGION=none, skip URL assembly and return the user-configured base URL as-is.
            if not url:
                raise RuntimeError(
                    "QWEN_BASE_URL must be set when QWEN_REGION=none."
                )
            return url.rstrip("/")
        if url:
            return url.rstrip("/")
        # Token Plan routing: sk-sp- key → TP endpoint
        if is_token_plan_key(self._current_key if hasattr(self, "_current_key") else None):
            return _TOKEN_PLAN_COMPAT_BASE
        return self._COMPAT_BASE.get(region, self._COMPAT_BASE["ap-southeast-1"])

    def native_base_url(self) -> str:
        custom = os.getenv("QWEN_BASE_URL")
        region = os.getenv("QWEN_REGION", "ap-southeast-1").lower()
        if region == "none":
            # When QWEN_REGION=none, skip URL assembly and return the user-configured base URL as-is.
            if not custom:
                raise RuntimeError(
                    "QWEN_BASE_URL must be set when QWEN_REGION=none."
                )
            return custom.rstrip("/")
        if custom:
            parsed = urllib.parse.urlparse(custom.rstrip("/"))
            return f"{parsed.scheme}://{parsed.netloc}/api/v1"
        # Token Plan routing
        if is_token_plan_key(self._current_key if hasattr(self, "_current_key") else None):
            return _TOKEN_PLAN_NATIVE_BASE
        return self._NATIVE_BASE.get(region, self._NATIVE_BASE["ap-southeast-1"])

    # --- HTTP headers ---

    def make_headers(
            self,
            api_key: str,
            payload: Any = None,
    ) -> dict[str, str]:
        hdrs: dict[str, str] = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "qwencloud-skills",  # Required for Token Plan
        }
        if payload and self.has_managed_url(payload):
            hdrs["X-DashScope-OssResourceResolve"] = "enable"
        source_cfg = build_source_config()
        if source_cfg:
            hdrs["X-DashScope-Source-Config"] = source_cfg
        return hdrs

    # --- Managed file URLs ---

    def has_managed_url(self, obj: Any) -> bool:
        if isinstance(obj, str):
            return obj.startswith("oss://")
        if isinstance(obj, dict):
            return any(self.has_managed_url(v) for v in obj.values())
        if isinstance(obj, (list, tuple)):
            return any(self.has_managed_url(v) for v in obj)
        return False

    def managed_url_schemes(self) -> tuple[str, ...]:
        return ("oss://",)

    # --- File upload (OSS) ---

    def upload_file(self, api_key: str, model: str, fp: Path) -> str:
        """Upload a local file and return a URL for API consumption.

        When ``QWEN_TMP_OSS_BUCKET`` is set, files go to the user's own
        OSS bucket and a presigned ``https://`` URL is returned.
        Otherwise, files go to DashScope temp storage (48 h TTL) and an
        ``oss://`` URL is returned.
        """
        if os.getenv("QWEN_TMP_OSS_BUCKET"):
            # Custom OSS upload uses the user's own bucket/credentials and is
            # available regardless of key type.
            return self._upload_to_user_oss(fp)
        # Token Plan keys cannot use the upload API
        if is_token_plan_key(api_key):
            raise RuntimeError(
                "Local file upload is not available on Token Plan.\n"
                "Alternative: host the file at a publicly accessible https:// URL "
                "and pass that URL directly.\n"
                "Docs: https://docs.qwencloud.com/token-plan/overview"
            )
        policy = self._get_upload_policy(api_key, model)
        key = f"{policy['upload_dir']}/{fp.name}"
        mime = mimetypes.guess_type(fp.name)[0] or "application/octet-stream"
        fields = {
            "OSSAccessKeyId": policy["oss_access_key_id"],
            "Signature": policy["signature"],
            "policy": policy["policy"],
            "x-oss-object-acl": policy["x_oss_object_acl"],
            "x-oss-forbid-overwrite": policy["x_oss_forbid_overwrite"],
            "key": key,
            "success_action_status": "200",
        }
        try:
            with fp.open("rb") as file_obj:
                body, ct, content_length = self._build_multipart(
                    fields, fp.name, file_obj, mime,
                )
                try:
                    req = urllib.request.Request(
                        policy["upload_host"],
                        data=body,
                        method="POST",
                        headers={
                            "Content-Type": ct,
                            "Content-Length": str(content_length),
                        },
                    )
                    with urllib.request.urlopen(req, timeout=120) as resp:
                        if resp.status != 200:
                            raise RuntimeError(f"OSS upload HTTP {resp.status}")
                finally:
                    body.close()
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            raise RuntimeError(
                f"OSS upload failed (HTTP {exc.code}): {detail[:300]}"
            ) from exc
        return f"oss://{key}"

    def _upload_to_user_oss(self, fp: Path) -> str:
        """Upload a file to the user's own OSS bucket via alibabacloud-oss-v2.

        Returns a presigned ``https://`` URL.  Requires
        ``QWEN_TMP_OSS_BUCKET`` and ``QWEN_TMP_OSS_REGION``.
        Credentials are resolved from ``QWEN_TMP_OSS_AK_ID`` /
        ``QWEN_TMP_OSS_AK_SECRET`` first, falling back to
        ``OSS_ACCESS_KEY_ID`` / ``OSS_ACCESS_KEY_SECRET``
        environment variables via the SDK's built-in provider.
        """
        try:
            import alibabacloud_oss_v2 as oss  # type: ignore[import-untyped]
        except ImportError:
            print(
                "Error: alibabacloud-oss-v2 is required for custom OSS upload.\n"
                "Install: pip3 install alibabacloud-oss-v2\n"
                "Docs: https://www.alibabacloud.com/help/en/oss/developer-reference/"
                "simple-upload-using-oss-sdk-for-python-v2",
                file=sys.stderr,
            )
            sys.exit(1)
        from datetime import timedelta

        bucket = os.environ["QWEN_TMP_OSS_BUCKET"]
        region = os.getenv("QWEN_TMP_OSS_REGION", "")
        if not region:
            print(
                "Error: QWEN_TMP_OSS_REGION is required when "
                "QWEN_TMP_OSS_BUCKET is set.",
                file=sys.stderr,
            )
            sys.exit(1)

        ak_id = os.getenv("QWEN_TMP_OSS_AK_ID", "")
        ak_secret = os.getenv("QWEN_TMP_OSS_AK_SECRET", "")
        if ak_id and ak_secret:
            credentials_provider = oss.credentials.StaticCredentialsProvider(
                ak_id, ak_secret,
            )
        else:
            ak_id = os.getenv("OSS_ACCESS_KEY_ID", "")
            ak_secret = os.getenv("OSS_ACCESS_KEY_SECRET", "")
            credentials_provider = (
                oss.credentials.EnvironmentVariableCredentialsProvider()
            )

        cfg = oss.config.load_default()
        cfg.credentials_provider = credentials_provider
        cfg.region = region
        endpoint = os.getenv("QWEN_TMP_OSS_ENDPOINT")
        if endpoint:
            cfg.endpoint = endpoint
        client = oss.Client(cfg)

        prefix = os.getenv("QWEN_TMP_OSS_PREFIX", "qwencloud-skill-uploads").strip("/")
        from datetime import datetime as _dt
        date_dir = _dt.now().strftime("%Y%m%d")
        key = f"{prefix}/{date_dir}/{uuid.uuid4().hex[:8]}_{fp.name}"

        mime = mimetypes.guess_type(fp.name)[0] or "application/octet-stream"
        try:
            uploader = oss.Uploader(
                client,
                part_size=8 * 1024 * 1024,
                parallel_num=1,
            )
            uploader.upload_file(
                oss.PutObjectRequest(
                    bucket=bucket,
                    key=key,
                    content_type=mime,
                ),
                str(fp),
            )

            expires_s = int(os.getenv("QWEN_TMP_OSS_URL_EXPIRES", "86400"))
            presign_result = client.presign(
                oss.GetObjectRequest(bucket=bucket, key=key),
                expires=timedelta(seconds=expires_s),
            )
            return presign_result.url
        except Exception as exc:
            msg = sanitize_diagnostic(str(exc))
            if ak_id:
                msg = msg.replace(ak_id, mask_key(ak_id))
            if ak_secret:
                msg = msg.replace(ak_secret, mask_key(ak_secret))
            # The SDK exception may contain an unredacted signed URL too.
            raise RuntimeError(f"Custom OSS upload failed: {msg}") from None

    def _get_upload_policy(self, api_key: str, model: str) -> dict[str, Any]:
        url = (
            f"{self.native_base_url()}/uploads?"
            f"{urllib.parse.urlencode({'action': 'getPolicy', 'model': model})}"
        )
        req = urllib.request.Request(
            url,
            method="GET",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        data = body.get("data")
        if not data:
            raise RuntimeError(
                f"Upload policy error: {json.dumps(body, ensure_ascii=False)[:300]}"
            )
        return data

    @staticmethod
    def _build_multipart(
            fields: dict[str, str],
            fname: str,
            file_obj: BinaryIO,
            fmime: str,
    ) -> tuple[Generator[bytes, None, None], str, int]:
        """Build a streaming multipart body without buffering the file."""
        boundary = uuid.uuid4().hex
        parts: list[bytes] = []
        for k, v in fields.items():
            parts.append(
                f'--{boundary}\r\nContent-Disposition: form-data; '
                f'name="{k}"\r\n\r\n{v}\r\n'.encode()
            )
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{fname}"\r\n'
            f"Content-Type: {fmime}\r\n\r\n".encode()
        )
        prefix = b"".join(parts)
        suffix = f"\r\n--{boundary}--\r\n".encode()
        file_size = os.fstat(file_obj.fileno()).st_size

        def stream() -> Generator[bytes, None, None]:
            yield prefix
            remaining = file_size
            while remaining:
                chunk = file_obj.read(min(1024 * 1024, remaining))
                if not chunk:
                    raise RuntimeError("File changed while it was being uploaded")
                remaining -= len(chunk)
                yield chunk
            yield suffix

        content_length = len(prefix) + file_size + len(suffix)
        return (
            stream(),
            f"multipart/form-data; boundary={boundary}",
            content_length,
        )

    # --- Async task polling ---

    def task_poll_url(self, task_id: str) -> str:
        return f"{self.native_base_url()}/tasks/{task_id}"

    def extract_task_status(self, result: dict[str, Any]) -> str:
        return result.get("output", {}).get("task_status", "")

    def terminal_statuses(self) -> frozenset[str]:
        return frozenset({"SUCCEEDED", "FAILED", "CANCELED"})


# ---------------------------------------------------------------------------
# Section 4: Provider registry & resolution
# ---------------------------------------------------------------------------

_PROVIDERS: dict[str, type[AIProvider]] = {}
_cached_provider: AIProvider | None = None


def register_provider(name: str, cls: type[AIProvider]) -> None:
    """Register an AI provider class under *name*.

    Example::

        class MyProvider(AIProvider):
            name = "my_provider"
            ...

        register_provider("my_provider", MyProvider)
    """
    _PROVIDERS[name.lower()] = cls


def get_provider() -> AIProvider:
    """Return the active ``AIProvider`` instance.

    The provider is selected by the ``QWEN_PROVIDER`` environment variable
    (default ``"dashscope"``).  The instance is created lazily and cached
    for the lifetime of the process.
    """
    global _cached_provider
    if _cached_provider is not None:
        return _cached_provider
    name = os.getenv("QWEN_PROVIDER", "dashscope").lower()
    cls = _PROVIDERS.get(name)
    if cls is None:
        available = ", ".join(sorted(_PROVIDERS)) or "(none)"
        print(
            f"Error: Unknown provider '{name}'. "
            f"Available providers: {available}",
            file=sys.stderr,
        )
        sys.exit(1)
    _cached_provider = cls()
    return _cached_provider


def _reset_provider() -> None:
    """Clear the cached provider instance (for testing only)."""
    global _cached_provider
    _cached_provider = None


# Register built-in provider
register_provider("dashscope", DashScopeProvider)


# ---------------------------------------------------------------------------
# Section 5: Provider-delegating public facade functions
# ---------------------------------------------------------------------------

def require_api_key(
        *,
        script_file: str | Path | None = None,
        allow_coding_plan: bool = False,
        domain: str = "",
) -> str:
    """Load and return the API key for the active provider, or exit with guidance.

    Parameters
    ----------
    script_file : str or Path, optional
        ``__file__`` of the calling script -- used to locate ``.env``.
    allow_coding_plan : bool
        If ``False`` (default), Coding Plan keys emit a warning (DashScope).
    domain : str
        Human-readable domain name for error messages (e.g. "Image", "Video").
    """
    load_env(script_file)
    provider = get_provider()

    # Priority: QWENCLOUD_API_KEY > QWEN_API_KEY > provider fallback.
    fallback_env = provider.get_api_key_env_name()  # DASHSCOPE_API_KEY
    key = get_api_key_from_env(fallback_env)

    if not key:
        console = provider.get_console_url()
        print(
            f"Error: QWENCLOUD_API_KEY/QWEN_API_KEY/{fallback_env} not found.\n"
            f"Option 1: Add to .env file in project root or current directory:\n"
            f"  echo 'QWENCLOUD_API_KEY=sk-your-key-here' >> .env\n"
            f"Option 2: Export as environment variable:\n"
            f"  export QWENCLOUD_API_KEY='sk-...'\n"
            f"Get key: {console}",
            file=sys.stderr,
        )
        sys.exit(1)

    return provider.validate_api_key(
        key, allow_coding_plan=allow_coding_plan, domain=domain,
    )


def compat_base_url() -> str:
    """Return the OpenAI-compatible API base URL for the active provider."""
    return get_provider().compat_base_url()


def native_base_url() -> str:
    """Return the native API base URL for the active provider."""
    return get_provider().native_base_url()


def chat_url() -> str:
    """Convenience: full OpenAI-compatible chat/completions endpoint."""
    return f"{compat_base_url()}/chat/completions"


def has_oss_url(obj: Any) -> bool:
    """Check whether *obj* contains provider-managed file URLs.

    Backward-compatible alias for ``get_provider().has_managed_url()``.
    The name ``has_oss_url`` is retained for existing consumers; internally
    this delegates to the active provider's ``has_managed_url()`` method.
    """
    return get_provider().has_managed_url(obj)


def build_source_config(script_file: str | None = None) -> str | None:
    """Extract skill/agent from path. Supports .xxx/skills (dot-prefixed) and skills (OpenClaw)."""
    path = script_file
    if not path:
        for frame_info in inspect.stack():
            mod = inspect.getmodule(frame_info.frame)
            if frame_info.filename.endswith('.py') and (mod.__name__ if mod else '') != 'qwencloud_lib':
                path = frame_info.filename
                break
    if not path or not path.endswith('.py'):
        return None

    candidates = [path]
    if sys.argv and sys.argv[0].endswith('.py'):
        argv_path = sys.argv[0]
        candidates.append(argv_path if os.path.isabs(argv_path) else os.path.join(os.getcwd(), argv_path))

    # Match: [/.agent]/skills/skill-name/scripts/xxx.py
    sep = r'[/\\]'
    pattern = sep + r'(?:\.([^/\\]+)' + sep + r')?skills' + sep + r'([^/\\]+)' + sep + r'scripts' + sep + r'[^/\\]+\.py$'
    for candidate in candidates:
        m = re.search(pattern, candidate)
        if m:
            agent, skill = m.group(1) or "default", m.group(2)
            if len(agent) <= 32 and len(skill) <= 32:
                return json.dumps({"channel": "qwencloud-skill", "tags": {"t1": skill, "t2": agent}}, separators=(',', ':'))
    return None


# ---------------------------------------------------------------------------
# Section 6: HTTP infrastructure
# ---------------------------------------------------------------------------

_RETRYABLE_CODES = frozenset({429, 500, 502, 503, 504})


def http_request(
        method: str,
        url: str,
        api_key: str,
        payload: dict[str, Any] | None = None,
        *,
        extra_headers: dict[str, str] | None = None,
        timeout: int = 120,
        retries: int = 2,
        backoff: float = 1.5,
) -> dict[str, Any]:
    """Generic HTTP request with retry and exponential backoff.

    Handles JSON serialisation, provider header injection, and retryable
    HTTP codes.
    """
    hdrs = get_provider().make_headers(api_key, payload)
    if extra_headers:
        hdrs.update(extra_headers)
    data = json.dumps(payload).encode("utf-8") if payload else None
    last_err = ""
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            if api_key and len(api_key) > 8 and api_key in body:
                body = body.replace(api_key, mask_key(api_key))
            last_err = f"HTTP {exc.code}: {sanitize_diagnostic(body)[:500]}"
            if exc.code not in _RETRYABLE_CODES or attempt >= retries:
                if exc.code == 401 and is_token_plan_key(api_key):
                    print(
                        "Hint: if this model is not on Token Plan, see supported "
                        "models at https://docs.qwencloud.com/token-plan",
                        file=sys.stderr,
                    )
                raise RuntimeError(last_err) from None
            time.sleep(backoff * (2 ** attempt))
        except urllib.error.URLError as exc:
            last_err = sanitize_diagnostic(str(exc.reason))
            if attempt >= retries:
                raise RuntimeError(f"Network error: {last_err}") from None
            time.sleep(backoff * (2 ** attempt))
    raise RuntimeError(last_err)


def http_post(
        url: str,
        api_key: str,
        payload: dict[str, Any],
        *,
        timeout: int = 120,
        retries: int = 2,
        backoff: float = 1.5,
) -> dict[str, Any]:
    """Convenience: non-streaming POST, returns parsed JSON."""
    return http_request(
        "POST", url, api_key, payload,
        timeout=timeout, retries=retries, backoff=backoff,
    )


def _sse_error_message(
        chunk: Any,
        event_type: str,
        api_key: str,
) -> Optional[str]:
    """Return a safe error message for an SSE error payload, if present."""
    error_payload = chunk.get("error") if isinstance(chunk, dict) else None
    has_top_level_error = isinstance(chunk, dict) and (
        not chunk.get("choices")
        and chunk.get("code") is not None
        and chunk.get("message") is not None
    )
    if event_type.lower() != "error" and error_payload is None and not has_top_level_error:
        return None

    payload = error_payload if error_payload is not None else chunk
    if isinstance(payload, dict):
        code = payload.get("code") or payload.get("type")
        message = payload.get("message")
        if code and message:
            detail = f"{code}: {message}"
        elif code or message:
            detail = str(code or message)
        else:
            detail = json.dumps(payload, ensure_ascii=False)
    else:
        detail = str(payload)

    if api_key and len(api_key) > 8 and api_key in detail:
        detail = detail.replace(api_key, mask_key(api_key))
    return f"SSE error: {sanitize_diagnostic(detail)[:500]}"


def stream_sse(
        url: str,
        api_key: str,
        payload: dict[str, Any],
        *,
        timeout: int = 180,
) -> Iterator[dict[str, Any]]:
    """Streaming POST.  Yields parsed SSE ``data:`` chunks.

    Automatically sets ``stream: true`` in the payload and sends the
    appropriate ``Accept`` header.
    """
    payload["stream"] = True
    hdrs = get_provider().make_headers(api_key, payload)
    hdrs["Accept"] = "text/event-stream"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=hdrs, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        if api_key and len(api_key) > 8 and api_key in body:
            body = body.replace(api_key, mask_key(api_key))
        raise RuntimeError(f"HTTP {exc.code}: {sanitize_diagnostic(body)[:500]}") from None
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {sanitize_diagnostic(str(exc.reason))}") from None

    buf = b""
    event_type = ""
    try:
        while True:
            raw = resp.read(4096)
            if not raw:
                break
            buf += raw
            while b"\n" in buf:
                line_bytes, buf = buf.split(b"\n", 1)
                line = line_bytes.decode("utf-8", errors="replace").strip()
                if not line:
                    event_type = ""
                    continue
                if line.startswith("event:"):
                    event_type = line[6:].strip()
                    continue
                if not line.startswith("data:"):
                    continue
                json_str = line[5:].strip()
                if json_str == "[DONE]":
                    return
                try:
                    chunk = json.loads(json_str)
                except json.JSONDecodeError:
                    if event_type.lower() == "error":
                        detail = json_str
                        if api_key and len(api_key) > 8 and api_key in detail:
                            detail = detail.replace(api_key, mask_key(api_key))
                        detail = sanitize_diagnostic(detail)[:500]
                        raise RuntimeError(f"SSE error: {detail}") from None
                    pass
                else:
                    error_message = _sse_error_message(chunk, event_type, api_key)
                    if error_message:
                        raise RuntimeError(error_message)
                    yield chunk
                event_type = ""
    finally:
        resp.close()


# ---------------------------------------------------------------------------
# Section 7: File upload / download
# ---------------------------------------------------------------------------

_BASE64_FILE_LIMIT = 7 * 1024 * 1024  # 7 MB (base64 adds ~33%; API limit is 10 MB)


def upload_local_file(api_key: str, model: str, fp: Path) -> str:
    """Upload a local file to the active provider's temp storage.

    Returns a provider-managed URL (e.g. ``oss://`` for DashScope).
    """
    return get_provider().upload_file(api_key, model, fp)


def resolve_file(
        value: str,
        *,
        api_key: str | None = None,
        model: str | None = None,
) -> str:
    """Resolve a file reference for API consumption.

    URLs (``http``, ``https``, ``data``, and provider-managed schemes)
    pass through unchanged.  Local files are handled based on context:

    - *api_key* + *model* provided: upload to temp storage.
    - Otherwise: convert to ``data:`` base64 URI (must be < 7 MB).
    """
    provider = get_provider()
    pass_through = ("http://", "https://", "data:") + provider.managed_url_schemes()
    if value.startswith(pass_through):
        return value
    if value.startswith("file://"):
        parsed = urllib.parse.urlparse(value)
        if parsed.netloc and parsed.netloc.lower() != "localhost":
            raise ValueError(
                f"Cannot resolve non-local file URI authority {parsed.netloc!r}; "
                "only an empty authority or 'localhost' is supported."
            )
        value = urllib.request.url2pathname(parsed.path)
    p = Path(value)
    if not (p.exists() and p.is_file()):
        return value

    file_size = p.stat().st_size

    if api_key and model:
        managed_url = provider.upload_file(api_key, model, p)
        tag = "48 h TTL" if managed_url.startswith("oss://") else "custom OSS"
        print(sanitize_diagnostic(f"Uploaded {p.name} -> {managed_url} ({tag})"), file=sys.stderr)
        return managed_url

    if file_size > _BASE64_FILE_LIMIT:
        print(
            f"Warning: {p.name} is {file_size / 1024 / 1024:.1f} MB -- "
            "base64 may exceed the 10 MB API limit. "
            "Use --upload-files to auto-upload, or provide an online URL.",
            file=sys.stderr,
        )

    mime = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def download_file(url: str, dest: Path, *, timeout: int = 120) -> Path:
    """Download a file from *url* to *dest*, creating parent dirs as needed."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "qwencloud-skills"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            dest.write_bytes(resp.read())
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Download failed: {sanitize_diagnostic(str(exc))}") from None
    return dest


# ---------------------------------------------------------------------------
# Section 8: Request / response utilities
# ---------------------------------------------------------------------------

def load_request(args: Any) -> dict[str, Any]:
    """Load request dict from ``--request`` or ``--file`` CLI argument."""
    if getattr(args, "request", None):
        return json.loads(args.request)
    if getattr(args, "file", None):
        return json.loads(Path(args.file).read_text(encoding="utf-8"))
    raise ValueError("Provide --request '{...}' or --file path/to/request.json")


def save_result(result: dict[str, Any], output_path: str | Path) -> None:
    """Write *result* as JSON to *output_path*, creating parent dirs."""
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def extract_text(content: Any) -> str:
    """Extract plain text from a message ``content`` field.

    Handles ``str``, ``list[{type, text}]``, and ``None``.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str):
                    return text
        return json.dumps(content, ensure_ascii=False)
    if content is None:
        return ""
    return json.dumps(content, ensure_ascii=False)


def try_parse_json(text: str) -> Any | None:
    """Attempt to parse *text* as JSON; return ``None`` on failure."""
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Section 9: Async task polling
# ---------------------------------------------------------------------------

def poll_task(
        task_id: str,
        api_key: str,
        *,
        timeout_s: int = 600,
        interval: int = 10,
        verbose: bool = True,
) -> dict[str, Any]:
    """Poll an async task until it reaches a terminal state.

    Returns the final result dict.  Raises ``TimeoutError`` if
    *timeout_s* is exceeded.
    """
    provider = get_provider()
    url = provider.task_poll_url(task_id)
    terminals = provider.terminal_statuses()
    start = time.time()
    poll_count = 0
    while True:
        result = http_request("GET", url, api_key)
        elapsed = int(time.time() - start)
        poll_count += 1
        status = provider.extract_task_status(result)
        if verbose:
            print(f"  [{elapsed}s] task={task_id} status={status}", file=sys.stderr)
        if status in terminals:
            return result
        if time.time() - start > timeout_s:
            raise TimeoutError(
                f"Task {task_id} timed out after {timeout_s}s "
                f"({poll_count} polls, last status: {status})"
            )
        time.sleep(interval)


# ---------------------------------------------------------------------------
# Section 10: Update-check signal
# ---------------------------------------------------------------------------

try:
    from gossamer import run as _run_update_signal_impl
except ImportError:
    _run_update_signal_impl = None  # type: ignore[assignment]


def run_update_signal(caller: str | Path | None = None) -> None:
    """Emit update-check signals to stderr (non-blocking, failure-safe).

    Parameters
    ----------
    caller : str or Path, optional
        ``__file__`` of the calling script.
    """
    if _run_update_signal_impl:
        try:
            _run_update_signal_impl(caller=caller or __file__)
        except Exception:
            pass
