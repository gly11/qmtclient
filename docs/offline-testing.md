# 离线策略测试

qmtclient 提供 `FakeQmtClient`、fixture loading 和 `EventReplay`，用于在没有 qmtserver、MiniQMT 或 `xtquant` 的环境中测试策略逻辑。

## FakeQmtClient

`FakeQmtClient` 暴露与真实 `QmtClient` 相同的常用入口：

- `health()`
- `status()`
- `methods()`
- `rpc(...)`
- `orders(...)`
- `order(...)`
- `trades(...)`
- `recent_events(...)`
- `events(...)`
- `xtdata` / `trader` 动态代理
- `market` / `account` / `trading` facade

示例：

```python
from qmtclient import FakeQmtClient

client = FakeQmtClient(
    rpc_results={
        "xtdata.get_full_tick": {"000001.SZ": {"last": 10.5}},
        "trader.query_stock_asset": {"account_id": "example-account", "cash": 1000},
    },
    orders=[{"order_id": "order-1", "stock_code": "000001.SZ"}],
)

ticks = client.market.get_full_tick(["000001.SZ"])
asset = client.account.asset("example-account")
orders = client.account.cached_orders()
```

未配置的 RPC 会抛出 `QmtRpcError(code="METHOD_NOT_ALLOWED")`，这能帮助测试代码尽早发现 fixture 缺口。

## JSON fixture

JSON fixture 的根对象可以包含：

```json
{
  "health": {"ok": true, "api_versions": ["v1"]},
  "status": {"ok": true, "service": "fake"},
  "rpc": {
    "xtdata.get_full_tick": {"000001.SZ": {"last": 10.5}},
    "trader.query_stock_asset": {"account_id": "example-account", "cash": 1000}
  },
  "orders": [{"order_id": "order-1"}],
  "trades": [{"trade_id": "trade-1"}],
  "events": [{"type": "stock_order", "data": {"order_id": "order-1"}}]
}
```

加载 fixture：

```python
from qmtclient import FakeQmtClient

client = FakeQmtClient.from_fixture("examples/fixtures/offline_strategy.json")
```

fixture 应使用示例账号、示例 URL 和示例 token；不要写入真实 token、真实账号或个人路径。

## JSONL 事件

`load_jsonl(...)` 可以读取每行一个 JSON 对象的事件文件：

```python
from qmtclient import EventReplay, load_jsonl

events = load_jsonl("examples/fixtures/events.jsonl")
for event in EventReplay(events, types=["stock_trade"]):
    print(event)
```

`EventReplay` 会按顺序回放事件。指定 `types` 时，非匹配事件会被过滤，但 `heartbeat` 会保留，方便策略测试同时验证连接心跳和业务事件。

## 与真实 client 的关系

Fake client 的目标是让策略单测覆盖常见行为，而不是模拟 qmtserver 的全部服务端逻辑。真实鉴权、RPC 白名单、交易保护、dry-run 和审计仍由 qmtserver 负责；离线测试只验证客户端策略逻辑是否正确消费数据和事件。
