# OpenClaw Workspace

OpenClaw Workspace is a public-safe reference implementation of a governed agent runtime.

The gateway is the choke point — every model-shaped call goes through it. Memory and state sit alongside as a side store that agents read from and write to through approved runtime APIs. Observability records runtime events and feeds the recovery loop.

This repo captures the architecture and lessons from a longer-running private system. It's designed to be inspected, run offline, and extended.

---

## Architecture at a Glance

```text
                    ┌─────────────────────┐
                    │   User / Interface  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │     Strategist      │
                    │   (Orchestrator)    │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
        ┌─────▼─────┐   ┌──────▼─────┐   ┌──────▼─────┐
        │ Specialist│   │ Specialist │   │ Specialist │
        │  Agents   │   │  Agents    │   │  Agents    │
        └─────┬─────┘   └──────┬─────┘   └──────┬─────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Gateway / Policy  │◄──── Budgets, caps,
                    │   Enforcement       │      approvals, audit
                    └──────────┬──────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
          ┌─────▼─────┐  ┌─────▼─────┐  ┌────▼─────┐
          │ Dry-Run   │  │ Approved  │  │ Memory + │
          │ Response  │  │ Live Call │  │  State   │
          └───────────┘  └───────────┘  └────┬─────┘
                                             │
                                  ┌──────────┴──────────┐
                                  │  SQLite + JSONL     │
                                  │  Event Log          │
                                  └─────────────────────┘

         Observability and recovery loops feed back into
         orchestration and tighten policies over time.
```

The gateway sits at the center. Memory and state sit alongside as a side store. Observability runs continuously and feeds the recovery loop back into orchestration.

---

## Current Repo Status

This repository includes a small offline Python implementation of the core architecture:

- Gateway-first model access
- Dry-run model responses by default
- Policy checks for model allowlists, cost caps, approvals, and live-call blocking
- SQLite memory/state side store
- Append-only JSONL observability events
- Recovery report generation from blocked events
- Unit tests for the gateway, policy, memory, and observability loop

It does not include private local OpenClaw state, credentials, provider logs, tokens, deployment state, or historical project reports. The public implementation deliberately avoids live provider calls so the architecture can be inspected and tested without API keys or risk of accidental spend.

---

## Why This Exists

This project started with a simple idea:

> What if you could give a system a product idea or set of requirements, and have it build, operate, monitor, and improve the product end-to-end?

The original goal was not to build AI demos. It was to explore whether agents could take a product requirement, coordinate work across tools and models, generate implementation, monitor metrics, identify problems, and continuously improve over time.

The deeper the project went, the more it evolved. The hardest problems were not code generation. They were governance, orchestration, observability, cost control, runtime reliability, memory, and safe autonomy.

What emerged was less of an "agent project" and more of an operational architecture for governed autonomous systems.

---

## Core Thesis

The biggest lesson from this project:

> Building agents is not just about getting them to act. It is about designing systems that allow them to act safely, visibly, continuously, and within limits.

The system evolved from a loosely connected multi-agent environment into a governed runtime built around gateway-based model access, dry-run defaults, staged promotion gates, operational memory, explicit approvals, billing reconciliation, policy enforcement, runtime observability, and durable state.

The result is a system designed to improve operationally while remaining auditable and controllable.

---

## Key Lessons

### 1. Autonomy Needs a Choke Point

The most important architectural decision was forcing all model activity through a single gateway. Without a centralized control layer, cost governance breaks down, approvals become bypassable, audit logs go incomplete, and observability fragments across providers.

The gateway became the foundation for every other governance mechanism in the system.

### 2. "Self-Healing" Starts With Observability

The system does not magically repair itself. It becomes more resilient by observing failures, logging runtime behavior, identifying blocked work, proposing fixes, validating outcomes, and tightening policies over time.

Visibility turned out to matter more than raw autonomy.

### 3. "Self-Learning" Is Operational, Not Model Training

This runtime does not autonomously retrain models. The learning loop is operational — gateway logs, verifier reports, runtime evidence, billing reconciliation, memory retrieval, execution outcomes, and accumulated project history.

The system gets better because it preserves decisions, failures, proof artifacts, costs, and governance boundaries in durable memory.

### 4. Cost Governance Must Be Designed In

Agent systems can become expensive surprisingly fast. The architecture includes dry-run defaults, gateway-only provider access, model tiering, per-request cost caps, daily and monthly budgets, billing reconciliation, request tracing, promotion gates, static scans for hidden provider calls, and disabled schedules unless explicitly approved.

The goal is not to monitor costs after they happen. The goal is to structurally prevent uncontrolled spend.

### 5. Real-World Agents Need Memory

