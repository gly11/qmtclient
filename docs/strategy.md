# 策略接口

`client.market`、`client.account`、`client.trading` 是 qmtserver RPC/API 的客户端封装，
减少手写 RPC payload。只读行情优先使用 qmtserver `0.3.0` 的稳定
market/reference endpoints；只读账户查询优先使用 qmtserver `0.4.0` 的稳定
trader readonly endpoints。直接 RPC 仍保留为 escape hatch。

## market

```python
ticks = client.market.get_full_tick(["000001.SZ", "600000.SH"])
capabilities = client.market.capabilities()
daily = client.market.daily_bars(["000001.SZ"], start_time="20260501")
bars_1m = client.market.intraday_bars(["000001.SZ"], period="1m")
instruments = client.market.instruments(["000001.SZ"])
quality = client.market.daily_quality(["000001.SZ"], start_time="2026-01-01", end_time="2026-01-31")
```

`daily_bars`、`intraday_bars` 和 `instruments` 返回 JSON-friendly typed response：

```python
{
    "schema_version": "qmtclient.market.v1",
    "data": [
        {
            "code": "000001.SZ",
            "date": "2026-05-25",
            "open": 10.0,
            "high": 10.8,
            "low": 9.8,
            "close": 10.5,
            "volume": 1000000.0,
            "amount": 10500000.0,
        }
    ],
    "meta": {"kind": "daily_bars", "codes": ["000001.SZ"], "period": "1d"},
}
```

空数据会抛出 `QmtDataEmptyError`，字段缺失或类型不匹配会抛出 `QmtSchemaMismatchError`。

默认情况下：

- `daily_bars()` 调用 `/v1/market/bars/daily`。
- `intraday_bars()` 调用 `/v1/market/bars/intraday`。
- `instruments()` 调用 `/v1/reference/instruments`。
- `daily_quality()` 调用 `/v1/market/bars/daily/quality`。

如果 `daily_bars()` 或 `intraday_bars()` 显式传入 `count`，qmtclient 会保留旧 RPC fallback，用于兼容需要 `xtdata.get_market_data` count 语义的调用。

其他 `xtdata` 方法可继续通过 RPC 调用：

```python
data = client.market.rpc("get_market_data", args=[...], kwargs={...})
```

### 实时行情订阅规划

qmtserver `0.5.0` 准备提供 `/v1/market/subscriptions`。qmtclient 计划在下一阶段封装：

```python
subscription = client.market.create_subscription(["000001.SZ"], period="tick")
for event in client.events(types=["market_quote"]):
    print(event)
client.market.stop_subscription(subscription["subscription_id"])
```

这是只读行情能力，不提供交易快捷入口。

## account

```python
status = client.account.status()
asset = client.account.asset("example-account")
positions = client.account.positions("example-account")
orders = client.account.orders("example-account", cancelable_only=True)
trades = client.account.trades("example-account")
```

这些方法调用 `/v1/trader/*`：

- `status()` -> `/v1/trader/account-status`
- `asset()` -> `/v1/trader/asset`
- `positions()` -> `/v1/trader/positions`
- `orders()` -> `/v1/trader/orders`
- `trades()` -> `/v1/trader/trades`

`account_id` 可省略，由 qmtserver 使用服务端配置解析默认账号；显式传入账号适合
多账号场景。`account_type` 默认保持 `"STOCK"`，也可以传 `None` 让 qmtserver 使用
服务端默认配置。

订单/成交缓存：

```python
cached_orders = client.account.cached_orders(limit=20)
cached_trades = client.account.cached_trades(limit=20)
```

## trading

```python
result = client.trading.order_stock(
    "example-account",
    "000001.SZ",
    order_type=23,
    volume=100,
    price_type=5,
    price=10.5,
)

cancel_result = client.trading.cancel_order_stock("example-account", "example-order-id")
```

qmtclient 只发起调用。真实交易、dry-run、限额、白名单和审计都由 qmtserver 决定。

## 仍可直接 RPC

```python
client.rpc("xtdata", "get_full_tick", [["000001.SZ"]])
client.xtdata.get_full_tick(["000001.SZ"])
client.trader.query_stock_asset(
    {"__type__": "StockAccount", "account_id": "example-account", "account_type": "STOCK"}
)
```
