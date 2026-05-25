# qmtclient

远程 qmtserver 的轻量 Python 客户端 SDK。适用于没有 MiniQMT、没有 `xtquant` 的策略机、服务器或笔记本。

```text
qmtclient  -- HTTP RPC / WebSocket / token -->  qmtserver + MiniQMT + xtquant
```

## 安装

```powershell
uv sync
```

## 基础用法

```python
from qmtclient import QmtClient

client = QmtClient("http://192.168.1.10:8000", token="dev-token")
print(client.health())
print(client.status())
print(client.xtdata.get_full_tick(["000001.SZ"]))
```

默认使用 qmtserver `/v1`。真实 token 不要写进源码，建议从环境变量读取。

## 策略接口

```python
ticks = client.market.get_full_tick(["000001.SZ"])
asset = client.account.asset("example-account")
orders = client.account.cached_orders(limit=20)
```

交易入口在 `client.trading`。它只组装参数并调用 qmtserver；是否允许真实交易由 qmtserver 的配置、保护和审计决定。

## 事件

```python
for event in client.events(types=["stock_order", "stock_trade"]):
    print(event)
```

## 离线测试

```python
from qmtclient import FakeQmtClient

fake = FakeQmtClient.from_fixture("examples/fixtures/offline_strategy.json")
print(fake.market.get_full_tick(["000001.SZ"]))
```

## 边界

- 不直接连接 MiniQMT。
- 不依赖 `xtquant`。
- 不绕过 qmtserver 的 token、RPC 白名单、透明 RPC 开关或交易保护。
- 不做 GUI。

## 文档

- [远程连接](docs/connection.md)
- [策略接口](docs/strategy.md)
- [离线测试](docs/offline-testing.md)
- [兼容性](docs/compatibility.md)
- [发布检查](docs/release.md)
- [路线图](docs/roadmap.md)
- [更新日志](CHANGELOG.md)
- [贡献指南](CONTRIBUTING.md)

## 开发检查

```powershell
uv run python -m unittest discover -s tests
uv run ruff check .
uv run ruff format --check .
uv run ty check
```
