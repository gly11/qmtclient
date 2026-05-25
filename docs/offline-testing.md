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
orders = client.account.cached_orders()
```

未配置的 RPC 会抛出 `QmtRpcError(code="METHOD_NOT_ALLOWED")`。

## Fixture

```python
client = FakeQmtClient.from_fixture("examples/fixtures/offline_strategy.json")
```

fixture 根对象支持：

- `health`
- `status`
- `rpc`
- `orders`
- `trades`
- `events`

只使用示例账号、示例 URL 和示例 token。

## EventReplay

```python
from qmtclient import EventReplay, load_jsonl

events = load_jsonl("examples/fixtures/events.jsonl")
for event in EventReplay(events, types=["stock_trade"]):
    print(event)
```

`types` 会过滤业务事件；`heartbeat` 会保留。
