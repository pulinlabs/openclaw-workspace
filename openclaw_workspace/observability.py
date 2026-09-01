from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import RuntimeEvent


class EventLog:
    """Append-only JSONL event log used for audit and recovery loops."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event_type: str, payload: dict) -> RuntimeEvent:
        event = RuntimeEvent(event_type=event_type, payload=payload)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.__dict__, sort_keys=True) + "\n")
        return event

    def read(self) -> list[RuntimeEvent]:
        if not self.path.exists():
            return []

        events: list[RuntimeEvent] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                events.append(RuntimeEvent(**payload))
        return events

    def failures(self) -> list[RuntimeEvent]:
        return [event for event in self.read() if event.event_type.endswith(".blocked")]


def recovery_report(events: Iterable[RuntimeEvent]) -> dict:
    blocked = [event for event in events if event.event_type.endswith(".blocked")]
    return {
        "blocked_count": len(blocked),
        "blocked_request_ids": [
            event.payload.get("request_id") for event in blocked if event.payload.get("request_id")
        ],
        "recommended_action": (
            "inspect blocked events, adjust policy only with approval, or rerun in dry-run mode"
            if blocked
            else "no recovery action needed"
        ),
    }
