# qmtclient 路线图

qmtclient 是面向远程 qmtserver 网关的独立 Python 客户端 SDK。它的目标很窄：让没有 MiniQMT、没有 `xtquant` 的电脑，也可以通过 qmtserver 网关开发、测试和运行策略代码。

## 当前状态

qmtclient 已经从 `qmtserver.client` 拆分为独立包骨架。

当前基线：

- Python 包位于 `src/qmtclient`。
- `QmtClient` 支持 HTTP RPC 和状态类端点。
- 动态 RPC 代理：`client.xtdata` 和 `client.trader`。
- WebSocket 事件迭代器。
- 客户端侧类型化异常。
- RPC 和事件示例。
- LAN、VPN、反向代理远程连接示例。
- 策略友好 facade：`client.market`、`client.account`、`client.trading`。
- 单元测试使用 `httpx.MockTransport` 和 fake WebSocket，不需要真实 qmtserver。

## Python 支持

qmtclient 目标支持 Python `>=3.10`，不设置 `<3.14` 上限。它是纯远程 SDK，不继承 qmtserver 在 Windows、MiniQMT、`xtquant` 或 Python 3.13 上的运行约束。

## 目标

- 客户端电脑不需要 MiniQMT。
- qmtclient 不依赖 `xtquant`。
- 稳定通过 HTTP RPC 和 WebSocket 访问 qmtserver。
- 对连接、认证、HTTP 和 RPC 失败提供清晰异常。
- 为常见行情、账户、委托、成交和事件流程提供策略友好的辅助接口。
- 通过 fake client、JSON fixture 和 event replay 支持离线策略测试。

目标形态：

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

## 非目标

- 不做 GUI。
- 不直接连接 MiniQMT。
- 不直接依赖 `xtquant`。
- 不绕过 qmtserver 的认证、RPC 白名单、透明 RPC 开关或交易保护。
- 第一阶段不做多语言 SDK。

## 包边界

qmtclient 负责：

- 远程 SDK API。
- 客户端侧错误类型。
- WebSocket 消费辅助能力。
- 策略适配层和 fake client。
- fixture 加载和 event replay。
- 从客户端视角说明 qmtserver 兼容性。

qmtserver 负责：

- HTTP API 和 WebSocket 服务端实现。
- RPC 白名单和透明 RPC 行为。
- MiniQMT / `xtquant` 连接生命周期。
- 交易保护、审计日志、指标和运维文档。

## 计划模块

