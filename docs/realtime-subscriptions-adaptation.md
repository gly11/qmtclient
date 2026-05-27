# qmtserver 0.5.0 实时行情订阅适配计划

qmtserver `0.5.0` 准备提供稳定实时行情订阅 endpoints，并通过 WebSocket 推送
`market_subscription` 和 `market_quote` 事件。qmtclient 应适配这些只读能力，让策略机不安装
MiniQMT 和 `xtquant` 也能订阅远程行情。

## 服务端契约

```text
POST /v1/market/subscriptions
GET /v1/market/subscriptions
GET /v1/market/subscriptions/{subscription_id}
DELETE /v1/market/subscriptions/{subscription_id}
WS /v1/ws/events?types=market_subscription,market_quote
```

创建请求：

```python
{
    "symbols": ["000001.SZ"],
    "period": "tick",
}
```

订阅响应使用 `market.subscription.v1`：

```python
{
    "schema": "market.subscription.v1",
    "subscription_id": "sub_...",
    "symbols": ["000001.SZ"],
    "period": "tick",
    "status": "active",
    "created_at": "2026-05-27T09:30:00+00:00",
    "updated_at": "2026-05-27T09:30:00+00:00",
    "upstream_id": [1],
    "last_error": None,
}
```

实时行情事件使用 `market.quote.v1`：

```python
{
    "type": "market_quote",
    "data": {
        "schema": "market.quote.v1",
        "symbol": "000001.SZ",
        "time": "2026-05-27T09:30:01+08:00",
        "last_price": 10.25,
        "volume": 1200,
        "amount": 12300.0,
        "extra": {},
    },
    "meta": {
        "source": "xtdata",
        "subscription_id": "sub_...",
        "quote_source": "initial",
    },
}
```

`quote_source` 为 `initial` 表示 qmtserver 的初始快照种子，为 `callback` 表示 live
`subscribe_quote` 回调。

## qmtclient 目标

- `client.market` 增加订阅生命周期方法。
- `client.events(types=["market_quote"])` 继续作为行情事件入口。
- `FakeQmtClient` 支持订阅状态和 `market_quote` fixture。
- CLI 增加只读订阅冒烟检查，不提供交易快捷入口。
- 错误继续映射为 `QmtRpcError`，保留服务端 `error.code`。

## API 设计

`client.market` 增加：

```python
subscription = client.market.create_subscription(["000001.SZ"], period="tick")
subscriptions = client.market.subscriptions()
subscription = client.market.subscription("sub_example")
stopped = client.market.stop_subscription("sub_example")
```

事件仍使用现有 WebSocket 入口：

```python
for event in client.events(types=["market_subscription", "market_quote"]):
    print(event)
```

第一版不新增专门的异步框架、不引入 GUI、不直接连接 MiniQMT。

## 测试计划

- `QmtClient` 调用 create/list/get/delete endpoint，并解析 named response。
- `client.market` facade 暴露订阅生命周期方法。
- `ok=False` 映射为 `QmtRpcError`，覆盖 `INVALID_SUBSCRIPTION_REQUEST`、
  `TARGET_NOT_CONNECTED`、`MARKET_SUBSCRIPTION_NOT_FOUND`。
- `EventStream` 能过滤 `market_subscription`、`market_quote` 类型。
- `FakeQmtClient` 支持订阅状态和事件回放。
- CLI 订阅 smoke 使用 fake client 和 fake WebSocket，不依赖真实 qmtserver。

## CLI 规划

新增只读诊断命令：

```powershell
qmtclient market-subscribe-check --symbol 000001.SZ --wait-seconds 10
```

行为：

1. 创建订阅。
2. 等待 `market_quote` 或 `market_subscription` 事件。
3. 尝试停止订阅。
4. 输出 JSON-friendly 诊断结果。

命令不得下单、撤单、转账，也不得保存 token。

## 文档计划

- `docs/compatibility.md` 增加 `/v1/market/subscriptions` 支持范围和 schema。
- `docs/strategy.md` 增加实时行情订阅示例。
- `docs/cli.md` 增加订阅 smoke 命令。
- `docs/offline-testing.md` 增加 `market_quote` 事件回放示例。
- `CHANGELOG.md` 在下一版本记录 qmtserver `0.5.0` 适配。

## 发布建议

建议作为 qmtclient `0.5.0` 主线。该能力是只读行情能力，适合优先推进；交易相关能力继续由
qmtserver 的配置、保护和审计控制。
