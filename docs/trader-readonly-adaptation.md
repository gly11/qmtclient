# qmtserver 0.4.0 只读交易查询适配

qmtserver `0.4.0` 提供稳定只读交易查询 endpoints。qmtclient `0.4.0`
已适配这些 endpoints，让 `client.account` 优先走稳定 API，而不是继续依赖
RPC escape hatch。

## 服务端契约

服务端 endpoints：

```text
GET /v1/trader/account-status
GET /v1/trader/asset
GET /v1/trader/positions
GET /v1/trader/orders
GET /v1/trader/trades
```

账号参数：

```text
account_id=<资金账号>
account_type=STOCK
cancelable_only=true
```

响应 envelope：

```python
{
    "ok": True,
    "data": {"asset": {...}},
    "error": None,
    "meta": {
        "schema": "trader.readonly.v1",
        "qmtserver_version": "0.4.0",
        "xtquant_version": None,
        "account_id": "123****789",
        "account_type": "STOCK",
    },
}
```

失败时 HTTP 仍可能是 200，但 `ok=False`，`error.code` 包含 `TRADER_ACCOUNT_REQUIRED`、`TARGET_NOT_CONNECTED` 或 `ACCOUNT_NOT_ALLOWED` 等服务端错误。

## qmtclient 行为

- `QmtClient` 提供稳定只读交易查询方法。
- `client.account` 优先调用 `/v1/trader/*` endpoints。
- 保留 `client.account.rpc()`、`client.trader.*` 和 `client.rpc()` 作为 escape hatch。
- 交易命令仍只在 `client.trading`，不新增真实交易快捷路径。
- 错误继续映射为 `QmtRpcError`，便于复用现有错误处理。

## API 设计

`QmtClient`：

```python
client.trader_account_status()
client.trader_asset(account_id=None, account_type=None)
client.trader_positions(account_id=None, account_type=None)
client.trader_orders(account_id=None, account_type=None, cancelable_only=False)
client.trader_trades(account_id=None, account_type=None)
```

`client.account`：

```python
client.account.status()
client.account.asset(account_id=None, account_type="STOCK")
client.account.positions(account_id=None, account_type="STOCK")
client.account.orders(account_id=None, account_type="STOCK", cancelable_only=False)
client.account.trades(account_id=None, account_type="STOCK")
```

兼容性说明：

- `account_id` 可选，用于支持 qmtserver 从服务端配置解析默认账号。
- 仍允许显式传 `account_id`，适合多账号或不想依赖服务端默认账号的场景。
- `client.account` 的 `account_type` 默认保持 `"STOCK"`；如需完全使用服务端默认值，可显式传 `None`。
- `client.account.infos()` 暂保留 RPC，因为 qmtserver `0.4.0` 只提供
  `account-status` 稳定 endpoint。

## 数据返回

客户端对稳定 endpoint 返回 JSON-friendly 基础类型：

- `trader_account_status()` -> `list[dict]`
- `trader_asset()` -> `dict`
- `trader_positions()` -> `list[dict]`
- `trader_orders()` -> `list[dict]`
- `trader_trades()` -> `list[dict]`

字段由 qmtserver `trader.readonly.v1` 负责规范化。qmtclient 不自行补字段、不连接 MiniQMT、不导入 `xtquant`。

## 测试覆盖

`tests/test_strategy.py` 覆盖：

- `client.trader_asset()` 调用 `/v1/trader/asset`，传递 `account_id` 和 `account_type`。
- `client.trader_positions()`、`trader_orders(cancelable_only=True)`、`trader_trades()` 解析 named list。
- `client.trader_account_status()` 解析 `statuses`。
- `client.account.asset()`、`positions()`、`orders()`、`trades()` 优先走稳定 endpoints。
- `ok=False` 响应抛出 `QmtRpcError`，保留 `code` 和 `message`。
- 现有 `client.account.rpc()` 和 `client.trader.query_stock_asset(...)` 不变。

默认测试继续使用 `httpx.MockTransport` 和 `FakeQmtClient`，不连接真实 qmtserver。

## 验证

```powershell
uv run python -m unittest discover -s tests
uv run ruff check .
uv run ruff format --check .
uv run ty check
git diff --check
```

## 发布说明

本适配属于 qmtclient `0.4.0` 内容，用于匹配 qmtserver `0.4.0`
的稳定只读交易查询契约。
