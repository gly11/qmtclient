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

## 事件消费

```python
for event in client.events(types=["stock_order", "stock_trade"]):
    print(event)
```

## 设计原则

- 客户端电脑不需要 MiniQMT。
- qmtclient 不依赖 `xtquant`。
- 不绕过 qmtserver 的认证、RPC 白名单、透明 RPC 开关或交易保护。
- 真实交易必须保持显式，并由服务端保护。
- SDK 保持轻量，适合策略脚本和测试使用。

## 文档

- [路线图](docs/roadmap.md)

## 开发检查

```powershell
uv run python -m unittest discover -s tests
uv run ruff check .
uv run ruff format --check .
uv run ty check
```
