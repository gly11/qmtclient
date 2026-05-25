# qmtclient

qmtclient 是面向远程 qmtserver 网关的轻量 Python 客户端 SDK。

它用于没有 MiniQMT、没有 `xtquant` 的策略机、服务器或笔记本。Windows 网关机器运行 qmtserver 并连接 MiniQMT；策略开发机器通过 qmtclient 使用 HTTP RPC 和 WebSocket 访问网关。

```text
strategy computer / server / laptop
  - qmtclient
  - no MiniQMT
  - no xtquant
        |
        | HTTP RPC / WebSocket / token
        |
MiniQMT gateway computer
  - qmtserver
  - MiniQMT
  - xtquant
```

## 当前状态

本包从 `qmtserver.client` 拆分而来，目前处于 pre-alpha 阶段。qmtclient 不直接连接 MiniQMT，也不依赖 `xtquant`。

## Python 支持

qmtclient 支持 Python `>=3.10`，不设置 `<3.14` 上限。qmtserver 可能受 Windows、MiniQMT 或 `xtquant` 约束，但 qmtclient 是纯远程 SDK。

## 开发安装

```powershell
uv sync
```

## 基础用法

```python
from qmtclient import QmtClient

client = QmtClient("http://192.168.1.10:8000", token="dev-token")
print(client.health())
print(client.status())
print(client.rpc("xtdata", "get_full_tick", [["000001.SZ"]]))
print(client.xtdata.get_full_tick(["000001.SZ"]))
```

`base_url` 写 qmtserver 服务根地址即可，默认会自动使用 `/v1` API 前缀。真实 token 不要写进源码，建议从环境变量读取。LAN、VPN 和反向代理配置见 [远程连接指南](docs/connection.md)。

## 事件消费

```python
for event in client.events(types=["stock_order", "stock_trade"]):
    print(event)
```

## 策略友好接口

```python
ticks = client.market.get_full_tick(["000001.SZ"])
asset = client.account.asset("example-account")
positions = client.account.positions("example-account")
orders = client.account.cached_orders(limit=20)
```

交易入口也在 `client.trading` 下，但它只负责组织参数并调用 qmtserver。真实交易是否允许执行，仍由 qmtserver 的服务端配置、交易保护、dry-run 和审计逻辑决定。

## 离线策略测试

```python
from qmtclient import FakeQmtClient

fake = FakeQmtClient.from_fixture("examples/fixtures/offline_strategy.json")
print(fake.market.get_full_tick(["000001.SZ"]))
print(fake.account.cached_orders())
```

`FakeQmtClient` 与 JSON/JSONL fixtures 可用于没有 qmtserver、MiniQMT 或 `xtquant` 的单元测试。事件回放见 [离线策略测试](docs/offline-testing.md)。

## 设计原则

- 客户端电脑不需要 MiniQMT。
- qmtclient 不依赖 `xtquant`。
- 不绕过 qmtserver 的认证、RPC 白名单、透明 RPC 开关或交易保护。
- 真实交易必须保持显式，并由服务端保护。
- SDK 保持轻量，适合策略脚本和测试使用。

## 文档

- [远程连接指南](docs/connection.md)
- [策略友好接口](docs/strategy.md)
- [离线策略测试](docs/offline-testing.md)
- [兼容性说明](docs/compatibility.md)
- [发布准备](docs/release.md)
- [路线图](docs/roadmap.md)
- [更新日志](CHANGELOG.md)

## 开发检查

```powershell
uv run python -m unittest discover -s tests
uv run ruff check .
uv run ruff format --check .
uv run ty check
```
