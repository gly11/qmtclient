# 更新日志

## Unreleased

- 适配 qmtserver `0.3.0` pre-release：`client.market` 优先使用稳定
  `/v1/market` 与 `/v1/reference` endpoints。
- `client.batch` 适配 `/v1/jobs/history-download` 和 job result manifest。
- 新增 `client.snapshots`，封装 snapshot create/list/manifest/quality。
- `load_snapshot_manifest()` 支持 qmtserver `0.3.0` CSV manifest 的 hash 和 row count 校验。
- 更新 `FakeQmtClient`、契约测试和相关文档。

## 0.2.0

- 稳定 market facade：新增 `daily_bars`、`intraday_bars`、`instruments`。
- 新增 typed response helpers、market/diagnose/snapshot schema version 和稳定错误类型。
- 新增 `FakeQmtClient` 标准 market fixture 支持和 daily/intraday/empty/error 示例。
- 新增 `diagnose()`、`check_compatibility()`、`client.batch` 和 snapshot manifest 校验工具。
- 新增有限 retry/backoff、WebSocket reconnect、`MemoryCache`、Pandas/Arrow 显式转换 helper。
- 更新 roadmap、兼容性、连接、策略、离线测试和数据工具文档。

## 0.1.0

- 独立 `qmtclient` 包，兼容 qmtserver `/v1`。
- `QmtClient`：HTTP RPC、状态查询、订单/成交缓存、WebSocket 事件。
- 动态 RPC：`client.xtdata.<method>(...)`、`client.trader.<method>(...)`。
- 类型化异常：连接、认证、HTTP、协议、RPC。
- 策略接口：`client.market`、`client.account`、`client.trading`。
- 离线测试：`FakeQmtClient`、JSON/JSONL fixture、`EventReplay`。
- 示例：远程连接、策略接口、离线策略。
- typed package：`qmtclient/py.typed`。
