# 策略接口

`client.market`、`client.account`、`client.trading` 是 qmtserver RPC/API 的薄封装，减少手写 RPC payload。

## market

```python
ticks = client.market.get_full_tick(["000001.SZ", "600000.SH"])
```

其他已开放 `xtdata` 方法：

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
