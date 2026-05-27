# qmtclient

[![PyPI](https://img.shields.io/pypi/v/qmtclient?style=flat-square)](https://pypi.org/project/qmtclient/)
[![Python](https://img.shields.io/pypi/pyversions/qmtclient?style=flat-square)](https://pypi.org/project/qmtclient/)
[![License](https://img.shields.io/pypi/l/qmtclient?style=flat-square)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/gly11/qmtclient/ci.yml?branch=main&style=flat-square&label=ci)](https://github.com/gly11/qmtclient/actions/workflows/ci.yml)
[![Ask Zread](https://img.shields.io/badge/Ask_Zread-_.svg?style=flat-square&color=00b0aa&labelColor=000000&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuOTYxNTYgMS42MDAxSDIuMjQxNTZDMS44ODgxIDEuNjAwMSAxLjYwMTU2IDEuODg2NjQgMS42MDE1NiAyLjI0MDFWNC45NjAxQzEuNjAxNTYgNS4zMTM1NiAxLjg4ODEgNS42MDAxIDIuMjQxNTYgNS42MDAxSDQuOTYxNTZDNS4zMTUwMiA1LjYwMDEgNS42MDE1NiA1LjMxMzU2IDUuNjAxNTYgNC45NjAxVjIuMjQwMUM1LjYwMTU2IDEuODg2NjQgNS4zMTUwMiAxLjYwMDEgNC45NjE1NiAxLjYwMDFaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00Ljk2MTU2IDEwLjM5OTlIMi4yNDE1NkMxLjg4ODEgMTAuMzk5OSAxLjYwMTU2IDEwLjY4NjQgMS42MDE1NiAxMS4wMzk5VjEzLjc1OTlDMS42MDE1NiAxNC4xMTM0IDEuODg4MSAxNC4zOTk5IDIuMjQxNTYgMTQuMzk5OUg0Ljk2MTU2QzUuMzE1MDIgMTQuMzk5OSA1LjYwMTU2IDE0LjExMzQgNS42MDE1NiAxMy43NTk5VjExLjAzOTlDNS42MDE1NiAxMC42ODY0IDUuMzE1MDIgMTAuMzk5OSA0Ljk2MTU2IDEwLjM5OTlaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik0xMy43NTg0IDEuNjAwMUgxMS4wMzg0QzEwLjY4NSAxLjYwMDEgMTAuMzk4NCAxLjg4NjY0IDEwLjM5ODQgMi4yNDAxVjQuOTYwMUMxMC4zOTg0IDUuMzEzNTYgMTAuNjg1IDUuNjAwMSAxMS4wMzg0IDUuNjAwMUgxMy43NTg0QzE0LjExMTkgNS42MDAxIDE0LjM5ODQgNS4zMTM1NiAxNC4zOTg0IDQuOTYwMVYyLjI0MDFDMTQuMzk4NCAxLjg4NjY0IDE0LjExMTkgMS42MDAxIDEzLjc1ODQgMS42MDAxWiIgZmlsbD0iI2ZmZiIvPgo8cGF0aCBkPSJNNCAxMkwxMiA0TDQgMTJaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00IDEyTDEyIDQiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K&logoColor=ffffff)](https://zread.ai/gly11/qmtclient)

远程 qmtserver 的轻量 Python 客户端 SDK。适用于没有 MiniQMT、没有 `xtquant` 的策略机、服务器或笔记本。

```text
qmtclient  -- HTTP RPC / WebSocket / token -->  qmtserver + MiniQMT + xtquant
```

## 安装

使用 PyPI 安装：

```powershell
uv pip install qmtclient
```

开发本仓库：

```powershell
git clone https://github.com/gly11/qmtclient.git
cd qmtclient
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
daily = client.market.daily_bars(["000001.SZ"], start_time="20260501")
quality = client.market.daily_quality(
    ["000001.SZ"],
    start_time="2026-01-01",
    end_time="2026-01-31",
)
asset = client.account.asset("example-account")
orders = client.account.cached_orders(limit=20)
```

`daily_bars`、`intraday_bars` 和 `instruments` 优先使用 qmtserver 稳定
`/v1/market` 与 `/v1/reference` endpoints。直接 RPC 仍可用于 escape hatch。
`account` 只读查询优先使用 qmtserver `0.4.0` 稳定 `/v1/trader/*` endpoints。

交易入口在 `client.trading`。它只组装参数并调用 qmtserver；是否允许真实交易由 qmtserver 的配置、保护和审计决定。

## 数据工具

```python
job = client.batch.create_job(
    "market.daily_bars",
    {"codes": ["000001.SZ"], "start": "2026-01-01", "end": "2026-01-31"},
)
manifest = client.batch.download_snapshot(job["job_id"])

created = client.snapshots.create(
    {
        "kind": "daily_bars",
        "symbols": ["000001.SZ"],
        "start": "2026-01-01",
        "end": "2026-01-31",
        "format": "csv",
    }
)
```

## CLI

```powershell
qmtclient check --base-url http://192.168.1.10:8000 --token-env QMTCLIENT_TOKEN
qmtclient diagnose --sample-code 000001.SZ --json
qmtclient snapshot-verify .\snapshot\manifest.json
```

CLI 只做诊断、只读冒烟检查和本地文件校验，不提供真实交易快捷入口。

## 事件

```python
for event in client.events(types=["stock_order", "stock_trade"]):
    print(event)
```

## 离线测试

```python
from qmtclient import FakeQmtClient

fake = FakeQmtClient.from_fixture("examples/fixtures/market_daily.json")
print(fake.market.daily_bars(["000001.SZ"]))
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
- [数据工具](docs/data-tools.md)
- [CLI](docs/cli.md)
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
