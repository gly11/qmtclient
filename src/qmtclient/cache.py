from __future__ import annotations

from copy import deepcopy
from typing import Any


class MemoryCache:
    def __init__(self, *, enabled: bool = False) -> None:
        self.enabled = enabled
        self._items: dict[str, Any] = {}

    def get(self, key: str) -> Any:
        if not self.enabled or key not in self._items:
            return None
        return deepcopy(self._items[key])

    def set(self, key: str, value: Any) -> None:
        if not self.enabled:
            return
        self._items[key] = deepcopy(value)

    def clear(self) -> None:
        self._items.clear()

    def info(self) -> dict[str, Any]:
        return {"enabled": self.enabled, "items": len(self._items)}
