# CLI

qmtclient CLI 用于诊断远程 qmtserver 连接和校验本地数据文件。它不替代 Python SDK，不提供真实交易快捷入口。

## 安装

安装包含 CLI 的 qmtclient 后会提供 `qmtclient` 命令：

```powershell
uv pip install qmtclient
qmtclient version
```

源码开发环境：

```powershell
uv sync
uv run qmtclient version
```

## 全局参数

```text
--base-url http://127.0.0.1:8000
--token <token>
--token-env QMTCLIENT_TOKEN
--timeout 10
--api-version v1
--json
```

token 读取顺序：

```text
--token
--token-env 指定的环境变量
QMTCLIENT_TOKEN
无 token
```

`--token` 只适合临时调试。脚本和文档示例应优先使用 `--token-env`。

## 常用命令

```powershell
qmtclient check --base-url http://192.168.1.10:8000 --token-env QMTCLIENT_TOKEN
qmtclient diagnose --sample-code 000001.SZ --json
qmtclient methods --json
qmtclient ws-check --wait-seconds 10
qmtclient market-capabilities
qmtclient market-subscribe-check --symbol 000001.SZ --wait-seconds 10
qmtclient snapshot-verify .\snapshot\manifest.json
qmtclient fixture-check .\examples\fixtures\market_daily.json
```

## 命令说明

### version

打印 qmtclient 版本和默认 API version。

### check

调用 `health()` 和 `check_compatibility()`，用于确认 qmtserver 可达且声明兼容的 API version。

### diagnose

调用 `diagnose()`，聚合 HTTP、ready、methods 和可选只读 sample 检查。

```powershell
qmtclient diagnose --sample-code 000001.SZ
```

### methods

调用 `/v1/rpc/methods`，输出 methods 数量和方法名。用于确认 RPC 白名单和透明 RPC 配置。

### ws-check

连接 `/v1/ws/events`，等待一条事件或 heartbeat。

```powershell
qmtclient ws-check --wait-seconds 10 --types stock_order,stock_trade
```

超时返回失败，不无限等待。

### market-capabilities

调用 `client.market.capabilities()`，确认 qmtserver 稳定 market endpoint 可用。

### market-subscribe-check

创建只读实时行情订阅，等待一条 `market_subscription` 或 `market_quote` 事件，然后尝试停止订阅。

```powershell
qmtclient market-subscribe-check --symbol 000001.SZ --wait-seconds 10
```

该命令只检查行情订阅链路，不提供下单、撤单或其他交易快捷入口。

### snapshot-verify

本地校验 snapshot manifest 的 hash 和 row count，不连接 qmtserver。

```powershell
qmtclient snapshot-verify .\snapshot\manifest.json
```

### fixture-check

本地检查 JSON 或 JSONL fixture 是否可读取。

JSON fixture 使用 `load_fixture()`；JSONL fixture 使用 `load_jsonl()`。

## 输出

默认输出面向人工阅读，不同命令字段不同：

```text
qmtclient: <version>
api_version: v1
method_count: 42
```

`--json` 输出 JSON-friendly dict，不打印 token。

## 退出码

```text
0  成功
1  检查完成但存在失败项
2  参数错误
3  认证失败
4  连接失败或 WebSocket 等待超时
5  协议或 schema 不匹配
```

异常映射：

- `QmtAuthError` -> 3
- `QmtConnectionError` -> 4
- `TimeoutError` -> 4
- `QmtProtocolError`、`QmtSchemaMismatchError` -> 5
- 其他 `QmtClientError` -> 1

## 边界

- 不直接连接 MiniQMT。
- 不依赖 `xtquant`。
- 不保存 token。
- 不提供下单、撤单等交易命令。
- 不绕过 qmtserver 的 token、RPC 白名单、透明 RPC 开关或交易保护。
- 不做 GUI 或 TUI。

## 里程碑步骤

CLI 按以下步骤实现：

- M1：CLI 骨架和本地命令：`version`、`snapshot-verify`、`fixture-check`。
- M2：连接诊断命令：`check`、`diagnose`、token 读取和 client 构造。
- M3：服务能力冒烟检查：`methods`、`market-capabilities`、`ws-check`。
- M3.5：实时行情订阅冒烟检查：`market-subscribe-check`。
- M4：README、兼容性文档、CLI 文档和质量门。

默认测试使用 mock、fake 或临时 fixture，不连接真实 qmtserver。真实 qmtserver 冒烟检查可手动执行。
