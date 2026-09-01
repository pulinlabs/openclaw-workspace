from __future__ import annotations

from pathlib import Path

from .memory import MemoryStore
from .models import ModelRequest, ModelResponse
from .observability import EventLog
from .policy import GatewayPolicy, PolicyViolation


class ModelGateway:
    """Mandatory model access layer for the public workspace sample."""

    def __init__(
        self,
        root: Path,
        policy: GatewayPolicy | None = None,
        memory: MemoryStore | None = None,
        events: EventLog | None = None,
    ) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.policy = policy or GatewayPolicy()
        self.memory = memory or MemoryStore(root / "state" / "memory.sqlite")
        self.events = events or EventLog(root / "logs" / "gateway.jsonl")

    def complete(self, request: ModelRequest) -> ModelResponse:
        estimated_cost = self._estimate_cost(request)
        self.events.append(
            "model.request.received",
            {
                "request_id": request.request_id,
                "agent_id": request.agent_id,
                "model": request.model,
                "dry_run": request.dry_run,
                "estimated_cost_usd": estimated_cost,
            },
        )

        try:
            self.policy.validate(request, estimated_cost)
        except PolicyViolation as exc:
            self.events.append(
                "model.request.blocked",
                {
                    "request_id": request.request_id,
                    "agent_id": request.agent_id,
                    "model": request.model,
                    "reason": str(exc),
                },
            )
            raise

        response = self._dry_run_response(request, estimated_cost)
        self.events.append(
            "model.response.completed",
            {
                "request_id": response.request_id,
                "provider_request_id": response.provider_request_id,
                "actual_cost_usd": response.actual_cost_usd,
                "dry_run": response.dry_run,
            },
        )
        self.memory.put(
            "model_calls",
            request.request_id,
            {
                "agent_id": request.agent_id,
                "model": request.model,
                "dry_run": request.dry_run,
                "estimated_cost_usd": estimated_cost,
                "actual_cost_usd": response.actual_cost_usd,
            },
        )
        return response

    def _estimate_cost(self, request: ModelRequest) -> float:
        if request.dry_run or request.model == "dry-run/local":
            return 0.0
        return max(0.001, len(request.prompt.split()) * 0.00001)

    def _dry_run_response(self, request: ModelRequest, estimated_cost: float) -> ModelResponse:
        summary = " ".join(request.prompt.split())[:160]
        return ModelResponse(
            request_id=request.request_id,
            provider_request_id=f"dry-run-{request.request_id}",
            model=request.model,
            content=f"[dry-run] {request.agent_id}: {summary}",
            estimated_cost_usd=estimated_cost,
            actual_cost_usd=0.0,
            dry_run=True,
        )
