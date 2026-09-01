from __future__ import annotations

import argparse
import json
from pathlib import Path

from .gateway import ModelGateway
from .memory import MemoryStore
from .models import ModelRequest
from .observability import EventLog, recovery_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openclaw-workspace")
    parser.add_argument("--root", type=Path, default=Path(".openclaw-workspace"))
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Create local runtime folders")

    dry_run = subparsers.add_parser("dry-run", help="Run a dry model call through the gateway")
    dry_run.add_argument("--agent", default="developer")
    dry_run.add_argument("--model", default="dry-run/local")
    dry_run.add_argument("--prompt", required=True)

    put = subparsers.add_parser("memory-put", help="Write JSON memory")
    put.add_argument("--namespace", required=True)
    put.add_argument("--key", required=True)
    put.add_argument("--json", required=True)

    search = subparsers.add_parser("memory-search", help="Search memory")
    search.add_argument("query")
    search.add_argument("--namespace")

    subparsers.add_parser("events", help="Print event log")
    subparsers.add_parser("recovery-report", help="Summarize blocked events")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    gateway = ModelGateway(args.root)

    if args.command == "init":
        print(json.dumps({"root": str(args.root), "initialized": True}, sort_keys=True))
    elif args.command == "dry-run":
        response = gateway.complete(
            ModelRequest(
                agent_id=args.agent,
                model=args.model,
                prompt=args.prompt,
                dry_run=True,
            )
        )
        print(json.dumps(response.__dict__, sort_keys=True))
    elif args.command == "memory-put":
        store = MemoryStore(args.root / "state" / "memory.sqlite")
        store.put(args.namespace, args.key, json.loads(args.json))
        print(json.dumps({"written": True, "namespace": args.namespace, "key": args.key}, sort_keys=True))
    elif args.command == "memory-search":
        store = MemoryStore(args.root / "state" / "memory.sqlite")
        print(json.dumps(store.search(args.query, args.namespace), sort_keys=True))
    elif args.command == "events":
        events = EventLog(args.root / "logs" / "gateway.jsonl").read()
        print(json.dumps([event.__dict__ for event in events], sort_keys=True))
    elif args.command == "recovery-report":
        events = EventLog(args.root / "logs" / "gateway.jsonl").read()
        print(json.dumps(recovery_report(events), sort_keys=True))
    else:
        parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    main()
