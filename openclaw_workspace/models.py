from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class ModelRequest:
    agent_id: str
    prompt: str
    model: str
    approval_id: str | None = None
    dry_run: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class ModelResponse:
    request_id: str
    provider_request_id: str
    model: str
    content: str
    estimated_cost_usd: float
    actual_cost_usd: float
    dry_run: bool
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class RuntimeEvent:
    event_type: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)
