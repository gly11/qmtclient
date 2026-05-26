# 数据工具

qmtclient 的数据工具只负责客户端封装、校验和显式转换，不改变 qmtserver 作为数据真相源的边界。

## 批量任务

`client.batch` 封装 qmtserver 批量任务接口：

```python
job = client.batch.create_job(
    "market.daily_bars",
    {"codes": ["000001.SZ"], "start": "2026-01-01", "end": "2026-01-31"},
)
status = client.batch.get_job(job["job_id"])
manifest = client.batch.download_snapshot(job["job_id"])
```

批量任务依赖 qmtserver `0.3.0` 提供的 `/v1/jobs/history-download` 契约。`create_job()`
会把旧参数名 `codes`、`start_time`、`end_time` 映射为 server 使用的 `symbols`、`start`、`end`。
`download_snapshot()` 保留为兼容别名，实际读取 `/v1/jobs/{job_id}/result` 返回的 manifest。

## Snapshot API

`client.snapshots` 封装 qmtserver snapshot registry：

```python
created = client.snapshots.create(
    {
        "kind": "daily_bars",
        "symbols": ["000001.SZ"],
        "start": "2026-01-01",
        "end": "2026-01-31",
        "format": "csv",
    }
)
snapshots = client.snapshots.list()
manifest = client.snapshots.manifest(created["manifest"]["snapshot_id"])
quality = client.snapshots.quality(created["manifest"]["snapshot_id"])
```

## Snapshot manifest

`load_snapshot_manifest()` 读取并校验 qmtserver 导出的 snapshot manifest：

```python
from qmtclient import load_snapshot_manifest

manifest = load_snapshot_manifest("snapshot/manifest.json")
```

`load_snapshot_manifest()` 支持两类 manifest：

- 旧客户端测试格式：`schema_version="qmtclient.snapshot.v1"`，每个文件条目包含 `path`、
  `sha256`、`row_count`。
- qmtserver `0.3.0` CSV manifest：包含 `snapshot_id`、`schema`、`format`、`hash`、
  `row_count` 等字段；校验时会读取同目录下 `{snapshot_id}.{format}`。

hash 或 row count 不匹配时抛出 `QmtSchemaMismatchError`。

## 本地轻量缓存

缓存默认关闭，必须显式启用。它只用于减少重复读取，不作为权威数据源。

```python
from qmtclient import MemoryCache

cache = MemoryCache(enabled=True)
cache.set("daily:000001.SZ", {"rows": 1})
print(cache.get("daily:000001.SZ"))
```

`QmtClient(cache_enabled=True)` 会暴露启用状态的 `client.cache`。

## Pandas / Arrow 转换

转换工具是显式调用，不影响基础 JSON 协议：

```python
from qmtclient import market_to_arrow, market_to_dataframe

response = client.market.daily_bars(["000001.SZ"])
df = market_to_dataframe(response)
table = market_to_arrow(response)
```

`pandas` 和 `pyarrow` 不属于基础依赖。缺少可选依赖时会抛出 `QmtOptionalDependencyError`。