Most AI systems rely heavily on short conversational context windows. That works for demos and breaks down quickly for long-running operational systems.

This project evolved toward persistent, externalized memory. Agents don't rely solely on prompts or transient chat history. Important context is written into durable memory that future sessions can retrieve, inspect, and build on.

---

## Components

### Gateway

The mandatory model access layer. `ModelGateway` accepts a `ModelRequest`, estimates cost, validates policy, emits observability events, writes call metadata to memory, and returns a dry-run `ModelResponse`.

The public implementation intentionally avoids live provider calls, giving the architecture a testable shape without requiring API keys or risking accidental spend.

### Policy

`GatewayPolicy` enforces:

- Allowed models
- Per-request cost cap
- Dry-run requirement
- Approval requirement for live-shaped requests
- Disabled schedules by default

Blocked requests are logged as observability events and can be summarized by the recovery report.

### Memory

`MemoryStore` is a lightweight SQLite side store for durable runtime memory. It supports namespaced writes, reads, and simple search. The goal is to externalize operational state rather than relying only on short conversation context.

### Observability

`EventLog` writes append-only JSONL events. The gateway records request receipt, blocked requests, and completed responses. The recovery loop reads these events and summarizes blocked work with recommended next actions.

---

## Multi-Agent Roles

The broader OpenClaw workspace uses specialized agent roles rather than interchangeable general assistants. Each has a defined role, scoped responsibilities, persistent context, runtime state, and structured handoff patterns.

**Strategist** — assigns work, routes tasks, tracks dependencies, escalates blockers, coordinates workflows.

**Developer** — writes code, implements features, fixes bugs, prepares work for review.

**QA** — runs tests, validates outputs, checks regressions, enforces quality gates.

**Research** — external research, summarization, trend identification, contextual enrichment.

**Security** — validates integrations, assesses vulnerabilities, reviews production changes, blocks unsafe actions.

**Integrations** — APIs, authentication, retries, rate limiting, external tooling.

**Triage** — diagnoses failures, identifies blockers, proposes fixes, coordinates recovery flows. Blocked execution paths can trigger repair flows which collaborate with coding agents to generate fixes, then return them to the originating workflow. This created an early form of operational self-healing.

**Operations** — health checks, alerts, warning detection, failure monitoring, runtime observability.

---

## The Feedback Loop

The system improves through operational feedback rather than autonomous retraining:

1. Execute bounded work
2. Record outputs, costs, IDs, and runtime evidence
3. Store conclusions in durable memory
4. Index or search memory for retrieval
5. Use prior evidence to guide future decisions
6. Improve workflows and tighten policies over time

The system becomes more informed because the memory and evidence layers get richer over time.

---

## Setup

Requires Python 3.11 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

Run the tests to confirm the gateway, policy, memory, and observability components are wired correctly:

```bash
python3 -m unittest discover -s tests
```

Initialize a local sample runtime:

```bash
openclaw-workspace --root .runtime init
```

Run a dry model call through the gateway:

```bash
openclaw-workspace --root .runtime dry-run \
  --agent developer \
  --model dry-run/local \
  --prompt "Build a safe gateway-first runtime"
```

Write and search memory:

```bash
openclaw-workspace --root .runtime memory-put \
  --namespace decisions \
  --key gateway \
  --json '{"summary":"all model calls must route through the gateway"}'

openclaw-workspace --root .runtime memory-search gateway
```

Inspect events and recovery state:

```bash
openclaw-workspace --root .runtime events
openclaw-workspace --root .runtime recovery-report
```

---

## What's Next

A few concrete directions:

- **Wiring a build layer into the runtime.** Letting a code-generation tool produce implementations that the governed runtime then executes, monitors, and feeds metrics back to.
- **Backtesting the operational signals.** The system records cost, failure, and recovery data — the next step is closing the loop on whether those signals actually predict which workflows will fail next time.
- **Tightening cost governance further.** Per-agent budget caps, harder enforcement on schedule promotion, and better detection of provider calls that escape the gateway.

The longer-term goal is a continuous build → run → improve loop where the build system creates software, the runtime governs execution, the memory system preserves continuity, and the metrics system drives the next iteration.

---

## Closing Note

This started as a question about whether agents could build software end-to-end. It became an exploration of what it takes to let any autonomous system run continuously without losing control of it. The technical surface is the visible part — the deeper work was figuring out where to put the guardrails, what to remember, and how to make a system that improves operationally rather than drifting.

Issues welcome.

## License

MIT License. See [LICENSE](LICENSE).

## Safety Boundary

Do not commit `.env` files, API keys, tokens, local state, provider logs, QR codes, channel credentials, or private operational reports.

The code in this repo is dry-run first and public-safe by design.
