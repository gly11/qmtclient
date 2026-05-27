# 离线测试

用于没有 qmtserver、MiniQMT 或 `xtquant` 的策略单测。

## FakeQmtClient

```python
from qmtclient import FakeQmtClient

client = FakeQmtClient(
    rpc_results={
        "xtdata.get_full_tick": {"000001.SZ": {"last": 10.5}},
        "trader.query_stock_asset": {"account_id": "example-account", "cash": 1000},
    },
    orders=[{"order_id": "order-1"}],
)

ticks = client.market.get_full_tick(["000001.SZ"])
asset = client.account.asset("example-account")
subscription = client.market.create_subscription(["000001.SZ"])
orders = client.account.cached_orders()
```

`client.account.asset()`、`positions()`、`orders()`、`trades()` 会复用
`trader.query_stock_*` fixture 数据，用于离线覆盖 qmtserver trader readonly 行为。

`client.market.create_subscription()` 会维护 fake 订阅状态，用于离线覆盖 qmtserver
`market.subscription.v1` 行为。`events` fixture 可以放入 `market_quote` 事件，用于回放实时行情。

未配置的 RPC 会抛出 `QmtRpcError(code="METHOD_NOT_ALLOWED")`。

## Fixture

```python
client = FakeQmtClient.from_fixture("examples/fixtures/offline_strategy.json")
```

fixture 根对象支持：

- `health`
- `status`
- `rpc`
- `market`
- `orders`
- `trades`
- `events`

标准 market fixture 示例：

- `examples/fixtures/market_daily.json`
- `examples/fixtures/market_intraday.json`
- `examples/fixtures/market_empty.json`
- `examples/fixtures/market_error.json`

`market.daily_bars`、`market.intraday_bars` 和 `market.instruments` 会被 `FakeQmtClient` 映射到稳定 `client.market` facade，用于覆盖正常、空数据和 schema 错误场景。
`market.subscriptions` 会映射到实时行情订阅 facade。

只使用示例账号、示例 URL 和示例 token。

## EventReplay

```python
from qmtclient import EventReplay, load_jsonl

events = load_jsonl("examples/fixtures/events.jsonl")
for event in EventReplay(events, types=["market_quote"]):
    print(event)
```

`types` 会过滤业务事件；`heartbeat` 会保留。
