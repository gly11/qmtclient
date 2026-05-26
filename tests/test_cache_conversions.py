from __future__ import annotations

import unittest

from qmtclient import MemoryCache, QmtOptionalDependencyError, market_to_arrow, market_to_dataframe


class CacheAndConversionTests(unittest.TestCase):
    def test_memory_cache_is_explicit_and_records_hits(self) -> None:
        cache = MemoryCache(enabled=True)

        self.assertFalse(cache.enabled is False)
        self.assertIsNone(cache.get("daily:000001.SZ"))

        cache.set("daily:000001.SZ", {"rows": 1})

        self.assertEqual(cache.get("daily:000001.SZ"), {"rows": 1})
        self.assertEqual(cache.info()["items"], 1)

    def test_disabled_memory_cache_does_not_store(self) -> None:
        cache = MemoryCache()

        cache.set("key", {"value": 1})

        self.assertIsNone(cache.get("key"))
        self.assertFalse(cache.info()["enabled"])

    def test_dataframe_conversion_uses_optional_dependency(self) -> None:
        response = {"schema_version": "qmtclient.market.v1", "data": [{"code": "000001.SZ"}]}

        try:
            frame = market_to_dataframe(response)
        except QmtOptionalDependencyError as exc:
            self.assertEqual(exc.dependency, "pandas")
        else:
            self.assertEqual(list(frame["code"]), ["000001.SZ"])

    def test_arrow_conversion_uses_optional_dependency(self) -> None:
        response = {"schema_version": "qmtclient.market.v1", "data": [{"code": "000001.SZ"}]}

        try:
            table = market_to_arrow(response)
        except QmtOptionalDependencyError as exc:
            self.assertEqual(exc.dependency, "pyarrow")
        else:
            self.assertEqual(table.num_rows, 1)


if __name__ == "__main__":
    unittest.main()
