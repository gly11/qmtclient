# CLI 设计计划

qmtclient CLI 的目标是帮助用户快速诊断远程 qmtserver 连接和只读数据能力。CLI 不替代 Python SDK，不提供真实交易快捷入口。

## 目标

- 检查 qmtserver 是否可达。
- 检查 token、API version、RPC methods 和 WebSocket 是否可用。
- 检查稳定 market endpoint 是否可用。
- 校验本地 snapshot manifest 和 fixture。
- 输出适合人工阅读和脚本处理的结果。

## 边界

- 不直接连接 MiniQMT。
- 不依赖 `xtquant`。
- 不保存 token。
- 不提供下单、撤单等交易命令。
- 不绕过 qmtserver 的 token、RPC 白名单、透明 RPC 开关或交易保护。
- 不做 GUI 或 TUI。

## 入口

使用标准库 `argparse`，不新增运行时依赖。

```toml
[project.scripts]
qmtclient = "qmtclient.cli:main"
```

代码建议放在：

```text
src/qmtclient/cli.py
tests/test_cli.py
docs/cli.md
```

`cli.py` 只负责参数解析、输出格式和退出码。实际请求继续复用 `QmtClient`、`load_snapshot_manifest()`、`load_fixture()` 和 `load_jsonl()`。

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

`--token` 只用于临时调试。文档示例优先使用 `--token-env`。

## 命令

```text
qmtclient version
qmtclient check
qmtclient diagnose
qmtclient methods
qmtclient ws-check
qmtclient market-capabilities
qmtclient snapshot-verify <manifest>
qmtclient fixture-check <path>
```

### version

本地命令，打印 qmtclient 版本和默认 API version。

### check

轻量连接检查，调用：

- `client.health()`
- `client.check_compatibility()`

默认输出摘要。`--json` 输出完整结果。

### diagnose

调用 `client.diagnose()`。支持：

```text
--sample-code 000001.SZ
```

未传 `--sample-code` 时只做 HTTP、ready 和 methods 检查。传入 sample code 时追加只读行情 sample。

### methods

调用 `/v1/rpc/methods`，输出 methods 数量和方法名。用于确认 RPC 白名单和透明 RPC 配置。

### ws-check

连接 `/v1/ws/events`，等待一条事件或 heartbeat。支持：

```text
--wait-seconds 10
--types stock_order,stock_trade
```

超时返回失败，不无限等待。

### market-capabilities

调用 `client.market.capabilities()`，确认 qmtserver 稳定 market endpoint 可用。

### snapshot-verify

本地命令，调用 `load_snapshot_manifest()` 校验 manifest hash 和 row count。

```powershell
qmtclient snapshot-verify .\snapshot\manifest.json
```

### fixture-check

本地命令，检查 JSON 或 JSONL fixture 是否可读取。JSON fixture 使用 `load_fixture()`，JSONL fixture 使用 `load_jsonl()`。

输出摘要包含：

- fixture 类型。
- event 数量。
- market 数据类型。
- orders/trades 数量。

## 输出

默认输出面向人工阅读，保持短句和固定字段名。

```text
qmtserver: ok
api_version: v1 ok
auth: ok
methods: 42
```

`--json` 输出 JSON-friendly dict，不打印 token。

## 退出码

```text
0  成功
1  检查完成但存在失败项
2  参数错误
3  认证失败
4  连接失败
5  协议或 schema 不匹配
```

异常映射：

- `QmtAuthError` -> 3
- `QmtConnectionError` -> 4
- `QmtProtocolError`、`QmtSchemaMismatchError` -> 5
- 其他 `QmtClientError` -> 1

## 测试策略

- 单元测试使用 `httpx.MockTransport` 和 fake WebSocket。
- `snapshot-verify` 使用临时目录和测试 manifest。
- `fixture-check` 使用临时 JSON/JSONL fixture。
- 测试覆盖人工可读输出、`--json` 输出和退出码。
- 默认测试不连接真实 qmtserver。

## 里程碑步骤

### M1：CLI 骨架和本地命令

- 增加 `qmtclient.cli:main` 和 `[project.scripts]`。
- 实现 `version`。
- 实现 `snapshot-verify`。
- 实现 `fixture-check`。
- 覆盖参数解析、JSON 输出和退出码测试。

### M2：连接诊断命令

- 实现 `check`。
- 实现 `diagnose`。
- 统一 token 读取和 client 构造。
- 覆盖认证失败、连接失败、server 不兼容和成功路径。

### M3：服务能力冒烟检查

- 实现 `methods`。
- 实现 `market-capabilities`。
- 实现 `ws-check`。
- 覆盖 RPC methods、market capabilities、WebSocket heartbeat 和超时路径。

### M4：文档和发布准备

- README 增加最短 CLI 示例。
- `docs/cli.md` 更新为用户文档。
- `docs/compatibility.md` 补充 CLI 覆盖范围。
- 运行完整质量门并准备下一个版本发布。

## 验收

发布或交付前至少运行：

```powershell
uv run python -m unittest discover -s tests
uv run ruff check .
uv run ruff format --check .
uv run ty check
git diff --check
```

真实 qmtserver 冒烟检查可手动执行，但不得进入默认单元测试门禁。
