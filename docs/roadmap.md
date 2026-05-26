# qmtclient 路线图

qmtclient 是远程 qmtserver 的 Python 客户端 SDK。它运行在没有 MiniQMT、没有 `xtquant` 的机器上，通过 HTTP RPC 和 WebSocket 访问 qmtserver。

```text
qmtclient  -- HTTP RPC / WebSocket / token -->  qmtserver + MiniQMT + xtquant
```

## 边界

qmtclient 负责：

- 客户端 SDK。
- 策略友好接口。
- fake client、fixture、event replay。
- 客户端侧兼容性说明。

qmtserver 负责：

- 服务端 API、RPC、WebSocket。
- token、白名单、透明 RPC 开关。
- 交易保护、审计、运行和 MiniQMT 连接。

## 模块

```text
qmtclient/
|-- client.py       # QmtClient
|-- batch.py        # history download job client
|-- cache.py        # optional local memory cache
|-- conversions.py  # optional Pandas / Arrow conversion helpers
|-- errors.py       # 客户端异常
|-- events.py       # WebSocket 事件
|-- models.py       # typed response schema helpers
|-- proxy.py        # 动态 RPC proxy
|-- snapshots.py    # snapshot API client and manifest validation
|-- strategy.py     # market/account/trading facade
|-- fake.py         # FakeQmtClient
`-- fixtures.py     # fixture loading / EventReplay
```

## 当前状态

`0.3.0` 已具备：

- qmtserver `/v1` HTTP RPC 和 WebSocket 客户端。
- `market`、`account`、`trading` 策略接口。
- `FakeQmtClient`、fixture loading、`EventReplay`。
- 中文文档、示例、CI、typed package。
- `client.market` 优先调用稳定 `/v1/market` 和 `/v1/reference` endpoints。
- `client.batch` 适配 `/v1/jobs/history-download` 和 job result manifest。
- `client.snapshots` 封装 `/v1/snapshots` registry、manifest 和 quality。
- `load_snapshot_manifest()` 支持 qmtserver `0.3.0` CSV manifest。

## 当前能力

qmtclient 已从薄 RPC 封装扩展为稳定、可测、类型清晰的客户端 SDK，为下游策略开发、回测系统和数据管线提供通用支撑。

- 稳定 market facade：`daily_bars`、`intraday_bars`、`instruments`、`capabilities` 和 `daily_quality`，返回 JSON-friendly response。
- 类型和错误契约：提供 market、diagnose、snapshot schema helpers，并区分认证失败、服务不可用、空数据、schema mismatch、可选依赖缺失等错误。
- 离线测试：`FakeQmtClient` 支持标准 market fixture，示例覆盖 daily、intraday、empty、error 场景。
- 连接诊断：`diagnose()` 聚合 HTTP、ready、methods 和只读 sample，`check_compatibility()` 检查 client/server API version。
- 数据工具：`client.batch` 封装 history download job，`client.snapshots` 封装 snapshot registry，`load_snapshot_manifest()` 校验 manifest hash 和 row count。
- 体验增强：支持有限 retry/backoff、WebSocket reconnect、显式启用的 `MemoryCache`、Pandas/Arrow 延迟导入转换工具。

## 后续方向

- 跟随 qmtserver 批量/snapshot 契约演进，优先更新兼容性文档和契约测试，再调整客户端实现。
- 当 qmtserver 新增 `/v2` 或新 schema version 时，先补兼容性测试和迁移说明，再扩展 facade。
- 扩展真实 qmtserver 手动 smoke 指南，但不把真实环境接入默认单元测试门禁。
- 规划诊断优先 CLI，用于连接检查、兼容性检查、RPC methods 查看、WebSocket 冒烟检查、只读 market 冒烟检查、snapshot/fixture 校验；CLI 不提供真实交易快捷入口。
- 持续保持基础安装轻量；研究体验能力优先通过延迟导入或 optional extra 提供。

## 验证分层

qmtclient 的默认开发验收不要求连接真实 qmtserver、MiniQMT 或 `xtquant`。真实 qmtserver 验证作为可选 integration smoke，用于补充确认部署环境和协议兼容性，不进入默认单元测试和本地质量门禁。

默认验证分层：

- 单元测试：必须使用 `httpx.MockTransport`、fake WebSocket、`FakeQmtClient` 或 fixture，覆盖 SDK 逻辑、错误分类和数据解析。
- 契约测试：必须使用固定 fixture 或 mock response，验证 market response、diagnose response、manifest 和 schema version 的稳定结构。
- 真实 qmtserver 冒烟检查：可选手动执行，覆盖 `health`、`status`、`methods`、`diagnose()`、只读 market sample，以及批量/snapshot sample。
- 真实 MiniQMT 行为：由 qmtserver 负责验证；qmtclient 只验证客户端协议、参数组织、返回解析和错误处理。

真实 qmtserver 冒烟检查不得使用真实 token、真实账号或个人路径写入仓库，也不得绕过 qmtserver 的 token、RPC allowlist、透明 RPC 开关或交易保护。

发布或交付前至少运行：

```powershell
uv run python -m unittest discover -s tests
uv run ruff check .
uv run ruff format --check .
uv run ty check
git diff --check
```
