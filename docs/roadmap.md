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
|-- batch.py        # batch job client
|-- cache.py        # optional local memory cache
|-- conversions.py  # optional Pandas / Arrow conversion helpers
|-- errors.py       # 客户端异常
|-- events.py       # WebSocket 事件
|-- models.py       # typed response schema helpers
|-- proxy.py        # 动态 RPC proxy
|-- snapshots.py    # snapshot manifest loading / validation
|-- strategy.py     # market/account/trading facade
|-- fake.py         # FakeQmtClient
`-- fixtures.py     # fixture loading / EventReplay
```

## 当前状态

`0.1.0` 已具备：

- qmtserver `/v1` HTTP RPC 和 WebSocket 客户端。
- `market`、`account`、`trading` 策略接口。
- `FakeQmtClient`、fixture loading、`EventReplay`。
- 中文文档、示例、CI、typed package。

## Milestones 状态

qmtclient 已按 milestones 从薄 RPC 封装升级为稳定、可测、类型清晰的客户端 SDK，为下游策略开发、回测系统和数据管线提供通用支撑。

| Milestone | 主题 | 状态 | 关键交付 |
| --- | --- | --- | --- |
| M0 | 数据契约确认 | 已实现 | `qmtclient.market.v1`、`qmtclient.diagnose.v1`、错误映射、兼容性文档 |
| M1 | 稳定 market facade | 已实现 | `daily_bars`、`intraday_bars`、`instruments` |
| M2 | Typed responses 与错误模型 | 已实现 | `models.py`、稳定异常、schema mismatch/empty data 处理 |
| M3 | Fake fixture 标准化 | 已实现 | daily、intraday、empty、error fixture 示例和 FakeQmtClient 映射 |
| M4 | 连接诊断与兼容检查 | 已实现 | `diagnose()`、`check_compatibility()`、结构化诊断结果 |
| M5 | 批量数据与 snapshot 工具 | 已实现 | `client.batch`、`load_snapshot_manifest()`、hash/row count 校验 |
| M6 | 稳定性与体验增强 | 已实现 | retry/backoff、WebSocket reconnect、`MemoryCache`、Pandas/Arrow 显式转换 |

### M0：数据契约确认

目标：在动手扩展 SDK 前，先把 qmtclient 对外承诺的 market 数据、错误语义和诊断结果固定下来。

范围：

- 定义 daily bar、intraday bar、instrument 的字段集合、类型和 `schema_version`。
- 明确空数据、字段缺失、服务不可用、认证失败、RPC 拒绝、schema 不匹配分别映射到什么结果或异常。
- 明确 qmtclient 保持 JSON-friendly 返回的边界：基础模型只使用 `dict`、`list`、`str`、`int`、`float`、`bool`、`None` 可表达的数据。
- 在 `docs/compatibility.md` 记录 qmtclient 与 qmtserver `/v1` 的数据契约假设。

交付物：

- market response 字段说明。
- 错误类型映射说明。
- `schema_version` 命名与演进规则。

验收标准：

- 后续 milestone 可以直接依据 M0 的字段和错误语义写测试。
- 文档明确说明 qmtclient 不直连 MiniQMT、不依赖 `xtquant`，也不绕过 qmtserver 的安全与交易保护。

### M1：稳定 market facade

目标：让下游只读行情调用优先使用稳定 facade，减少手写 `rpc("xtdata", ...)`。

范围：

- 在 `client.market` 增加 `daily_bars`、`intraday_bars`、`instruments`。
- 保留 `client.market.rpc()` 作为 escape hatch，但文档中把稳定 facade 列为首选。
- 对 qmtserver 返回的原始数据做最小必要 normalization，输出 M0 定义的字段。
- 覆盖正常数据、空数据、字段缺失和 RPC 错误路径。

交付物：

- `src/qmtclient/strategy.py` 的 market facade 扩展。
- `tests/test_strategy.py` 的 market facade 测试。
- `docs/strategy.md` 的使用示例。

验收标准：

- daily、intraday、instrument 三类入口都有测试覆盖。
- 下游调用不需要知道 `xtdata` 原始方法名和参数形态。
- facade 不实现服务端保护逻辑，只表达客户端查询意图。

### M2：Typed responses 与错误模型

目标：让返回结构和错误类型可预测，降低下游重复解析和错误分支判断成本。

范围：

- 新增轻量 response models 或 schema helpers，优先使用标准库 typing 能力，避免引入重依赖。
- 为 market response 增加 `schema_version`、`data`、`meta` 的稳定结构。
- 补齐稳定异常类型，例如服务不可用、空数据、schema mismatch。
- 将 HTTP、RPC、协议和 schema 错误统一转换为 qmtclient 异常体系。

交付物：

- `src/qmtclient/models.py` 或等价轻量 schema 模块。
- `src/qmtclient/errors.py` 的错误类型扩展。
- `tests/test_client.py`、`tests/test_strategy.py` 的异常和 schema 测试。

验收标准：

- public API 返回值字段清晰、类型可检查、schema version 可见。
- 数据管线能区分重试类错误、配置类错误、权限类错误和空数据。
- 不新增 `xtquant` 依赖，不引入重量级 runtime dependency。

### M3：Fake fixture 标准化

目标：让下游可以在没有 Windows、MiniQMT、`xtquant` 或真实 qmtserver 的环境中稳定测试。

范围：

- 增加 daily、intraday、empty、error fixture 示例。
- 扩展 `FakeQmtClient` fixture loader，使其能覆盖 M1/M2 的稳定 facade 和 response shape。
- 增加 fixture schema 校验，尽早暴露示例数据结构错误。
- 更新离线测试文档，说明 fixture 组织方式和推荐测试模式。

