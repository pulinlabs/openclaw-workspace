from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .models import utc_now


class MemoryStore:
    """Small durable side store for agent memory and runtime state."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                create table if not exists memory_entries (
                    namespace text not null,
                    key text not null,
                    value_json text not null,
                    created_at text not null,
                    updated_at text not null,
                    primary key (namespace, key)
                )
                """
            )

    def put(self, namespace: str, key: str, value: dict[str, Any]) -> None:
        now = utc_now()
        with self._connect() as connection:
            connection.execute(
                """
                insert into memory_entries (namespace, key, value_json, created_at, updated_at)
                values (?, ?, ?, ?, ?)
                on conflict(namespace, key) do update set
                    value_json = excluded.value_json,
                    updated_at = excluded.updated_at
                """,
                (namespace, key, json.dumps(value, sort_keys=True), now, now),
            )

    def get(self, namespace: str, key: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "select value_json from memory_entries where namespace = ? and key = ?",
                (namespace, key),
            ).fetchone()
        return json.loads(row["value_json"]) if row else None

    def search(self, query: str, namespace: str | None = None) -> list[dict[str, Any]]:
        like = f"%{query}%"
        sql = "select * from memory_entries where value_json like ? or key like ?"
        args: list[Any] = [like, like]
        if namespace:
            sql += " and namespace = ?"
            args.append(namespace)
        sql += " order by updated_at desc"

        with self._connect() as connection:
            rows = connection.execute(sql, args).fetchall()

        return [
            {
                "namespace": row["namespace"],
                "key": row["key"],
                "value": json.loads(row["value_json"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]
