# qmtserver 0.4 只读交易查询适配计划

qmtserver `0.4.0` prerelease 新增稳定只读交易查询 endpoint。qmtclient 应在发布 `0.4.0` 前适配这些 endpoint，让 `client.account` 优先走稳定 API，而不是继续依赖 RPC escape hatch。

## 服务端契约

新增 endpoint：

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

## qmtclient 目标

- `QmtClient` 增加稳定只读交易查询方法。
- `client.account` 优先调用 `/v1/trader/*` endpoint。
- 保留 `client.account.rpc()`、`client.trader.*` 和 `client.rpc()` 作为 escape hatch。
- 交易命令仍只在 `client.trading`，不新增真实交易快捷路径。
- 错误继续映射为 `QmtRpcError`，便于复用现有错误处理。

## API 设计

`QmtClient` 增加：

```python
client.trader_account_status()
client.trader_asset(account_id=None, account_type=None)
client.trader_positions(account_id=None, account_type=None)
client.trader_orders(account_id=None, account_type=None, cancelable_only=False)
client.trader_trades(account_id=None, account_type=None)
```

`client.account` 调整为：

```python
client.account.status()
client.account.asset(account_id=None, account_type=None)
client.account.positions(account_id=None, account_type=None)
client.account.orders(account_id=None, account_type=None, cancelable_only=False)
client.account.trades(account_id=None, account_type=None)
```

兼容性说明：

- `account_id` 从必填改为可选，用于支持 qmtserver 从 `QMT_ACCOUNT_ID` 解析默认账号。
- 仍允许显式传 `account_id`，适合多账号或不想依赖服务端默认账号的场景。
- `client.account.infos()` 暂保留 RPC，因为 qmtserver 0.4 只提供 `account-status` 稳定 endpoint。

## 数据返回

客户端对稳定 endpoint 返回 JSON-friendly 基础类型：

- `trader_account_status()` -> `list[dict]`
- `trader_asset()` -> `dict`
- `trader_positions()` -> `list[dict]`
- `trader_orders()` -> `list[dict]`
- `trader_trades()` -> `list[dict]`

字段由 qmtserver `trader.readonly.v1` 负责规范化。qmtclient 不自行补字段、不连接 MiniQMT、不导入 `xtquant`。

## 测试计划

新增或更新 `tests/test_strategy.py`：

- `client.trader_asset()` 调用 `/v1/trader/asset`，传递 `account_id` 和 `account_type`。
- `client.trader_positions()`、`trader_orders(cancelable_only=True)`、`trader_trades()` 解析 named list。
- `client.trader_account_status()` 解析 `statuses`。
- `client.account.asset()`、`positions()`、`orders()`、`trades()` 优先走稳定 endpoint。
- `ok=False` 响应抛出 `QmtRpcError`，保留 `code` 和 `message`。
- 现有 `client.account.rpc()` 和 `client.trader.query_stock_asset(...)` 不变。

默认测试继续使用 `httpx.MockTransport`，不连接真实 qmtserver。

## 文档计划

- `docs/compatibility.md` 增加 `/v1/trader/*` 支持范围。
- `docs/strategy.md` 说明 account facade 优先走 qmtserver `0.4.0` 稳定只读交易查询 endpoint。
- `CHANGELOG.md` 在 `0.4.0` 中加入 qmtserver `0.4.0` trader readonly 适配。
- `README.md` 可保留现有 account 示例，只补一句“account 查询优先走稳定只读 endpoint”。

## 实施步骤

1. 先写失败测试，覆盖 `QmtClient.trader_*` helper 和 `client.account` facade。
2. 在 `client.py` 增加 named item/list 解析 helper 和 `trader_*` 方法。
3. 调整 `strategy.py` 的 `AccountFacade`，让只读查询调用稳定 endpoint。
4. 更新 fake client 或 fixture 文档，仅在现有 fake 行为不匹配测试时调整。
5. 更新文档和 changelog。
6. 运行完整质量门：

```powershell
uv run python -m unittest discover -s tests
uv run ruff check .
uv run ruff format --check .
uv run ty check
git diff --check
```

## 发布建议

建议在 qmtclient `0.4.0` tag 前完成本适配。这样 qmtclient `0.4.0` 与 qmtserver `0.4.0` 的稳定只读交易查询契约保持一致。
