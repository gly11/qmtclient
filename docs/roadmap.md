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

## 当前状态

`0.1.0` 已具备：

- qmtserver `/v1` HTTP RPC 和 WebSocket 客户端。
- `market`、`account`、`trading` 策略接口。
- `FakeQmtClient`、fixture loading、`EventReplay`。
- 中文文档、示例、CI、typed package。

## 后续方向

- 跟随 qmtserver `/v1` 补充常用只读 helper。
- 根据真实策略使用反馈微调 facade 命名和返回结构。
- 扩展 fixture/event replay 示例。
- 当 qmtserver 引入新 API 版本时，先补兼容性测试和文档。

## 发布检查

```powershell
uv run python -m unittest discover -s tests
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv build
uv tool run twine check dist/*
```
