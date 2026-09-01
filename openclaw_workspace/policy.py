from __future__ import annotations

from dataclasses import dataclass, field

from .models import ModelRequest


class PolicyViolation(RuntimeError):
    """Raised when a model request violates the gateway policy."""


@dataclass(frozen=True)
class GatewayPolicy:
    allowed_models: set[str] = field(
        default_factory=lambda: {
            "dry-run/local",
            "openrouter/anthropic/claude-sonnet-4-6",
            "openrouter/anthropic/claude-opus-4-7",
            "openrouter/openai/gpt-4o",
        }
    )
    max_cost_usd_per_request: float = 0.05
    require_dry_run: bool = True
    require_approval_for_live: bool = True
    schedules_enabled: bool = False

    def validate(self, request: ModelRequest, estimated_cost_usd: float) -> None:
        if request.model not in self.allowed_models:
            raise PolicyViolation(f"model is not allowed: {request.model}")

        if estimated_cost_usd > self.max_cost_usd_per_request:
            raise PolicyViolation(
                f"estimated cost {estimated_cost_usd:.4f} exceeds cap "
                f"{self.max_cost_usd_per_request:.4f}"
            )

        if self.require_dry_run and not request.dry_run:
            raise PolicyViolation("live provider calls are disabled by policy")

        if self.require_approval_for_live and not request.dry_run and not request.approval_id:
            raise PolicyViolation("live provider calls require an approval_id")
