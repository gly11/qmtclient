# 兼容性说明

本文从 qmtclient 视角说明 qmtclient 与 qmtserver 的兼容关系。

## 版本矩阵

| qmtclient | qmtserver API | 状态 | 说明 |
| --- | --- | --- | --- |
| `0.1.0` | `/v1` | 目标兼容 | 第一个独立客户端版本，覆盖基础 RPC、WebSocket、策略 facade、fake client、fixture 和 event replay。 |

qmtclient `0.1.0` 只承诺兼容 qmtserver 的 `/v1` API。客户端 CI 覆盖 Windows、macOS、Linux 和 Python 3.10-3.14。旧的无版本路径可能仍由 qmtserver 保留，但 qmtclient 默认使用 `/v1`。

## 支持的 qmtserver `/v1` 能力

基础 HTTP：

- `GET /v1/health`
- `GET /v1/qmt/status`
- `GET /v1/rpc/methods`
- `POST /v1/rpc`
- `GET /v1/orders`
- `GET /v1/orders/{order_id}`
- `GET /v1/trades`
- `GET /v1/events/recent`

WebSocket：

- `WS /v1/ws/events`

客户端 SDK：

- `QmtClient.health()`
- `QmtClient.status()`
- `QmtClient.methods()`
- `QmtClient.rpc(...)`
- `QmtClient.orders(...)`
- `QmtClient.order(...)`
- `QmtClient.trades(...)`
- `QmtClient.recent_events(...)`
- `QmtClient.events(...)`
- `client.xtdata.<method>(...)`
- `client.trader.<method>(...)`
- `client.market`
- `client.account`
- `client.trading`

离线测试：

- `FakeQmtClient`
- `load_json(...)`
- `load_jsonl(...)`
- `load_fixture(...)`
- `EventReplay`

## API 版本前缀

默认情况下：

```python
QmtClient("http://192.168.1.10:8000")
```

会访问：

```text
http://192.168.1.10:8000/v1/...
```

如果网关或反向代理路径已经包含 `/v1`，可以关闭自动前缀：

```python
QmtClient("https://qmt.example.com/qmt/v1", api_version=None)
```

## 兼容性边界

- qmtclient 不兼容直接 MiniQMT 连接。
- qmtclient 不兼容直接 `xtquant` 调用。
- qmtclient 不绕过 qmtserver 的 token、RPC 白名单、透明 RPC 开关或交易保护。
- 交易 facade 只负责组织客户端参数；真实交易是否执行由 qmtserver 决定。
- qmtserver 新增 `/v2` 或破坏 `/v1` 契约时，应先在 qmtclient 文档和测试中新增兼容策略。

## 推荐升级策略

- qmtserver 保持 `/v1` API 稳定时，qmtclient `0.1.x` 应继续兼容。
- qmtserver 新增只读方法时，qmtclient 可以通过 `client.rpc(...)` 或动态代理先行访问。
- qmtserver 新增常用工作流后，qmtclient 再考虑增加 facade 方法。
- qmtserver 改变错误结构、事件结构或交易保护语义时，qmtclient 必须新增测试和文档说明。
