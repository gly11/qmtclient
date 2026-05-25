# 策略友好接口

qmtclient 提供 `client.market`、`client.account` 和 `client.trading` 三组 facade，方便策略代码少写 RPC payload。它们都是 qmtserver RPC/API 的薄封装，不直接连接 MiniQMT，不导入 `xtquant`，也不绕过 qmtserver 的 token、RPC 白名单、透明 RPC 开关或交易保护。

## market

`client.market` 面向行情查询。当前提供常用 `get_full_tick`：

```python
from qmtclient import QmtClient

client = QmtClient("http://192.168.1.10:8000", token="example-token")

ticks = client.market.get_full_tick(["000001.SZ", "600000.SH"])
print(ticks)
```

如果需要调用 qmtserver 已允许的其他 `xtdata` RPC 方法，可以使用：

```python
data = client.market.rpc("get_market_data", args=[...], kwargs={...})
```

是否允许调用由 qmtserver 的 RPC 白名单和透明 RPC 配置决定。

## account

`client.account` 面向账户和交易回报查询：

```python
asset = client.account.asset("example-account")
positions = client.account.positions("example-account")
orders = client.account.orders("example-account")
trades = client.account.trades("example-account")
```

这些方法会把账号组装成 qmtserver 可识别的 JSON-friendly `StockAccount` payload：

```python
{
    "__type__": "StockAccount",
    "account_id": "example-account",
    "account_type": "STOCK",
}
```

也可以查询 qmtserver 的订单/成交缓存：

```python
cached_orders = client.account.cached_orders(limit=20)
cached_trades = client.account.cached_trades(limit=20)
```

## trading

`client.trading` 面向下单和撤单入口：

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

交易 facade 只负责组织客户端参数并调用 qmtserver。真实交易是否允许执行，仍由 qmtserver 的服务端配置、交易保护、白名单、dry-run 和审计逻辑决定。服务端拒绝时，qmtclient 会保留 `QmtRpcError.code`、`message` 和 `request_id`。

## 底层 RPC 仍然可用

facade 不替代底层 RPC。策略需要调用更底层能力时，仍然可以使用：

```python
client.rpc("xtdata", "get_full_tick", [["000001.SZ"]])
client.xtdata.get_full_tick(["000001.SZ"])
client.trader.query_stock_asset(
    {"__type__": "StockAccount", "account_id": "example-account", "account_type": "STOCK"}
)
```
