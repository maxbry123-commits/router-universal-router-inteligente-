"""Vercel entrypoint for the RIU Chat MVP (provisional hosting).

Vercel functions have no persistent disk: the data dir is /tmp (per instance). Provider keys are NOT stored on Vercel:
use the chat's "Claves" tab (BYOK, sent per request) or an environment variable added later. Live provider inference is on.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("RIU_DATA_DIR", "/tmp/riu")
os.environ.setdefault("RIU_CHAT_ALLOW_PROVIDER_LIVE", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from integration.chat_mvp.app import app  # noqa: E402,F401  (Vercel serves the ASGI `app`)