```text
qmtclient/
|-- client.py          # QmtClient: HTTP RPC、状态、缓存查询
|-- errors.py          # QmtClientError、QmtRpcError、QmtAuthError 等
|-- events.py          # WebSocket 事件订阅和过滤
|-- proxy.py           # client.xtdata / client.trader 动态代理
|-- strategy.py        # market/account/trading 策略友好 facade
|-- fake.py            # 单元测试 fake client
`-- fixtures.py        # JSON/JSONL fixture 加载和 event replay
```

## 开发路径

1. 保持 base `QmtClient` 小而稳定，并兼容 qmtserver `/v1`。
2. 增加 LAN、VPN 等远程连接示例。
3. 增加策略友好 facade：`market`、`account`、`trading`。
4. 增加 fake client 和 fixture loading。
5. 增加 event replay，用于订单/成交回调测试。
6. 文档说明 qmtclient 与 qmtserver 的版本兼容关系。

## 版本策略

当前开发版本使用 `0.1.0.dev0`。`0.1.0` 是 M1-M4 全部完成并通过 release readiness 检查后的第一个正式目标版本，不代表任一单独 milestone 完成。

版本推进规则：

- M1-M3 完成时只更新 milestone 状态和开发文档，不切正式版本。
- M4 完成时执行完整 release readiness 检查。
- 只有 M4 验收通过后，才把版本从 `0.1.0.dev0` 切到 `0.1.0`。
- 如果 M2/M3/M4 过程中需要发布测试包，可以使用 PEP 440 预发布或开发版本，例如 `0.1.0.dev1`、`0.1.0a1`。

## Milestones

### M1: Base SDK 稳定

状态：已完成。

目标：把 `QmtClient` 做成小而可靠的 qmtserver `/v1` 客户端。

范围：

- 稳定 `health`、`status`、`methods` 和 `rpc`。
- 保持 `orders`、`order`、`trades` 和 `recent_events` 兼容 qmtserver `/v1`。
- 保持通过 `client.events()` 消费 WebSocket 事件。
- 保留连接、认证、HTTP 和 RPC 失败的类型化异常。
- 在服务端返回时保留 `error.code`、`message` 和 `request_id`。
- 增加 LAN、VPN、反向代理场景的远程连接示例。
- 文档说明 `base_url`、`token` 和 `api_version` 行为。
- 对非 JSON 服务端响应提供客户端侧类型化错误。

验收：

- qmtclient 不依赖 MiniQMT 或 `xtquant`。
- HTTP 行为使用 `httpx.MockTransport` 覆盖测试。
- WebSocket 行为使用 fake WebSocket 覆盖测试。
- `uv run python -m unittest discover -s tests` 通过。
- `uv run ruff check .` 通过。
- `uv run ruff format --check .` 通过。
- `uv run ty check` 通过。

### M2: Strategy Facade

状态：已完成。

目标：提供更适合策略代码使用的 API，同时不扩大客户端安全边界。

范围：

- 增加 `client.market`，用于常见行情查询。
- 增加 `client.account`，用于资产、持仓、委托和成交查询。
- 增加 `client.trading`，用于下单和撤单入口。
- facade 方法保持为 qmtserver RPC/API 行为的薄封装。
- 返回值保持 JSON 友好，并适合策略测试。
- 文档明确交易保护仍然在服务端执行。
- 示例展示策略代码如何使用 facade，减少手写 RPC payload。

验收：

- 策略代码可完成常见行情、账户和交易流程，且不导入 `xtquant`。
- 底层 `client.rpc` 仍然可用。
- 交易相关 facade 不绕过 qmtserver 保护。
- 公共 facade 行为有测试覆盖。

### M3: Offline Strategy Testing

目标：让策略逻辑可以在没有 qmtserver、MiniQMT 或 `xtquant` 的环境中测试。

范围：

- 增加 `FakeQmtClient`。
- 增加 JSON 和 JSONL fixture loading。
- 支持 fixture 驱动的行情、账户、委托、成交和事件数据。
- 增加 event replay，用于订单/成交回调测试。
- fake client 的常用返回结构与真实 client 保持兼容。
- 增加离线策略测试示例。

验收：

- 策略单元测试不需要真实 qmtserver。
- fake client 和 fixture helper 返回 JSON 友好的类型。
- event replay 可以确定性复现订单/成交事件序列。
- fixture 不包含真实 token、真实账号或个人路径。

### M4: 兼容性与发布准备

目标：让 qmtclient 具备独立 pre-alpha/alpha 发布条件。

范围：

- 文档说明 qmtclient/qmtserver 版本兼容关系。
- 文档说明支持的 qmtserver API 版本，从 `/v1` 开始。
- 补齐 README、docs 和 examples 中已支持能力的说明。
- 增加 changelog 或 release notes。
- 检查包元数据、typed package 行为和构建产物。
- 定义从 pre-alpha 走向 alpha 的发布标准。

验收：

- 新用户可以只看 README 完成安装并连接远程 qmtserver。
- 策略开发者可以找到 facade、fake client、fixture 和 event replay 示例。
- 服务端兼容性和客户端边界清楚。
- 开发检查稳定通过。
- 干净的 build/release dry run 成功。

## 交易原则

qmtclient 不能降低交易安全性：

- 示例默认只读或 dry-run。
- 真实交易需要服务端显式配置和确认。
- 客户端异常保留服务端 `error.code` 和 request ID。
- qmtclient 不在源码中保存 token、真实账号或个人路径。

## 独立发布前验收标准

qmtclient 独立发布前应该满足：

1. 没有 MiniQMT 的电脑可以使用 `QmtClient` 调用远程 qmtserver。
2. 策略代码不需要导入 `xtquant`。
3. 常见行情、账户、委托和事件 helper 有测试覆盖。
4. 离线策略测试可以使用 fake client 和 fixtures。
5. WebSocket 事件消费可用于订单/成交回调。
6. qmtserver API 版本兼容性已文档化。
