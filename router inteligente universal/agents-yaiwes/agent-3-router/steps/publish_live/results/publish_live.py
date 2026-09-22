```python
"""publish_live: Job Router en maquina 32 GB RAM + Space estatico riu-chat-yaiwes."""
from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import requests
from huggingface_hub import HfApi, whoami

PORT = 8000
SPACE_SUFFIX = "riu-chat-yaiwes"
# Id tecnico HF Jobs que mapea a 32 GB RAM (detalle de implementacion; requisito =
