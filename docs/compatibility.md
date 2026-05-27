# 兼容性

| qmtclient | qmtserver API | 说明 |
| --- | --- | --- |
| `0.1.0` | `/v1` | 基础 RPC、WebSocket、策略接口、fake client、fixture、event replay。 |
| `0.2.0` | `/v1` | 稳定 market facade、诊断、retry/backoff、WebSocket reconnect、MemoryCache 和转换 helper。 |
| `0.3.0` | `/v1` | 适配 qmtserver `0.3.0` 的稳定 market、history job、snapshot 和 quality/reference endpoints。 |
| `0.4.0` | `/v1` | 新增诊断优先 CLI；适配 qmtserver `0.4.0` 只读交易查询 endpoints。 |
| 下一版本 | `/v1` | 适配 qmtserver `0.5.0` 实时行情订阅 endpoints 和 WebSocket quote events。 |

qmtclient 默认使用 `/v1`。旧的无版本路径不作为客户端兼容目标。

## 支持范围

- `GET /v1/health`
- `GET /v1/qmt/status`
- `GET /v1/rpc/methods`
- `POST /v1/rpc`
- `GET /v1/orders`
- `GET /v1/orders/{order_id}`
- `GET /v1/trades`
- `GET /v1/events/recent`
- `GET /v1/market/capabilities`
- `GET /v1/market/bars/daily`
- `GET /v1/market/bars/intraday`
- `GET /v1/market/bars/daily/quality`
- `GET /v1/reference/instruments`
- 下一版本：`POST /v1/market/subscriptions`
- 下一版本：`GET /v1/market/subscriptions`
- 下一版本：`GET /v1/market/subscriptions/{subscription_id}`
- 下一版本：`DELETE /v1/market/subscriptions/{subscription_id}`
- `GET /v1/trader/account-status`
- `GET /v1/trader/asset`
- `GET /v1/trader/positions`
- `GET /v1/trader/orders`
- `GET /v1/trader/trades`
- `POST /v1/jobs/history-download`
- `GET /v1/jobs/{job_id}`
- `GET /v1/jobs/{job_id}/result`
- `POST /v1/jobs/{job_id}/cancel`
- `POST /v1/snapshots`
- `GET /v1/snapshots`
- `GET /v1/snapshots/{snapshot_id}/manifest`
- `GET /v1/snapshots/{snapshot_id}/quality`
- `WS /v1/ws/events`

SDK 入口：

- `QmtClient`
- `client.xtdata` / `client.trader`
- `client.market` / `client.account` / `client.trading`
- `client.batch`
- `client.snapshots`
- `FakeQmtClient`
- `load_json` / `load_jsonl` / `load_fixture`
- `load_snapshot_manifest`
- `EventReplay`

CLI 覆盖范围：

- `qmtclient check`
- `qmtclient diagnose`
- `qmtclient methods`
- `qmtclient ws-check`
- `qmtclient market-capabilities`
- 下一版本：`qmtclient market-subscribe-check`
- `qmtclient snapshot-verify`
- `qmtclient fixture-check`

## 数据契约

稳定 market facade 使用 `schema_version="qmtclient.market.v1"`。基础 response 为 JSON-friendly 结构：

- `schema_version`: 当前客户端 schema 名称。
- `data`: 规范化后的 list。
- `meta`: `kind`、`codes`、`period` 等客户端上下文。

`daily_bars` 字段：`code`、`date`、`open`、`high`、`low`、`close`、`volume`、`amount`。

`intraday_bars` 字段：`code`、`datetime`、`open`、`high`、`low`、`close`、`volume`、`amount`。

`instruments` 字段：`code`、`name`、`exchange`、`instrument_type`、`status`。

下一版本实时行情订阅使用 qmtserver `schema="market.subscription.v1"` 和
`schema="market.quote.v1"`。qmtclient 通过 `client.market` 封装订阅生命周期，并继续通过
`client.events(types=["market_quote"])` 接收行情事件。

稳定 trader readonly facade 使用 qmtserver `schema="trader.readonly.v1"`。qmtclient
按 named data 提取 JSON-friendly 基础类型：

- `trader_account_status()` / `client.account.status()`: `data.statuses`
- `trader_asset()` / `client.account.asset()`: `data.asset`
- `trader_positions()` / `client.account.positions()`: `data.positions`
- `trader_orders()` / `client.account.orders()`: `data.orders`
- `trader_trades()` / `client.account.trades()`: `data.trades`

如果 qmtserver 返回 `ok=False`，qmtclient 抛出 `QmtRpcError` 并保留服务端
`error.code`、`error.message` 和 `meta.request_id`。

诊断结果使用 `schema_version="qmtclient.diagnose.v1"`。`load_snapshot_manifest()` 支持旧
`schema_version="qmtclient.snapshot.v1"` 文件列表，也支持 qmtserver `0.3.0` 的
`schema="market.bars.v1"` CSV manifest，并校验 `hash` 与 `row_count`。

## 错误分类

- `QmtAuthError`: token 或认证失败。
- `QmtServerUnavailableError`: qmtserver 临时不可用，例如 502、503、504。
- `QmtDataEmptyError`: 服务端成功响应但稳定数据为空。
- `QmtSchemaMismatchError`: 返回字段、manifest 或 schema 与客户端契约不匹配。
- `QmtOptionalDependencyError`: 显式转换工具缺少可选依赖。

默认测试必须使用 mock、fake 或 fixture；真实 qmtserver 冒烟检查是可选手动验证。

## 边界

- 不直连 MiniQMT。
- 不调用或依赖 `xtquant`。
- 不绕过 qmtserver 的 token、RPC 白名单、透明 RPC 开关或交易保护。
- qmtserver 新增 `/v2` 或改变 `/v1` 契约时，qmtclient 需要先补测试和文档。