交付物：

- `examples/fixtures/` 下的标准 fixture 文件。
- `src/qmtclient/fake.py`、`src/qmtclient/fixtures.py` 的必要扩展。
- `tests/test_fake.py` 的 fixture 覆盖。
- `docs/offline-testing.md` 的标准化说明。

验收标准：

- fake client 能覆盖 daily、intraday、empty、error 四类核心场景。
- fixture 中只使用明显假的 token、账号、URL 和数据。
- 未配置或 schema 错误的 fixture 能抛出明确异常。

### M4：连接诊断与兼容检查

目标：提供一个标准入口快速判断 qmtserver 是否可用、token 是否有效、服务是否 ready、方法和 schema 是否匹配。

范围：

- 增加 `client.diagnose()`，聚合 HTTP health、token、server ready、RPC methods 和 sample smoke。
- 增加 client/server API version 与 schema version 检查。
- 诊断结果必须结构化返回，不因单项失败中断整体诊断。
- 为连接诊断补充文档和示例输出。

交付物：

- `src/qmtclient/client.py` 的 `diagnose()`。
- 诊断结果 response model 或 schema helper。
- `tests/test_client.py` 的诊断路径测试。
- `docs/connection.md`、`docs/compatibility.md` 的诊断说明。

验收标准：

- 诊断结果能指出失败项、异常类型、request id 和建议检查方向。
- token 错误、服务不可达、server not ready、method 缺失、schema 不匹配都有测试。
- 诊断不执行真实交易，也不绕过 qmtserver 权限控制。

### M5：批量数据与 snapshot 工具

目标：增强批量数据消费能力，让回测和数据管线可以可靠读取 qmtserver 导出的数据。

范围：

- 增加批量下载客户端封装，覆盖 job 创建、状态轮询、失败读取和 snapshot 下载。
- 增加 snapshot manifest 读取工具，校验 hash、row count、schema version 和文件完整性。
- 批量任务和 snapshot 工具只处理客户端封装与校验，不定义 qmtserver 内部导出实现。
- 更新兼容性文档，明确该 milestone 依赖 qmtserver 提供稳定批量/snapshot 契约。

交付物：

- `src/qmtclient/batch.py` 或等价批量客户端模块。
- `src/qmtclient/snapshots.py` 或等价 manifest 工具模块。
- `tests/` 中的 batch、snapshot 测试。
- `docs/compatibility.md` 和相关示例文档。

验收标准：

- job 创建、轮询、成功、失败、超时和下载校验路径都有测试。
- manifest hash 或 row count 不匹配时抛出明确异常。
- 工具可以被下游回测系统直接调用，并保持 JSON-friendly 基础协议。

### M6：稳定性与体验增强

目标：在基础契约稳定后补充可靠性和研究体验能力，同时避免改变数据真相源。

范围：

- 增加 request-level timeout、有限 retry 和 backoff 配置；默认保守，不无限重试。
- 扩展 WebSocket 事件封装，支持事件过滤、断线重连、心跳状态和 fixture replay 对齐。
- 增加可选本地轻量缓存；默认关闭，明确数据来源、时间戳和失效策略。
- 增加 Pandas/Arrow 显式转换工具；通过 optional extra 或延迟导入实现，不增加基础安装负担。

交付物：

- retry/backoff 配置和测试。
- WebSocket 事件增强和回放测试。
- 可选缓存模块和文档。
- Pandas/Arrow 转换 helper 与 optional dependency 文档。

验收标准：

- retry/backoff 不掩盖认证、权限、schema mismatch 和服务端保护类错误。
- 缓存必须显式启用，且不会成为权威数据源。
- Pandas/Arrow 不影响基础安装和 JSON 协议。

## 后续维护顺序

M0-M6 已具备本地 mock/fake/fixture 验收覆盖。后续维护优先顺序：

- 当 qmtserver 批量/snapshot 契约变化时，先更新 `docs/compatibility.md` 和 batch/snapshot 契约测试，再调整客户端实现。
- 当 qmtserver 新增 `/v2` 或新 schema version 时，先补兼容性测试和文档，再扩展 facade。
- 当下游需要新的研究依赖时，优先使用延迟导入或 optional extra，不增加基础安装负担。

## 验证分层

qmtclient 的默认开发验收不要求连接真实 qmtserver、MiniQMT 或 `xtquant`。真实 qmtserver 验证作为可选 integration smoke，用于补充确认部署环境和协议兼容性，不进入默认单元测试和本地质量门禁。

默认验证分层：

- 单元测试：必须使用 `httpx.MockTransport`、fake WebSocket、`FakeQmtClient` 或 fixture，覆盖 SDK 逻辑、错误分类和数据解析。
- 契约测试：必须使用固定 fixture 或 mock response，验证 market response、diagnose response、manifest 和 schema version 的稳定结构。
- 真实 qmtserver smoke：可选手动执行，覆盖 `health`、`status`、`methods`、`diagnose()` 和一个只读 market sample；M5 可追加批量/snapshot sample。
- 真实 MiniQMT 行为：由 qmtserver 负责验证；qmtclient 只验证客户端协议、参数组织、返回解析和错误处理。

真实 qmtserver smoke 不得使用真实 token、真实账号或个人路径写入仓库，也不得绕过 qmtserver 的 token、RPC allowlist、透明 RPC 开关或交易保护。

每个 milestone 完成前至少运行：

```powershell
uv run python -m unittest discover -s tests
uv run ruff check .
uv run ruff format --check .
uv run ty check
git diff --check
```
