from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid
import time

class TaskEnvelope(BaseModel):
    task_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: float = Field(default_factory=time.time)
    source: str
    task: str
    mode_hint: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
