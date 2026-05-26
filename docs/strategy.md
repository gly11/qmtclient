# 策略接口

`client.market`、`client.account`、`client.trading` 是 qmtserver RPC/API 的客户端封装，减少手写 RPC payload。只读行情优先使用稳定 `market` facade；直接 RPC 仍保留为 escape hatch。

## market

```python
ticks = client.market.get_full_tick(["000001.SZ", "600000.SH"])
daily = client.market.daily_bars(["000001.SZ"], start_time="20260501")
bars_1m = client.market.intraday_bars(["000001.SZ"], period="1m")
instruments = client.market.instruments(["000001.SZ"])
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

其他 `xtdata` 方法可继续通过 RPC 调用：

```python
data = client.market.rpc("get_market_data", args=[...], kwargs={...})
```

## account

```python
asset = client.account.asset("example-account")
positions = client.account.positions("example-account")
orders = client.account.orders("example-account")
trades = client.account.trades("example-account")
```

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
