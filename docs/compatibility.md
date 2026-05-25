# 兼容性

| qmtclient | qmtserver API | 说明 |
| --- | --- | --- |
| `0.1.0` | `/v1` | 基础 RPC、WebSocket、策略接口、fake client、fixture、event replay。 |

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
- `WS /v1/ws/events`

SDK 入口：

- `QmtClient`
- `client.xtdata` / `client.trader`
- `client.market` / `client.account` / `client.trading`
- `FakeQmtClient`
- `load_json` / `load_jsonl` / `load_fixture`
- `EventReplay`

## 边界

- 不直连 MiniQMT。
- 不调用或依赖 `xtquant`。
- 不绕过 qmtserver 的 token、RPC 白名单、透明 RPC 开关或交易保护。
- qmtserver 新增 `/v2` 或改变 `/v1` 契约时，qmtclient 需要先补测试和文档。
