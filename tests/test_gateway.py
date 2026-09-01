from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openclaw_workspace.gateway import ModelGateway
from openclaw_workspace.memory import MemoryStore
from openclaw_workspace.models import ModelRequest
from openclaw_workspace.observability import recovery_report
from openclaw_workspace.policy import GatewayPolicy, PolicyViolation


class GatewayTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_dry_run_model_call_goes_through_gateway(self) -> None:
        gateway = ModelGateway(self.root)
        request = ModelRequest(agent_id="developer", model="dry-run/local", prompt="build a safe runtime")

        response = gateway.complete(request)

        self.assertTrue(response.dry_run)
        self.assertEqual(response.actual_cost_usd, 0.0)
        self.assertIn("build a safe runtime", response.content)
        self.assertEqual(gateway.memory.get("model_calls", request.request_id)["agent_id"], "developer")

        event_types = [event.event_type for event in gateway.events.read()]
        self.assertEqual(
            event_types,
            ["model.request.received", "model.response.completed"],
        )

    def test_policy_blocks_disallowed_model(self) -> None:
        gateway = ModelGateway(self.root)
        request = ModelRequest(agent_id="developer", model="unapproved/model", prompt="hello")

        with self.assertRaises(PolicyViolation):
            gateway.complete(request)

        report = recovery_report(gateway.events.read())
        self.assertEqual(report["blocked_count"], 1)
        self.assertEqual(report["blocked_request_ids"], [request.request_id])

    def test_policy_blocks_live_calls_by_default(self) -> None:
        gateway = ModelGateway(self.root)
        request = ModelRequest(
            agent_id="developer",
            model="openrouter/anthropic/claude-sonnet-4-6",
            prompt="live call should not run",
            dry_run=False,
            approval_id="approval-123",
        )

        with self.assertRaises(PolicyViolation):
            gateway.complete(request)

    def test_memory_store_searches_side_state(self) -> None:
        store = MemoryStore(self.root / "state" / "memory.sqlite")
        store.put("decisions", "gateway", {"summary": "all model calls route through gateway"})

        results = store.search("gateway")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["namespace"], "decisions")

    def test_live_policy_can_be_enabled_with_approval(self) -> None:
        policy = GatewayPolicy(require_dry_run=False)
        gateway = ModelGateway(self.root, policy=policy)
        request = ModelRequest(
            agent_id="developer",
            model="openrouter/anthropic/claude-sonnet-4-6",
            prompt="approved live-shaped request",
            dry_run=False,
            approval_id="approval-123",
        )

        response = gateway.complete(request)

        self.assertTrue(response.dry_run)
        self.assertEqual(response.actual_cost_usd, 0.0)


if __name__ == "__main__":
    unittest.main()
