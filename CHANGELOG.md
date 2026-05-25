# 更新日志

## 0.1.0 - 待发布

qmtclient 的第一个独立版本，目标是让没有 MiniQMT、没有 `xtquant` 的策略机、服务器或笔记本，通过远程 qmtserver 网关访问 MiniQMT 能力。

### 新增

- `QmtClient`：支持 qmtserver `/v1` HTTP RPC、状态查询、订单/成交缓存查询和 WebSocket 事件消费。
- 动态 RPC 代理：`client.xtdata.<method>(...)` 和 `client.trader.<method>(...)`。
- 类型化异常：连接错误、认证错误、HTTP 错误、协议错误和 RPC 错误。
- 策略友好 facade：`client.market`、`client.account`、`client.trading`。
- `FakeQmtClient`：用于不依赖真实 qmtserver 的策略单元测试。
- JSON/JSONL fixture loading 和 `EventReplay`。
- LAN、VPN、反向代理、策略 facade 和离线测试示例。
- 中文用户文档和英文 agent 协作规范。

### 安全边界

- qmtclient 不直接连接 MiniQMT。
- qmtclient 不依赖 `xtquant`。
- qmtclient 不绕过 qmtserver 的 token、RPC 白名单、透明 RPC 开关或交易保护。
- 真实交易能力仍由 qmtserver 显式配置、保护和审计。

### 验证

发布前需要通过：

```powershell
uv run python -m unittest discover -s tests
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv build
```
