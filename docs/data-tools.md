# 数据工具

qmtclient 的数据工具只负责客户端封装、校验和显式转换，不改变 qmtserver 作为数据真相源的边界。

## 批量任务

`client.batch` 封装 qmtserver 批量任务接口：

```python
job = client.batch.create_job("market.daily_bars", {"codes": ["000001.SZ"]})
status = client.batch.get_job(job["job_id"])
snapshot = client.batch.download_snapshot(job["job_id"])
```

批量任务依赖 qmtserver 提供稳定 `/v1/batch/jobs` 契约。qmtclient 不定义服务端导出实现，只负责请求组织和返回解析。

## Snapshot manifest

`load_snapshot_manifest()` 读取并校验 qmtserver 导出的 snapshot manifest：

```python
from qmtclient import load_snapshot_manifest

manifest = load_snapshot_manifest("snapshot/manifest.json")
```

manifest 使用 `schema_version="qmtclient.snapshot.v1"`，每个文件条目至少包含：

- `path`
- `sha256`
- `row_count`

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
