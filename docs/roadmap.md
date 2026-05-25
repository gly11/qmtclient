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
|-- errors.py       # 客户端异常
|-- events.py       # WebSocket 事件
|-- proxy.py        # 动态 RPC proxy
|-- strategy.py     # market/account/trading facade
|-- fake.py         # FakeQmtClient
`-- fixtures.py     # fixture loading / EventReplay
```

## 版本

当前版本：`0.1.0`。

`0.1.x` 继续以 qmtserver `/v1` 兼容为主。后续如果 qmtserver 引入新 API 版本，先补兼容性文档和测试，再扩展客户端接口。

## Milestones

### M1: Base SDK 稳定

状态：已完成。

- `QmtClient` 兼容 qmtserver `/v1`。
- HTTP RPC、状态查询、订单/成交缓存、WebSocket 事件可用。
- 连接、认证、HTTP、协议、RPC 错误有类型化异常。
- LAN、VPN、反向代理文档和示例已补。

### M2: Strategy Facade

状态：已完成。

- `client.market`
- `client.account`
- `client.trading`
- facade 只做薄封装，不绕过 qmtserver 保护。

### M3: Offline Strategy Testing

状态：已完成。

- `FakeQmtClient`
- JSON/JSONL fixture loading
- `EventReplay`
- 离线策略测试示例

### M4: 兼容性与发布准备

状态：已完成。

- qmtclient/qmtserver `/v1` 兼容性文档。
- `CHANGELOG.md`。
- `py.typed`。
- CI、build、twine check 配置。
- `0.1.0` release readiness 检查清单。

## 发布前验收

- 无 MiniQMT 机器可以使用 `QmtClient` 调用远程 qmtserver。
- 策略代码不导入 `xtquant`。
- 常见行情、账户、委托、事件 helper 有测试。
- 离线测试可用 fake client、fixtures、event replay。
- `uv run python -m unittest discover -s tests`、ruff、ty、build 通过。
