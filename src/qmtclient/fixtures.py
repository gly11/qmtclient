from __future__ import annotations

import json
from collections.abc import Iterator
from copy import deepcopy
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def load_jsonl(path: str | Path) -> list[Any]:
    items: list[Any] = []
    with Path(path).open("r", encoding="utf-8-sig") as file:
        for line in file:
            stripped = line.strip()
            if stripped:
                items.append(json.loads(stripped))
    return items


def load_fixture(path: str | Path) -> dict[str, Any]:
    fixture = load_json(path)
    if isinstance(fixture, dict):
        return fixture
    raise TypeError("fixture JSON root must be an object")


class EventReplay:
    def __init__(
        self,
        events: list[dict[str, Any]],
        *,
        types: list[str] | tuple[str, ...] | None = None,
    ) -> None:
        self._events = deepcopy(events)
        self._types = set(types or [])

    def __iter__(self) -> Iterator[dict[str, Any]]:
        for event in self._events:
            event_type = event.get("type")
            if self._types and event_type != "heartbeat" and event_type not in self._types:
                continue
            yield deepcopy(event)
